# 晨报卡（morning-brief）— GoIM Agentic App 黑客松参赛作品

> 一句话：打开卡片，AI 自动抓取当天科技新闻、由「AI 编辑部」挑重点，并由「视觉主编」现做一张今日头版。

- 比赛：GoIM Agentic App 黑客松（https://create.gosim.org/agenticapp26/ ）
- 队伍：**共创**　ID：**小鞠老师**　赛道：**信息类 / 新闻场景**
- 报名帖：https://github.com/gosimfoundation/hackathon-agenticapp26/issues/5

## 现在能做到什么（全部实机验证过）

1. 打开卡片自动恢复上次晨报，头版也能一起回来
2. 一键「生成晨报」：先出**取数计划**请你批准 → 官方 net 能力抓 Hacker News + TechMeme → AI 编辑部 3 个视角（技术 / 行业 / 读者）**背靠背独立评审** → 主编终审挑重点
3. 列表页：条条有来源与缩略图、三方推荐标记、AI 主编用时与 token 数
4. **今日头版**：结果页顶部一张按当天头条现画的横图 + 英文头版标语，点「换一张头版」可重画
5. 点进任意一条 → 卡片内阅读页：官方摘要 / AI 解读 / 更多报道 / 讨论 / 原文链接
6. **AI 配图**：阅读页顶部按标题现场生成配图，「重画」能换新图，缓存秒开
7. 全程能看到"编辑部交回几份意见、每个人用了多少秒"，不是黑盒

## 快速开始（Windows + PowerShell）

> 前置：本机需已安装 OctoSense App Hub 与 card-host（见 `04_项目实操指南.md`），并已克隆官方 `OctoScript-App-Design-Flow`。

```powershell
# 1) 停掉旧进程
powershell -ExecutionPolicy Bypass -File tools\stop.ps1

# 2) 启动卡片服务（端口 8136）
powershell -ExecutionPolicy Bypass -File tools\run.ps1

# 3) 打开界面后，截图看效果（存到 my-entry/evidence/）
powershell -ExecutionPolicy Bypass -File tools\shot.ps1 -Name 'my_shot.png'

# 4) 改完 main.splash 必须做语法校验
python tools\brace.py
```

`tools\run.ps1` 里的路径按本机实际安装位置调整即可。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `my-entry/morning-brief/bundle/main.splash` | **主代码**（1783 行，唯一需要改的文件） |
| `my-entry/morning-brief/bundle/listing.json` | 卡片上架信息（副标题、关键词、截图、发布者） |
| `my-entry/evidence/` | 每一步的实机截图（验收证据） |
| `项目复盘/` | 每轮进化复盘（外行话术，能看懂"这轮到底变好了什么"） |
| `进度交接_第27轮前.md` | **交接文档**：新同学/新对话看这一个文件就能接着干 |
| `00`–`05` 开头的 Markdown | 比赛策略、分工、实操指南、跑通实录 |
| `tools/` | 运行 / 截图 / 语法校验脚本 |

## 贡献指南（欢迎继续改）

1. 改代码前先读 `进度交接_第27轮前.md` 的「六、坑（务必记住）」
2. 改 `main.splash` 的硬规矩：
   - 不用 `contains / slice / sort / map / filter`；保留字 `ok / me / scope / self / _` 不可作变量名
   - 数字拼串要 `"" + n`；拼接结果先 `let` 成变量再传参；`llm.chat` 的 `max_tokens <= 2048`
   - makepad 的 `on_render` 子控件每帧重建，**必须显式 `.render()`**
   - 文件编码：`main.splash` 用 UTF-8 无 BOM + LF
3. 改完必须：`python tools\brace.py`（语法）→ `tools\run.ps1`（实跑）→ `tools\shot.ps1`（截图留证）
4. 每轮完成后：写一份 `项目复盘/日期_第N轮_主题.md`，并把交接文档更新到下一轮
5. 提交：`git add -A` → `git commit -m "第N轮：做了什么"` → `git push`

## 设计原则（为什么这么做）

- **先授权、再取数**：不批准不联网，取数范围与域名明示
- **不补齐条数**：部分来源失败就只展示成功来源，并列出失败项
- **可核验**：每条新闻都能看到来源、时间、原文链接
- **看得见的过程**：编辑部几个视角、各自用时多少秒，全部摆在明面上

## 许可

比赛作品，仅供学习与评审使用；新闻内容版权归原站点所有，本作品只做聚合与链接。