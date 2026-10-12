#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""晨报卡 · 看门狗：白屏时自动把卡片重启回来。

它治的是什么
------------
宿主（makepad + D3D11）偶发会掉进一种状态：**逻辑全活着、一帧都画不出来**。
表现是窗口整片纯白 —— 连引擎自己画的标题栏都没了；而控件树依然完整、点击也
照样改状态。所以从卡片脚本内部根本察觉不到，只有重启卡片能恢复。

2026-10-12 的实测口径（本机 824x1504 窗口、采样约 1.1 万个点）：
    正常页面   色数 2700~8600，非白点 13000~96000
    白屏       色数 27，非白点 32
差距三个数量级，判定很稳。

触发条件目前是**偶发**的：400 次滚轮、200 次边缘拖拽、主编台开关、连拖桌宠
都没能稳定复现；只在一次"完整出报 + 核验台 + 密集合成拖拽"的混合长序列里
出现过一次。所以这里不做"根治"，只做**兜底恢复**。

判定（很保守）
------------
连续 3 次采样（间隔 --interval 秒）都同时满足：
    ① 窗口整片纯白
    ② /snap 里还有 >= --min-widgets 个控件   ← 说明是"有内容但没画出来"
才动手。然后 POST /quit，等端口释放，再用同一个启动器把卡片拉起来。

用法
----
    python tools/card_watchdog.py --port 8160
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
import urllib.request
from ctypes import wintypes as wt
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LAUNCH = REPO / "tools" / "launch.py"
try:
    ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)   # 否则坐标被 DPI 缩放
except Exception:
    pass
u32 = ctypes.WinDLL("user32", use_last_error=True)
g32 = ctypes.WinDLL("gdi32", use_last_error=True)
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class _BIH(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", wt.LONG),
                ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def log(msg):
    print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


def card_hwnd(title_hint="Card host"):
    found = []

    def cb(hwnd, _lp):
        cls = ctypes.create_unicode_buffer(64)
        u32.GetClassNameW(hwnd, cls, 64)
        if cls.value != "MakepadWindow":
            return True
        n = u32.GetWindowTextLengthW(hwnd)
        b = ctypes.create_unicode_buffer(n + 2)
        u32.GetWindowTextW(hwnd, b, n + 2)
        if title_hint in b.value:
            found.append(hwnd)
        return True

    u32.EnumWindows(ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)(cb), 0)
    return found[0] if found else None


GA_ROOT = 2


def covered_at(cx, cy):
    """卡片那个点是不是被别的窗口盖着。

    为什么必须查：下面用桌面 BitBlt 取样，取到的是**屏幕上真实显示**的像素 ——
    如果用户拿一个白底窗口盖住了卡片，取到的就是那层白，会被误判成白屏。
    所以每次取样前先问一句：这个点最上面那个窗口，根窗口是不是卡片自己。
    （卡片最小化时最上面是 Progman，同样会被挡掉，不会误判。）
    """
    class POINT(ctypes.Structure):
        _fields_ = [("x", wt.LONG), ("y", wt.LONG)]

    h = u32.WindowFromPoint(POINT(int(cx), int(cy)))
    if not h:
        return True
    return u32.GetAncestor(h, GA_ROOT) != card_hwnd()


