#!/usr/bin/env python3
"""main.splash 语法体检：括号配平 + 字符串闭合。

用法：
    python tools/brace.py                       # 自动定位 my-entry/morning-brief/bundle/main.splash
    python tools/brace.py <path/to/main.splash> # 指定文件

退出码：0 = 通过，1 = 发现问题（CI 依赖这个）。
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT = REPO / "my-entry" / "morning-brief" / "bundle" / "main.splash"

p = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
if not p.is_file():
    print(f"[FAIL] 找不到文件：{p}")
    sys.exit(1)

src = p.read_text(encoding="utf-8")
lines = src.split("\n")
pairs = {"}": "{", ")": "(", "]": "["}
stack = []
in_str = False
in_line_comment = False
esc = False
ln = 1
col = 0
events = []

for ch in src:
    col += 1
    if ch == "\n":
        ln += 1
        col = 0
        in_line_comment = False
        continue
    if in_line_comment:
        continue
    if in_str:
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == '"':
            in_str = False
        continue
    if ch == '"':
        in_str = True
        continue
    # 行注释判定：本行 col 处确实是 '//'（col 是 1-based 字符列，下标 col-1 是当前字符）
    if ch == "/" and col < len(lines[ln - 1]) and lines[ln - 1][col] == "/":
        in_line_comment = True
        continue
    if ch in "{([":
        stack.append((ch, ln, col))
    elif ch in "})]":
        if not stack:
            events.append(f"多余的右括号 {ch} @ 第 {ln} 行 第 {col} 列")
        elif stack[-1][0] != pairs[ch]:
            o = stack[-1]
            events.append(f"括号不匹配：第 {o[1]} 行 第 {o[2]} 列的 {o[0]} 被第 {ln} 行 第 {col} 列的 {ch} 关闭")
            stack.pop()
        else:
            stack.pop()

ok = (not in_str) and (not stack) and (not events)

print(f"文件：{p}")
print(f"总行数：{len(lines)}")
print(f"字符串在文末仍未闭合：{in_str}")
print(f"未闭合的括号：{stack[:12] if stack else '无'}")
print(f"异常：{events[:12] if events else '无'}")

if ok:
    print("[PASS] 语法体检通过")
    sys.exit(0)

print("[FAIL] 语法体检未通过，请修掉上面列出的问题")
sys.exit(1)
