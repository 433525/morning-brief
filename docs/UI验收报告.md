# 晨报卡 UI 本地验收

2026-10-02：实际 Splash 界面已完成两轮改造和复核修复，保留 OctoSense、新闻来源、生图入口、15 个主编工具及取数授权流程。UI提交`a9a1008`已依用户授权推送到[个人fork分支](https://github.com/433525/morning-brief/tree/round-31/ui-upgrade)，尚未合并或上线。当前续作窗口约10:02–18:02，按有依据的改进继续检查。

## 改动与证据

| 检查维度 | 本轮处理 | 验证方式 |
| --- | --- | --- |
| 排版 | IBM Plex Sans 与 Noto Sans SC 配对；统一正文、标题和状态文字；完整新闻标题可滚动阅读 | 实际宿主截图，中文和英文长标题 fixture |
| 留白 | 去除 Label 默认重复内边距；连续关注任务区，减少同等权重的大卡片；阅读宽度限制为 760px | 320、412、768、1280px 视口 |
| 视觉层级 | 静态晨光刊头；按真实顺序区分首条与后续条目；计划页独立滚动；三编辑显示独立状态；阅读标题不重复 | 首页、计划、编辑过程、列表、阅读与主编截图 |
| 色彩 | 墨蓝 `#17283b`、冷白 `#f3f6fa`、莓红 `#b72857`、琥珀；降低次要信息的视觉权重 | 原生截图；明确悬停、按下和焦点色 |
| 动效 | 保留破晓开场；移除强白闪；可跳过和保存关闭偏好；改为有限计时 | 两帧不同的开场截图、自动结束、`animating=false` 日志 |
| 微交互 | 主题勾选及四态反馈、条数调节、回车提交、焦点边框、真实状态短标签；非空对话隐藏快捷建议 | 原生交互脚本；模拟双语音/忙碌/非空消息布局 |
| 响应式 | 主题和语音控件可换行；主编独立占用布局；长标题不再挤掉正文；换新闻重置阅读位置 | 窄屏真实滚动后切下一条，控件矩形和截图 |
| 原创性 | 围绕“破晓编辑部”组织信息，沿用用户的企鹅女孩素材与晨光标记；获奖作品用于层级与完成度校准 | 与基线及官方获奖作品公开截图对照 |

## 已复现并修复的问题

- 320px 基线主题按钮横向裁切；新主题行可换行。
- 首页滚动到生成按钮后，授权页沿用旧偏移；授权改为独立滚动区域。
- 长标题和来源挤占阅读正文；完整标题进入阅读滚动区，固定栏保留返回与前后条。
- `ReaderBody` 初始化访问嵌套字段导致渲染错误；改为创建新滚动区后通过已有 UI 绑定同步内容，并检查日志。
- 非空对话 `on_render` 恢复声明中的隐藏状态；移除冲突的隐藏声明，只在有消息时重渲染。
- 底栏状态裁字、语音入口挤压；缩短状态，将语音操作留在展开面板。
- 选中态和键盘焦点继承不一致；补齐状态色和可见焦点边框。
- 开场隐藏后仍持续请求动画帧；采用可停止计时，空闲动画泵关闭。
- 首轮320px准备按钮未进入首屏；紧凑刊头、短占位文案与连续任务区后，首屏断言通过。
- 编辑汇总将失败结果也称为“意见”；改为返回结果数，角色行分别说明成功、失败和等待。
- 首条标签挤掉小屏时间；元信息允许两行，时间统一为中文，带缩略图条目也在实际宿主检查。

## 如何查看

- 图像证据：`my-entry/evidence/ui-upgrade/`，每个尺寸独立目录；PNG 旁的 JSON 是同一状态的实际控件矩形。
- 审阅页：`design/ui-review.html`。
- 本机启动：`powershell -ExecutionPolicy Bypass -File tools/run.ps1`。
- 截图：`powershell -ExecutionPolicy Bypass -File tools/shot.ps1 -Name ui-review.png`。
- 停止：`powershell -ExecutionPolicy Bypass -File tools/stop.ps1`。

测试命令：`python tools/ui_smoke.py`；另可指定 `--width 320 --height 568`、`--first-fold`、`--news`、`--stress-ui`、`--judging-ui`、`--motion`。`--news`、`--stress-ui` 和 `--judging-ui` 创建独立测试副本与状态，有可见模拟标记，不调用实际模型、语音或新闻源。普通测试检查授权、修改偏好与拒绝路径，不批准新闻请求。新闻副本包含中文/英文长标题和本地素材缩略图，检查实际滚动与换条归位。

## 验证边界

当前 stock 宿主没有原项目的语音补丁，也没有配置可用 AI。真实新闻生成、模型选稿、生图、语音收发未在本轮宣称通过；界面保留这些入口及降级说明。企鹅女孩使用已有粉围巾素材，默认皮肤仍可由用户决定。键盘焦点已明确设置样式，完整键盘导航与屏幕阅读器仍需单独验证。

后续复查已实测输入框Return进入授权计划及意图保留；隔离宿主静置120秒持续响应，无渲染/回调错误，未批准新闻请求。四组核心文字色对的对比度为14.97、4.75、6.08、13.14；未据此宣称全界面可访问性合规。

Bundle 维持未签名，遵守官方 8 MiB 限制；字体为 GB2312 常用字及界面文字子集，罕见字与 emoji 使用宿主字体回退。字体来源和 OFL 许可保留；许可网址以纯文本域名表示，避免 Hub 将许可说明误判为外部资源请求。

## 参考来源

- [Bolt 2025 官方获奖名单](https://bolt.new/blog/2025-bolt-hackathon-winners)：实际查看 Tailored Labs、Weight Coach、KeyHaven 的官方公开界面截图，提取主操作、信息层级和强调色的使用原则。
- [Supabase LW13 官方获奖公告](https://supabase.com/blog/lw13-hackathon-winners)：确认视觉奖类别与 Munchwise 获奖事实；未取得其可用现场截图，未将其当作视觉对照证据。
- [Awwwards 官方《Hot Right Now 2023》](https://assets.awwwards.com/awards/gallery/2023/07/HOT-RIGHT-NOW-BOOK-2023.pdf)：实际查看p29 Humana（页内注明Site of the Day）、p115 Neutra VDL和p117 Niccolò Miranda。后两者是书中案例，不据此推定具体奖项。
- [Webby 2025 Bézier](https://winners.webbyawards.com/2025/websites-and-mobile-sites/features-design/best-visual-design-function/324140/bzier)与[FWA25 官方策展评价](https://thefwa.com/FWA25/RobFWA.html)：参考功能与视觉一致、有目的的交互；未成功加载的现场不作视觉结论。
- [官方 Splash API](https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/SCRIPT-API.md)、本地锁定 Makepad 源码及真实 card-host，作为实现与验证依据。

第二轮设计判断、参考边界和逐项修复见 [UI第二轮设计记录](UI第二轮设计记录.md)。获奖作品用于品质校准，当前结果仍需用户实际审阅，不宣称取得任何奖项或评委认可。
