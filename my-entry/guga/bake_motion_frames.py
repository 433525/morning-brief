# -*- coding: utf-8 -*-
"""咕嘎桌宠 → 晨报卡：把桌宠里的 2D 变换动画离线烘焙成逐帧贴图（v2，按边距约束）。

桌宠（PyQt）里，呼吸/蹦跳/抖动/探头/傲娇摆头/前倾这些动作是运行时对同一张
立绘做位移+挤压+旋转算出来的；卡片的 splash 脚本没有这些变换原语，
所以在这里把同一套变换预先算成静止帧，运行时换帧即可复刻同一套动作语义。

v2 修正：立绘脚底正好贴着画布底边、左右边距只有 3–16px，
        所以「向上抬」先做小幅整体收缩（留出头顶空间），
        「旋转」改为绕「脚底上方 20px」为轴，宽的部分离轴近、不会被裁；
        烘焙完逐帧打印留白，任何一帧越过画布边界都会在这里暴露。

输入：晨报卡 bundle/assets/guga/ 下六张表情贴图（当前 160x222；脚本按实际尺寸自适应）
输出：bundle/assets/guga/motion/ 下 14 张动作帧，**尺寸与基础帧完全一致**

v4 修正（2026-10-12，用户报「企鹅不停闪动」的根因之一）：
    动作帧一律输出成与基础帧同尺寸。之前输出 168x233，而基础帧是 160x222 ——
    运行时两种图被拉伸进同一个 Image 控件，每换一次帧整只企鹅就缩放 5%，
    1Hz 硬切，看上去就是在闪。现在帧与帧之间除了动作本身没有任何缩放差。
    画笔尺寸也从素材真实尺寸推导（不再硬编码 216x300），位移量按同一个比例换算，
    所以换素材尺寸（比如以后换上更大的立绘）不用改动画参数。
"""
import os
from PIL import Image

BUNDLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'morning-brief', 'bundle')
G = os.path.join(BUNDLE, 'assets', 'guga')
OUT = os.path.join(G, 'motion')
EXPRS = ['idle', 'cheer', 'pout', 'sad', 'sleepy', 'surprised']


def load(expr):
    return Image.open(os.path.join(G, expr + '.png')).convert('RGBA')


# 画笔尺寸 = 素材真实尺寸；基准尺寸 216x300 只用来换算位移量比例。
W, H = load(EXPRS[0]).size
OUT_W, OUT_H = W, H
SCALE = W / 216.0
PIVOT_Y = H - 20 * SCALE  # 旋转轴：脚底上方 20px（按素材比例）


def spx(v):
    """位移量换算：动画参数是按 216 宽的设计稿写的，按素材实际宽度等比缩放。"""
    r = int(round(v * SCALE))
    if r == 0 and v != 0:
        r = 1 if v > 0 else -1
    return r


def canvas():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def shrink_center(im, s):
    """整体收缩，居中放回（四周都留出空间）"""
    nw, nh = max(1, int(round(W * s))), max(1, int(round(H * s)))
    scaled = im.resize((nw, nh), Image.LANCZOS)
    out = canvas()
    out.paste(scaled, ((W - nw) // 2, (H - nh) // 2), scaled)
    return out


def squash_bottom(im, sx, sy):
    """挤压/拉伸：以「脚底中心」为支点，重心不飘、脚不离地"""
    nw, nh = max(1, int(round(W * sx))), max(1, int(round(H * sy)))
    scaled = im.resize((nw, nh), Image.LANCZOS)
    out = canvas()
    out.paste(scaled, ((W - nw) // 2, H - nh), scaled)
    return out


def breathe(im):
    """呼吸帧：脚底锚点，纵向微缩（脚不离地、头顶只抬 1 逻辑像素内）。

    v3 之前这里是 move(im, 0, -5) —— 整只精灵上下跳 5px，运行时以 1Hz
    在两帧之间硬切，看起来就是「企鹅不停闪动」（用户实机反馈）。
    桌宠（PyQt 版）的真实呼吸是 1.005 的缩放 + 不到 1px 的浮动，
    这里近似成同语义：横向 -0.2%、纵向 +1.0%，锚在脚底。
    """
    return squash_bottom(im, 0.998, 1.010)


def spin(im, deg):
    """绕脚底上方 20px 转（expand=False：画布不放大，宽处离轴近不会裁）"""
    return im.rotate(deg, resample=Image.BICUBIC, expand=False, center=(W / 2, PIVOT_Y))


def move(im, dx, dy):
    out = canvas()
    out.paste(im, (dx, dy), im)
    return out


def save(im, name):
    small = im.resize((OUT_W, OUT_H), Image.LANCZOS)
    path = os.path.join(OUT, name + '.png')
    small.save(path, optimize=True)
    bb = small.split()[3].getbbox()
    l, t, r, b = bb
    mar = (l, t, OUT_W - r, OUT_H - b)
    # 脚底贴边（b == 0）是这批素材的常态：立绘本来就画到画布底边。
    # 只查左右与顶部 —— 那才是旋转/位移真正会把内容推出画布的方向。
    flag = ''
    if l < 1 or t < 1 or r > OUT_W - 1:
        flag = '  <<< 越界!'
    print('%-20s %6dB  留白 l%-3d t%-3d r%-3d b%-3d%s' %
          (name + '.png', os.path.getsize(path), mar[0], mar[1], mar[2], mar[3], flag))


def main():
    os.makedirs(OUT, exist_ok=True)
    bases = {e: load(e) for e in EXPRS}

    # 呼吸帧：脚底锚点微缩（breathe），不再整只上跳
    for e in EXPRS:
        im = bases[e]
        if e == 'sad':
            im = shrink_center(im, 0.96)
        save(breathe(im), e + '_breath')

    # 蹦（开心）：收缩后起跳（脚下留出空气）＋ 落地挤压（脚不离地）
    save(move(squash_bottom(bases['cheer'], 0.975, 0.96), 0, spx(-26)), 'cheer_jump')
    save(squash_bottom(bases['cheer'], 1.035, 0.94), 'cheer_squat')

    # 抖（受惊）：左右摇摆。角度收到 1.3°、横移各 1px 且方向与转角同侧 ——
    # 受惊立绘的左边缘只有 3px 余量，原参数（2.2° + 横移 2px）会把左上角推出画布，
    # 烘焙脚本的越界告警就是在这一步逮到它的。
    save(move(spin(bases['surprised'], 1.3), 1, spx(-2)), 'surprised_wobL')
    save(move(spin(bases['surprised'], -1.3), -1, spx(-2)), 'surprised_wobR')

    # 傲娇摆头：绕脚底慢摆 + 略昂头
    save(move(spin(bases['pout'], 2.6), 0, spx(-6)), 'pout_swingL')
    save(move(spin(bases['pout'], -2.6), 0, spx(-6)), 'pout_swingR')

    # 偷偷看我：收缩一点侧移探头（不歪斜，保持比例）
    save(move(spin(shrink_center(bases['idle'], 0.95), 2.6), spx(11), spx(-4)), 'idle_peek')

    # 指点江山：前倾
    save(move(spin(bases['pout'], 5.5), spx(4), spx(-4)), 'pout_go')

    print('done ->', os.path.abspath(OUT))


if __name__ == '__main__':
    main()
