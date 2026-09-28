# AGENTS.md — 给接手的 AI Agent 的入口

> 你（AI agent）打开这个仓库时，请先读完本文件，再看 `进度交接_第30轮前.md`。
> 这一个文件讲清：这是什么项目、现在到哪一步、怎么跑起来、什么不能碰、下一步做什么。
>
> **接力任务（GitHub Issue #1）**：https://github.com/jscjscjscjscjsc/morning-brief/issues/1
> —— 那是本轮起要推进的目标清单，动手前先看它。

---

## 一、这是什么

**晨报卡（morning-brief）** —— GoIM Agentic App 黑客松参赛作品（信息类 / 新闻场景）。

一句话：打开卡片，AI 自动抓取当天科技新闻，由「AI 编辑部」挑重点，由「视觉主编」现做一张今日头版，
并且有一位**常驻 AI 主编**——用户说一句话，它就能操作整个程序。

- 比赛官网：https://create.gosim.org/agenticapp26/
- 报名帖：https://github.com/gosimfoundation/hackathon-agenticapp26/issues/5
- 队伍：共创（小鞠老师）
- 作品仓库：本仓库（public）

## 二、技术栈（重要，别用错工具）

作品跑在 **OctoSense App Hub** 的 `card-host` 里，界面用 **splash 脚本**（一种类 makepad 的 DSL）写的，
大模型能力走宿主的 `llm` 服务（`host.request("llm.chat", ...)`）。

- **主代码只有一个文件**：`my-entry/morning-brief/bundle/main.splash`（约 2400 行）
- `my-entry/morning-brief/bundle/manifest.json`：能力清单（capabilities / network.hosts / 哈希）
- `my-entry/morning-brief/bundle/listing.json`：上架信息（副标题、关键词、发布者）

⚠️ **官方运行环境不在本仓库里**（被 `.gitignore` 排除了）。你需要另建一套：

1. `OctoScript-App-Design-Flow`（官方开发流程仓库，含 `tools/octo` 驱动脚本）
2. `OctoSense-App-Hub`（含 `card-host` 宿主）
3. 按 `04_项目实操指南.md` 一步步装好

装好后，运行一个卡片的标准动作是：

```bash
# 语法校验（改完 main.splash 必做；仓库里有同一份脚本）
python tools/brace.py

# 启动卡片（card-host，端口自定，下面以 8136 为例）
python <OctoScript-App-Design-Flow>/tools/octo run my-entry/morning-brief/bundle \
    --port 8136 --detach --app-data <一个可写的状态目录>

# 截图留证
python <OctoScript-App-Design-Flow>/tools/octo shot 8136 my-entry/evidence/xxx.png

# 用交互桥驱动（窗口是 412x892 逻辑点；截图是 2 倍，点击坐标要 ÷2）
curl -s "127.0.0.1:8136/snap"                     # 读控件树（含文字与矩形）
curl -s "127.0.0.1:8136/click?x=100&y=200&wait=1" # 点击
curl -s "127.0.0.1:8136/t?t=文字&wait=1"           # 输入（先点输入框）
curl -s "127.0.0.1:8136/quit"                     # 退出
```

> 本机（Windows 开发机）的快捷脚本在 `tools/`（`run.ps1` / `stop.ps1` / `shot.ps1`），
> 路径按你机器的实际安装位置改。

## 三、现在到哪一步了

**已完成第 29 轮。** 产品现在能跑通的完整链路：

1. 开场 CG「Dawn / 破晓」（3.12 秒，网格 → 粒子汇聚 → 破晓光带 → 轨道环 → 洋红扫描线 → 白闪切出）
2. 自动恢复上次晨报（导语 + 每条入选理由 + 头版图）
3. **常驻 AI 主编**：右下角「● AI 主编」展开对话条，12 个工具能操作界面的一切
4. 生成晨报：取数计划待批准 → 官方 net 抓 Hacker News + TechMeme → 三视角编辑部背靠背评审 → 主编终审
5. 今日头版：深色 hero 卡片，按当天头条现画横图 + 英文头版标语
6. 阅读页：官方摘要 / AI 解读 / 更多报道 / 讨论 / 原文链接 / AI 配图

详细交接见 **`进度交接_第30轮前.md`**（含本机路径、操作手册、全部坑）。

## 四、红线（splash 语法，踩过就会崩）

这些是**实测踩过的坑**，不遵守会导致卡片直接不渲染或卡死：

