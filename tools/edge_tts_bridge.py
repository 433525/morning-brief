#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""咕嘎的软萌音桥 · edge-tts 合成，写给晨报卡的宿主进程用。

为什么需要这个桥：
    晨报卡的桌面版桌宠用的是 edge-tts 的 `zh-CN-XiaoyiNeural`（软萌少女音）
    + 提高音调；而卡片宿主的语音只走 Windows 自带引擎（本机最像人的是
    Huihui 的 SAPI 音，离"人声"很远）。宿主进程里没有 Python 运行时，
    所以由它按需拉起本脚本：喂一段文本，换回一段 16-bit 单声道 PCM。

协议（宿主侧照抄即可）：
    启动：python edge_tts_bridge.py --serve
    宿主写一行 JSON 到 stdin，桥回一行 JSON 到 stdout：
        请求  {"text": "...", "voice": "zh-CN-XiaoyiNeural", "rate": "+14%", "pitch": "+16Hz"}
        成功  {"ok": true, "sample_rate": 24000, "samples_b64": "...", "seconds": 3.2, "cached": false}
        失败  {"ok": false, "error": "..."}
    PCM 是 s16le 单声道。合成结果按 (text,voice,rate,pitch) 的哈希缓存到
    临时目录，同一句话第二次说是零网络开销。

为什么走「常驻进程 + 行 JSON」而不是一次一进程：
   边缘首句合成约 1~2 秒，拉起一次 Python 解释器还要 ~0.3 秒；
   常驻可以把解释器启动只付一次，之后每句只有网络合成的时间。
