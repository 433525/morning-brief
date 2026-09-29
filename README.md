# 晨报卡（morning-brief）— GoIM Agentic App 黑客松参赛作品

> 一句话：打开卡片，AI 自动抓取当天科技新闻、由「AI 编辑部」挑重点，并由「视觉主编」现做一张今日头版。

- 比赛：GoIM Agentic App 黑客松（https://create.gosim.org/agenticapp26/ ）
- 队伍：**共创**　ID：**小鞠老师**　赛道：**信息类 / 新闻场景**
- 报名帖：https://github.com/gosimfoundation/hackathon-agenticapp26/issues/5

## 现在能做到什么（全部实机验证过）

1. 打开卡片先播 3.12 秒开场 CG「Dawn / 破晓」，随后自动恢复上次晨报，头版也能一起回来
2. **常驻 AI 主编**：右下角「● AI 主编」展开对话条，一句话让它操作整个程序 —— 换主题、改条数、写关注点、生成计划、批准取数、取消、重新开始、打开某条、返回列表、前后条、换头版、画配图。界面上能点的，它都能做
3. 生成晨报：先出**取数计划**请你批准 → 官方 net 能力抓 Hacker News + TechMeme → AI 编辑部 3 个视角（技术 / 行业 / 读者）**背靠背独立评审** → 主编终审挑重点。**联网必须经你明确批准**（说过「批准」才放行，主编自己不能越过这一步）
4. 列表页：编号 + 来源缩略图 + 三方推荐标记 + AI 主编用时与 token 数
5. **今日头版**：深色 hero 卡片，按当天头条现画的横图 + 英文头版标语压在图上，点「换一张头版」可重画
6. 点进任意一条 → 卡片内阅读页：官方摘要 / AI 解读 / 更多报道 / 讨论 / 原文链接
7. **AI 配图**：阅读页顶部按标题现场生成配图，「重画」能换新图，缓存秒开
8. 全程能看到"编辑部交回几份意见、每个人用了多少秒"，不是黑盒
9. **语音对话**：点「🎙 说话」直接对主编讲话（中文识别）；点「念这一期」把整期念出来；主编答完话会自动配声音（可关）
10. **读者画像**：这份报记得你读过什么、常读哪些主题、你亲口说的偏好 —— 并且在主编选稿时真的用上
11. **本报记忆**：每一期的入选条目进本地档案；再读相关新闻时，页面会自动列出「本报追过这条线索」

### 常驻 AI 主编的内部结构（四层）

| 层 | 实现 | 作用 |
| --- | --- | --- |
| 感知 | `ag_context()` | 把界面现状（在哪页、什么设置、入选了哪些条目、在读哪条、读者画像）讲给模型 |
| 决策 | `ag_turn()` / `ag_reply()` | 多轮工具调用循环，一轮最多六步，带重复调用拦截与未完成续推 |
| 工具 | `ag_tools` / `ag_do()` | 15 个工具，唯一派发入口，与界面按钮一一对应 |
| 界面 | `ag_dock` | 常驻对话条（气泡流 + 输入框 + 快捷短语 + 语音按钮） |

> **语音能力需要宿主补丁**：`my-entry/patches/host-voice.patch`（打在官方 `OctoSense-App-Hub` 上，说明见该目录 README）。
> 没打补丁的机器上卡片会自动降级 —— 隐藏语音按钮，其余功能照常。

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

## 仓库与推送（本机注意）

- 仓库地址：https://github.com/jscjscjscjscjsc/morning-brief （public）
- 本机到 `github.com:443` 的 HTTPS 被阻断，且 `~/.gitconfig` 里的本地代理 `127.0.0.1:7899` 已失效，因此**推送走 SSH**：

```powershell
# 远端已配置为 ssh://git@ssh.github.com:443/jscjscjscjscjsc/morning-brief.git
$env:GIT_SSH_COMMAND='"C:/Windows/System32/OpenSSH/ssh.exe" -o StrictHostKeyChecking=no'
git push
```

- 若想恢复 HTTPS 推送：启动本地代理后 `git config --global http.https://github.com.proxy http://127.0.0.1:7899`，或把该行删掉改用直连。
## 目录结构

| 路径 | 说明 |
| --- | --- |
| `my-entry/morning-brief/bundle/main.splash` | **主代码**（2420 行，唯一需要改的文件） |
| `my-entry/morning-brief/bundle/listing.json` | 卡片上架信息（副标题、关键词、截图、发布者） |
| `my-entry/evidence/` | 每一步的实机截图（验收证据） |
| `项目复盘/` | 每轮进化复盘（外行话术，能看懂"这轮到底变好了什么"） |
| `进度交接_第30轮前.md` | **交接文档**：新同学/新对话看这一个文件就能接着干 |
| `00`–`07` 开头的 Markdown | 比赛策略、分工、实操指南、跑通实录、官方仓库下载说明 |
| `tools/` | 运行 / 截图 / 语法校验脚本 |

## 接力任务与贡献

- **接力任务（GitHub Issue #1）**：https://github.com/jscjscjscjscjsc/morning-brief/issues/1
  —— 后来的人/AI agent 看这一条就知道背景与下一步。
- **AI agent 入口**：仓库根目录的 `AGENTS.md`（背景 / 状态 / 环境 / 红线 / 贡献流程）。
- 提交改动：开 `round-<轮次>/<主题>` 分支 → PR（模板已备好）→ 维护者默认全同意。

## 贡献指南（欢迎继续改）

1. 改代码前先读 `进度交接_第30轮前.md` 的「六、坑（务必记住）」
2. 改 `main.splash` 的硬规矩：
   - 不用 `contains / slice / sort / map / filter`；保留字 `ok / me / scope / self / _` 不可作变量名
   - 数字拼串要先转文本再拼（`"" + n`）；拼接结果先 `let` 成变量再传参；`llm.chat` 的 `max_tokens <= 2048`
   - 渲染循环里不要再遍历同一数据源（会打断迭代，只出第一行）；JSON 缺字段要先取键再判空
   - `View{show_bg: true}` 的底色不渲染，要用 `RoundedView` / `SolidView`
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