def pixel_stats():
    """(色数, 非白采样点, 窗口尺寸)。拿不到返回 (-1, -1, '')。"""
    h = card_hwnd()
    if not h:
        return -1, -1, ""
    r = wt.RECT()
    u32.GetWindowRect(h, ctypes.byref(r))
    w, hh = r.right - r.left, r.bottom - r.top
    if w < 50 or hh < 50:
        return -1, -1, f"{w}x{hh}"
    if covered_at(r.left + w // 2, r.top + hh // 2):
        return -1, -1, "被遮挡"
    hdc = u32.GetDC(0)
    if not hdc:
        return -1, -1, ""
    mem = g32.CreateCompatibleDC(hdc)
    bmp = g32.CreateCompatibleBitmap(hdc, w, hh)
    g32.SelectObject(mem, bmp)
    g32.BitBlt(mem, 0, 0, w, hh, hdc, r.left, r.top, 0x00CC0020)
    bi = _BIH(ctypes.sizeof(_BIH), w, -hh, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * hh * 4)
    g32.GetDIBits(mem, bmp, 0, hh, buf, ctypes.byref(bi), 0)
    g32.DeleteObject(bmp)
    g32.DeleteDC(mem)
    u32.ReleaseDC(0, hdc)
    p = bytes(buf)
    uniq, nonwhite = set(), 0
    for i in range(0, len(p) - 4, 44):
        b, g, rr = p[i], p[i + 1], p[i + 2]
        uniq.add((rr, g, b))
        if not (rr > 245 and g > 245 and b > 245):
            nonwhite += 1
        if len(uniq) > 400:            # 早就够非白屏了，别白算
            return len(uniq), nonwhite, f"{w}x{hh}"
    return len(uniq), nonwhite, f"{w}x{hh}"


def http(port, path, timeout=6):
    with _OPENER.open(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def widget_count(port):
    try:
        d = json.loads(http(port, "/snap", timeout=5))
        return len(d.get("s") or [])
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8160)
    ap.add_argument("--interval", type=float, default=8.0)
    ap.add_argument("--strikes", type=int, default=3, help="连续几次白才判定")
    ap.add_argument("--min-widgets", type=int, default=30)
    ap.add_argument("--max-restarts", type=int, default=6)
    args = ap.parse_args()

    pidfile = Path(os.environ.get("TEMP", ".")) / f"morning-brief-watchdog-{args.port}.pid"
    try:
        pidfile.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    log(f"看门狗上线：端口 {args.port}，每 {args.interval:.0f}s 看一眼")
    strikes = 0
    restarts = 0
    misses = 0

    while True:
        time.sleep(args.interval)

        # 卡片已经关了（用户自己关的）→ 看门狗收工，别把窗口又拉起来。
        if card_hwnd() is None:
            misses += 1
            if misses >= 3:
                log("卡片窗口已经不在了，看门狗退出。")
                break
            continue
        misses = 0

        uniq, nonwhite, dim = pixel_stats()
        if dim == "被遮挡":
            strikes = 0                      # 取样无效，这一轮不算数
            continue
        wc = widget_count(args.port)

        white = uniq >= 0 and uniq < 200 and nonwhite < 800
        if white and wc >= args.min_widgets:
            strikes += 1
            log(f"疑似白屏 {strikes}/{args.strikes}（色数={uniq} 非白={nonwhite} "
                f"控件={wc} {dim}）")
        else:
            if strikes:
                log(f"恢复正常（色数={uniq} 控件={wc}），计数清零")
            strikes = 0

        if strikes < args.strikes:
            continue

        strikes = 0
        restarts += 1
        if restarts > args.max_restarts:
            log(f"已经重启过 {args.max_restarts} 次，不再自动重启（避免死循环）。")
            continue

        log(f"判定白屏 → 重启卡片（第 {restarts} 次）")
        try:
            http(args.port, "/quit", timeout=5)
        except Exception as e:
            log(f"  /quit 没成功：{e}")
        for _ in range(40):
            time.sleep(0.5)
            if card_hwnd() is None:
                break
        log("  旧窗口已关闭，重新拉起…")
        try:
            subprocess.run([sys.executable, str(LAUNCH), "--port", str(args.port),
                            "--no-watchdog"], cwd=str(REPO), timeout=300,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(8)
            log(f"  重启完成，控件数 = {widget_count(args.port)}")
        except Exception as e:
            log(f"  重启失败：{e}")

    try:
        pidfile.unlink()
    except Exception:
        pass


if __name__ == "__main__":
    main()