"""
import argparse
import asyncio
import base64
import hashlib
import io
import json
import os
import sys
import tempfile
import time

VOICE_DEFAULT = "zh-CN-XiaoyiNeural"   # 桌面版同款软萌音
RATE_DEFAULT = "+14%"
PITCH_DEFAULT = "+16Hz"
CACHE_DIR = os.path.join(tempfile.gettempdir(), "guga-edge-tts-cache")
CACHE_MAX = 240
CACHE_TTL = 7 * 24 * 3600

_voice = VOICE_DEFAULT


def _load_asr():  # pragma: no cover - 兼容旧名
    pass


def _cache_path(key):
    return os.path.join(CACHE_DIR, key + ".pcm.json")


def _cache_get(key):
    p = _cache_path(key)
    try:
        if not os.path.exists(p):
            return None
        if time.time() - os.path.getmtime(p) > CACHE_TTL:
            os.remove(p)
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _cache_put(key, value):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        files = []
        for name in os.listdir(CACHE_DIR):
            fp = os.path.join(CACHE_DIR, name)
            try:
                files.append((os.path.getmtime(fp), fp))
            except OSError:
                pass
        if len(files) >= CACHE_MAX:
            files.sort()
            for _, fp in files[: len(files) - CACHE_MAX + 1]:
                try:
                    os.remove(fp)
                except OSError:
                    pass
        with open(_cache_path(key), "w", encoding="utf-8") as f:
            json.dump(value, f)
    except Exception:
        pass


def system_proxy():
    """读 Windows 的系统代理（HKCU Internet Settings）。

    为什么需要：edge-tts 打的是 speech.platform.bing.com，在部分网络下
    IPv4 直连会被重置（TLS handshake 阶段 connection reset）；系统里已经
    配好的本地代理能一路通到 HTTP 层。桥优先用 EDGE_TTS_PROXY 环境变量，
    没配就自动读系统代理；都没有就直连（在能直连的网络里同样工作）。
    """
    env = os.environ.get("EDGE_TTS_PROXY") or os.environ.get("HTTPS_PROXY")         or os.environ.get("https_proxy")
    if env:
        return env
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
        enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
        if enable:
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
            if server:
                if not server.startswith("http"):
                    server = "http://" + server
                return server
    except Exception:
        pass
    return None


async def _synth_mp3(text, voice, rate, pitch, proxy=None):
    import edge_tts
    kw = {}
    if proxy:
        kw["proxy"] = proxy
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                       volume="+0%", **kw)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


def _mp3_to_pcm(mp3_bytes):
    """mp3 -> (samples list[int16], sample_rate)。用 miniaudio 解码。"""
    import miniaudio
    decoded = miniaudio.decode(mp3_bytes, output_format=miniaudio.SampleFormat.SIGNED16,
                               nchannels=1, sample_rate=24000)
    return list(decoded.samples), decoded.sample_rate


def synth(text, voice, rate, pitch, use_cache=True):
    """同步合成一段，返回 (pcm_s16le_bytes, sample_rate, cached)。"""
    key = hashlib.sha256(
        (text + "|" + voice + "|" + rate + "|" + pitch).encode("utf-8")).hexdigest()[:32]
    if use_cache:
        hit = _cache_get(key)
        if hit is not None:
            raw = base64.b64decode(hit["samples_b64"])
            return raw, hit["sample_rate"], True

    proxy = system_proxy()
    mp3 = asyncio.run(asyncio.wait_for(_synth_mp3(text, voice, rate, pitch, proxy), timeout=25))
    if not mp3 and proxy:
        # 代理挂了就直连再试一次（网络环境换过的情况）
        mp3 = asyncio.run(asyncio.wait_for(_synth_mp3(text, voice, rate, pitch, None), timeout=25))
    if not mp3:
        raise RuntimeError("edge-tts 返回空音频")
    samples, sr = _mp3_to_pcm(mp3)
    if not samples:
        raise RuntimeError("解码后没有采样")
    # int16 小两端
    raw = bytearray()
    for s in samples:
        if s > 32767:
            s = 32767
        elif s < -32768:
            s = -32768
        raw += int(s).to_bytes(2, "little", signed=True)
    raw = bytes(raw)
    if use_cache:
        _cache_put(key, {"samples_b64": base64.b64encode(raw).decode("ascii"),
                         "sample_rate": sr, "seconds": len(samples) / float(sr or 1)})
    return raw, sr, False


def serve():
    """常驻模式：逐行读请求，逐行回结果。"""
    global _voice
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            out.write(json.dumps({"ok": False, "error": "bad json"}) + "\n")
            out.flush()
            continue
        text = (req.get("text") or "").strip()
        if not text:
            out.write(json.dumps({"ok": False, "error": "empty text"}) + "\n")
            out.flush()
            continue
        voice = req.get("voice") or _voice
        rate = req.get("rate") or RATE_DEFAULT
        pitch = req.get("pitch") or PITCH_DEFAULT
        try:
            raw, sr, cached = synth(text, voice, rate, pitch)
            out.write(json.dumps({
                "ok": True,
                "sample_rate": sr,
                "samples_b64": base64.b64encode(raw).decode("ascii"),
                "seconds": round(len(raw) / 2.0 / float(sr or 1), 2),
                "cached": cached,
                "voice": voice,
            }) + "\n")
        except Exception as e:
            out.write(json.dumps({"ok": False, "error": str(e)[:200]}) + "\n")
        out.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="常驻：逐行 JSON 请求/响应")
    ap.add_argument("--probe", action="store_true", help="探测：合成一句短音并回报")
    ap.add_argument("--text", default="咕嘎～本鹅在呢。")
    ap.add_argument("--voice", default=VOICE_DEFAULT)
    ap.add_argument("--rate", default=RATE_DEFAULT)
    ap.add_argument("--pitch", default=PITCH_DEFAULT)
    ap.add_argument("--out", default="", help="把 PCM 写到文件（调试用）")
    args = ap.parse_args()

    global _voice
    _voice = args.voice

    if args.probe:
        t0 = time.time()
        raw, sr, cached = synth(args.text, args.voice, args.rate, args.pitch, use_cache=False)
        info = {"ok": True, "engine": "edge-tts", "voice": args.voice,
                "sample_rate": sr, "seconds": round(len(raw) / 2.0 / sr, 2),
                "ms": int((time.time() - t0) * 1000)}
        print(json.dumps(info, ensure_ascii=False))
        if args.out:
            with open(args.out, "wb") as f:
                f.write(raw)
        return 0

    if args.serve:
        # 启动自检：探一句短的，把引擎状态写进日志（宿主可以据此知道桥能用）
        try:
            t0 = time.time()
            synth("咕嘎，本鹅上线了。", _voice, RATE_DEFAULT, PITCH_DEFAULT)
            sys.stderr.write("[guga-voice-bridge] ready in %dms, voice=%s\n"
                             % (int((time.time() - t0) * 1000), _voice))
        except Exception as e:
            sys.stderr.write("[guga-voice-bridge] probe failed: %s\n" % e)
        sys.stderr.flush()
        serve()
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
