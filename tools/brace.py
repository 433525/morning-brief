import pathlib, json
p = pathlib.Path(r"C:\Users\Admin（无密码）\Desktop\数据文件\黑客松比赛项目\my-entry\morning-brief\bundle\main.splash")
src = p.read_text(encoding="utf-8")
lines = src.split("\n")
depth = {"{":0, "(":0, "[":0}
pairs = {"}":"{", ")":"(", "]":"["}
stack = []
i = 0
in_str = False
in_line_comment = False
esc = False
ln = 1
col = 0
events = []
for ch in src:
    col += 1
    if ch == "\n":
        ln += 1; col = 0; in_line_comment = False; continue
    if in_line_comment: continue
    if in_str:
        if esc: esc = False
        elif ch == "\\": esc = True
        elif ch == '"': in_str = False
        continue
    if ch == '"': in_str = True; continue
    if ch == "/" and col < len(lines[ln-1]) and lines[ln-1][col] == "/":
        in_line_comment = True; continue
    if ch in "{([":
        stack.append((ch, ln, col))
    elif ch in "})]":
        if not stack:
            events.append(f"EXTRA CLOSE {ch} at line {ln} col {col}")
        elif stack[-1][0] != pairs[ch]:
            events.append(f"MISMATCH: open {stack[-1][0]} at line {stack[-1][1]} col {stack[-1][2]} closed by {ch} at line {ln} col {col}")
            stack.pop()
        else:
            stack.pop()
print("in_str at EOF:", in_str)
print("unclosed:", stack[:12])
print("events:", events[:12])
print("total lines:", len(lines))