- 无 `contains / slice / sort / map / filter`；保留字 `ok / me / scope / self / _` 不可作变量名
- **数字拼串必须先转文本**：`let t = "" + n` 再拼。写 `"0" + n` 会让整段渲染中断
- **渲染循环里不要再遍历同一数据源**：`else for r in show_rows()` 体内再调 `show_rows()`
  会打断外层迭代，列表只出第一行。要编号就用 `for i r in rows` + 纯函数按下标算
- **JSON 缺字段时直接取属性会抛错**（不是返回 nil）：写成 `let v = o["key"]` 再判空
- `View{show_bg: true}` 的底色在 card-host **不渲染**，要用 `RoundedView` / `SolidView`
- `on_render` 子控件每帧重建，改完要显式 `render()`
- `llm.chat` 的 `max_tokens <= 2048`；拼接结果先 `let` 成变量再传参
- 给滚动区加底部内边距要小心：内边距大于视口高度会让内容区塌成 0

## 五、下一步做什么（第 30 轮候选，按优先级）

1. **语音交互层** —— 让主编「听得见、说得出」。
   ⚠️ 调研结论：makepad 里有现成的 `voice_wave.rs` / `window_voice_input.rs`（whisper STT + VAD + kokoro/indextts TTS），
   但 **card-host 没有注册语音服务**，不是卡片里写几行就能接上，**先确认宿主侧能不能开这个口子**。
2. **桌宠形象** —— 现在的主编只是一个胶囊按钮，给它一个常驻小形象。
3. **联网搜索工具** —— 工具层加 `search_web`，让主编能主动查资料回答新闻相关问题。
4. **编辑部记忆 / 预测性晨报** —— 见 `06_创新思路清单.md` 第 1、7 条。
5. **打包提交流程** —— 报名帖要求的最终提交物检查清单。

## 六、贡献流程（怎么提交你的改动）

**任何人都可以参与。** 两类路径：

**A. 你有本仓库写权限**（被加为 collaborator）

```bash
git checkout -b round-30/你的主题      # 分支名：round-<轮次>/<主题>，一个分支只做一轮的事
# ...改代码...
git commit -m "第30轮：做了什么"
git push -u origin round-30/你的主题
# 然后在 GitHub 上开 Pull Request，用仓库自带的模板写清改动
```

**B. 你没有写权限**：先 fork 本仓库，在自己的 fork 上建同样的分支，再向上游开 PR。

**PR 必须写清三件事**（模板已备好，`.github/pull_request_template.md`）：
1. 这轮改了什么、为什么
2. 怎么验证的（跑了什么命令、看了哪张截图）
3. 证据在哪（`my-entry/evidence/xxx.png`）

**维护者对所有 PR 的默认态度是全同意**（小鞠老师会直接批），不用等讨论；只要你的改动：
- 让 `python tools/brace.py` 通过
- 实机跑过并在 `my-entry/evidence/` 留下截图
- 没破坏既有功能（尤其：**联网必须用户明确批准**这条底线不能破）

**改完 `main.splash` 的标准动作**（顺序别乱）：

```
brace.py（语法） → run（实跑） → shot（截图留证）
→ 写 项目复盘/日期_第N轮_主题.md → 更新 进度交接_第N+1轮前.md → git commit → push
```

**改过 bundle 内容还要重新签名**（否则提交官方 hub 会被拒）：

```bash
hub stamp my-entry/morning-brief/bundle
hub sign-manifest my-entry/morning-brief/bundle --key <密钥文件> --key-id gongchuang
hub check my-entry/morning-brief/bundle --publisher-key "gongchuang=<公钥>"
```

> 注意：**本地开发时 manifest 保持未签名**（仓库现状），因为本地 card-host 没有签名验证器，
> 签名版根本起不来。签名只在上传官方 hub 前做。

## 七、设计原则（不能破的产品底线）

- **先授权、再取数**：不批准不联网，取数范围与域名明示。主编自己也不能越过这一步（代码里有硬闸门）
- **不补齐条数**：部分来源失败就只展示成功来源，并列出失败项
- **可核验**：每条新闻都能看到来源、时间、原文链接
- **看得见的过程**：编辑部几个视角、各自用时多少秒，全部摆在明面上

## 八、文档地图

| 文件 | 作用 |
| --- | --- |
| `进度交接_第30轮前.md` | **接手第一份**：本机路径、操作手册、完整坑列表 |
| `项目复盘/` | 每轮进化复盘（大白话，能看懂"这轮到底变好了什么"） |
| `06_创新思路清单.md` | 三档共 16 条大胆方向 + 推荐三选 |
| `02_比赛方案.md` | 参赛策略 |
| `04_项目实操指南.md` | **环境搭建**：从零装好官方运行环境 |
| `README.md` | 项目总览与快速开始 |
