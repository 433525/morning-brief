# -*- coding: utf-8 -*-
"""咕嘎说话口型帧：闭嘴基准帧 + 张嘴补丁 -> 透明底、可换帧的三张口型。

素材（桌宠同源的说话动作图，285x384，浅蓝背景）：
  70da9472 = 闭嘴微笑（基准帧，人物位置基准）
  95ee9e5f = 张口大笑（只取嘴部）

处理链（每一步都有理由，出错时逐段有打印）：
  1. 嘴部补丁：两图人物位置差 (-10,+13)（互相关测得），取源区时要补上偏移，
     矩形 (137,162)-(206,226) 由 10px 网格核准 —— 只盖嘴，不碰睫毛/轮廓。
  2. 去背景：从四边泛洪，判据是"偏蓝且亮"（b-r>12 且亮度>140），
     白肚皮 b-r≈0 不会被误伤。
  3. 去水印：保留面积 > 0.8% 的连通块（"AI生成"字样是孤立小块）。
  4. 对齐：角色高度缩放到 279px、脚底贴底、水平中心 108 —— 与现有的
     idle/cheer/pout 等六张素材完全同一构图，换帧时人物不会跳。

输出：bundle/assets/guga/talk0.png（闭嘴）/ talk1.png（微张）/ talk2.png（大张），
      216x300 RGBA，和那六张同规格。
"""
import os
from collections import deque
from PIL import Image, ImageFilter

SRC = r'C:\Users\Admin（无密码）\Desktop\图片库\咕嘎说话动作'
BUNDLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'morning-brief', 'bundle')
G = os.path.join(BUNDLE, 'assets', 'guga')

BASE = '70da9472a6e74edda2c3eeca1ebab6db.jpeg~tplv-a9rns2rl98-ds_wm_1_5_dk.png'
OPEN = '95ee9e5fa3834dfa9a80d5eb6ba812fa.jpeg~tplv-a9rns2rl98-ds_wm_1_5_dk.png'

MOUTH = (137, 162, 206, 226)
ALIGN_DX = -10
ALIGN_DY = 13

OUT_W, OUT_H = 216, 300          # 与现有六张素材同画布
TARGET_H = 279                   # 现有素材的角色高度
TARGET_CX = 108                  # 现有素材的角色水平中心
MIN_BLOB = 0.008                 # 小于画布 0.8% 的连通块 = 水印/杂点


def load(name):
    return Image.open(os.path.join(SRC, name)).convert('RGB')


def mouth_mask(size, feather=14):
    w, h = size
    mask = Image.new('L', size, 255)
    px = mask.load()
    for yy in range(h):
        for xx in range(w):
            d = min(xx, yy, w - 1 - xx, h - 1 - yy)
            if d < feather:
                px[xx, yy] = int(255 * (d / feather))
    return mask.filter(ImageFilter.GaussianBlur(3.0))


def blend_mouth(base, open_im, alpha=1.0):
    out = base.copy()
    x0, y0, x1, y1 = MOUTH
    patch = open_im.crop((x0 + ALIGN_DX, y0 + ALIGN_DY, x1 + ALIGN_DX, y1 + ALIGN_DY))
    mask = mouth_mask(patch.size)
    if alpha < 1.0:
        mask = mask.point(lambda v: int(v * alpha))
    out.paste(patch, (x0, y0), mask)
    return out


def is_bg(px, x, y):
    r, g, b = px[x, y]
    lum = (r + g + b) / 3
    return (b - r) > 12 and lum > 140 and b > 150


def remove_bg(im):
    """四边泛洪去背景（偏蓝且亮的像素），返回 RGBA 图"""
    w, h = im.size
    px = im.load()
    out = im.convert('RGBA')
    opx = out.load()
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_bg(px, x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg(px, x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    while q:
        x, y = q.popleft()
        opx[x, y] = (0, 0, 0, 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and is_bg(px, nx, ny):
                seen[ny * w + nx] = 1
                q.append((nx, ny))

    # 连通块过滤：保留大块（水印是孤立小块）
    a = out.split()[3].load()
    keep = bytearray(w * h)
    vis = bytearray(w * h)
    min_size = w * h * MIN_BLOB
    dropped = 0
    for y in range(h):
        for x in range(w):
            if vis[y * w + x] or a[x, y] == 0:
                continue
            cq = deque([(x, y)])
            vis[y * w + x] = 1
            blob = []
            while cq:
                bx, by = cq.popleft()
                blob.append((bx, by))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = bx + dx, by + dy
                    if 0 <= nx < w and 0 <= ny < h and not vis[ny * w + nx] and a[nx, ny] > 0:
                        vis[ny * w + nx] = 1
                        cq.append((nx, ny))
            if len(blob) < min_size:
                dropped += 1
                for bx, by in blob:
                    opx[bx, by] = (0, 0, 0, 0)
            else:
                for bx, by in blob:
                    keep[by * w + bx] = 1
    print('     连通块过滤：保留大块，丢弃 %d 个小块' % dropped)
    return out


def fit_canvas(im):
    """角色缩放到 TARGET_H、脚底贴底、中心 TARGET_CX，放进 OUT_W x OUT_H 画布"""
    bb = im.split()[3].getbbox()
    l, t, r, b = bb
    ch, cw = b - t, r - l
    s = TARGET_H / ch
    nw, nh = max(1, int(round(cw * s))), max(1, int(round(ch * s)))
    ch_im = im.crop(bb).resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGBA', (OUT_W, OUT_H), (0, 0, 0, 0))
    x = int(round(TARGET_CX - nw / 2))
    y = OUT_H - nh
    canvas.paste(ch_im, (x, y), ch_im)
    return canvas


def main():
    base = load(BASE)
    oper = load(OPEN)

    talk0 = base
    talk1 = blend_mouth(base, oper, 0.55)
    talk2 = blend_mouth(base, oper, 1.0)

    for name, im in [('talk0', talk0), ('talk1', talk1), ('talk2', talk2)]:
        print('   处理', name)
        cleaned = remove_bg(im)
        fitted = fit_canvas(cleaned)
        bb = fitted.split()[3].getbbox()
        path = os.path.join(G, name + '.png')
        fitted.save(path, optimize=True)
        print('%-10s %6dB  bbox=%s' % (name + '.png', os.path.getsize(path), bb))

    # 预览：三帧 + 与 idle 叠放对比构图
    idle = Image.open(os.path.join(G, 'idle.png'))
    H = 300
    sheet = Image.new('RGBA', (216 * 5 + 60, H + 20), (238, 240, 246, 255))
    xs = [10, 236, 462]
    for x, n in zip(xs, ['talk0', 'talk1', 'talk2']):
        im = Image.open(os.path.join(G, n + '.png'))
        sheet.paste(im, (x, 10), im)
    sheet.paste(idle, (688, 10), idle)
    im4 = Image.open(os.path.join(G, 'cheer.png'))
    sheet.paste(im4, (914, 10), im4)
    sheet.save(r'C:\Users\Admin（无密码）\Desktop\数据文件\_talk_final_check.png')
    print('预览已存')


if __name__ == '__main__':
    main()
