# 术语核对记录（BV144nc6KEA4）

来源：B 站 `ai-zh` 字幕（自动生成），已生成 `transcript.corrected.txt`。
核对方式：结合上下文检索官方文档 / 项目仓库 / 新闻；**未做音画核验**，仅确认实体身份。

| 时间 | 原转写 | 校正/候选 | 依据 | 状态 |
|------|--------|-----------|------|------|
| 全篇 | DPC卡点 / depc harness / deep c harness / deep seek harness / DSH / DEPY harness | **DeepSeek Harness（dsh）** | 视频标题即 DeepSeek Harness；官方架构文档 https://deepseekharness.online/en/guide/architecture ；仓库 github.com/deepseek-ai/deepseek-harness | 已确认 |
| 00:40–01:25 | CORIS / CORDIS / cortex / CODICE / cos | **Cordis** | 官方文档：DeepSeek Harness 构建在 Cordis 插件系统之上，负责插件加载/卸载与依赖；仓库内 vendor/cordis，发布为 @deepseek-ai/cordis | 已确认 |
| 00:00 | ANTHROPIC说 get it 不够用 | **Git** | 上下文为版本控制/仓库讨论；按“Git 不够用”理解。属讲师转述，未查到同日原文 | 语境校正 |
| 00:21–00:22 | GROWBOT / grab bot / gal boss / GROWBOAT / GROUBT / grab board | **GrokBot** | 2026-08 xAI（与 Cursor 合作）推出的多智能体“AI 同事团队”产品：可拉群、Bot 间互发消息、共享上下文、按 routine 定时工作；与本段描述一致 | 已确认 |
| 00:23 | cloud 导弹MD / cloud dot m d | **CLAUDE.md** | 多 agent 工具共用的项目说明文件；上下文为“同时支持多种 agent 时要用它们都理解的方式组织项目文件” | 已确认 |
| 00:28 | 菲律宾是最好的编程语言 | **PHP 是最好的编程语言** | 网络老梗 LAMP/PHP；同段出现 “LINUXAPARTYMICOPHP”，即 Linux + Apache + MySQL + PHP | 已确认（同音误转） |
| 00:29 | LINUXAPARTYMICOPHP | **LAMP（Linux + Apache + MySQL + PHP）** | 同上 | 已确认 |
| 00:33 | jeff in和SJ 发了一篇文章…叫map reduce | **Jeff Dean 与 Sanjay Ghemawat，MapReduce（2004）** | OSDI 2004《MapReduce: Simplified Data Processing on Large Clusters》 | 已确认 |
| 01:00 | 梁文峰 / 梁文谷 | **梁文锋** | DeepSeek 创始人通用写法 | 已确认 |
| 01:07 | super rap / SUWAP / SUPREP / SUFP / super b / super app | **SuperApp（超级应用）** | 上下文指 WPS / Excel / Blender 这类宿主大应用，通过 bridge 接入 agent；原词读音同 “super app”。**未能定位到同名产品**，正文按“超级应用”理解并保留英文 | 存疑（保留） |
| 01:11 | excelly door / ex calida / EXEXCITOR | **Excalidraw** | 手绘风格白板/画布，可嵌网页；与“拖框、画 turtle、对象锁定”演示一致 | 已确认 |
| 00:57 | better side8 / better side bar | **Better Sidebar（插件名）** | 上下文为社区插件把侧边栏做成 VS Code 式布局 | 已确认 |
| 00:16 | work body / cold body | **WorkBuddy / CodeBuddy** | 讲师称两者共享同一 agent 层编排架构 | 已确认 |
| 00:16 | GB t office | 未定 | 上下文为“网上那些用其他模型做 3D 建模的”，无法确认具体产品 | 未解决，正文不点名 |
| 01:11 | KIMI Work k8 | **Kimi（等 AI 做 PPT 产品）** | 上下文为“让 AI 做 PPT 后产品团队自己再做编辑器”；后半段产品名无法确认 | 部分存疑，正文只提 Kimi |
| 00:15 | work body | **WorkBuddy** | 同上 | 已确认 |
| 01:14 | DSH打NMUI的一个DF | **带 `dsh-ui` 标记的 div** | 上下文为“约定一个标记，模型输出里出现就以卡片渲染”。标记名未能从官方文档确认 | 存疑，正文标注 |

未决问题：
- `SuperApp` 是否为某具体开源项目名，未查到。
- 动态 UI 的标记约定（`dsh-ui`）为按读音复原，正文已注明为“讲师演示里的约定”。
- 讲师称 Cordis“先发了一篇论文”，可对应 arXiv 2608.25512《A Programming Paradigm for Spatiotemporal Composability》（DeepSeek-AI 与北大）。正文按讲师原意表述为“先有一篇关于 Cordis 的论文”，不替代讲师说法。
