# 第 05 讲独立内容审查报告

审查对象是第 05 讲《软件工程的来龙去脉》（`BV1Nyeq6qEt8`）。本报告与 pipeline 的生成记录分开，依据校正字幕逐时间段复核旧书和当前新书，判断以命题、限定和因果链为准，不以关键词命中代替语义支持。

## 证据和抽样

第 05 讲当前只有校正字幕 `content-review/lecture05.transcript.corrected.txt`（2,555 个带时间戳行，5,999 秒，SHA-256 见 `baseline.json`）和旧书快照。工作区没有原始 `transcript.txt` 或 `transcript.json`，所以名称与同音词只能按校正字幕标疑，不能宣称完成原始/校正双源核对。新书也明确写了这个限制。

全量抽样池来自 `../sampling.json`（候选源自任务提供的 sample.json 快照），固定 `seed=20260922`；先排除第 05 讲 `BV1Nyeq6qEt8`，再运行 Python `random.Random(20260922).sample(population_without_lecture05, 2)`，可复现结果为：

- `BV1yu9cBCEAb`，第 10 讲《调试 C 标准库》；
- `BV1qkEX6FEb5`，第 28 讲《计算机系统安全》。

完整候选、排除项和结果保存在 pipeline 的 `../sampling.json`；跨讲语义/新手可读性样本在 `cross-lecture.regression.jsonl` 与 `beginner-readability.json`。两讲字幕都已读取，说明了 schema 可处理操作验证、抽象因果、安全边界和证据不足，而不是只对第 05 讲术语有效。

## 旧书基线

字数和阅读时间统一使用 `src/book_quality.py::metrics`：去除 Markdown 标签、链接 URL 和 HTML 标签后，每个汉字或英文/数字词计 1 个阅读单位；阅读时间为 `reading_units / 400`，同时报告 300/500 单位每分钟的范围。这是估算，不是实测。

| 指标 | 旧 book 快照 |
|---|---:|
| Markdown 字符数 | 5,219 |
| 阅读单位 | 2,900 |
| 估算阅读时间（400 units/min） | 7.25 分钟 |
| 300–500 units/min 敏感性范围 | 5.80–9.67 分钟 |
| 视频时长 | 99.98 分钟 |
| 估算阅读占视频 | 7.25% |

本集按 19 个用户指定/直接相关主题族做**语义覆盖基线**：旧书严格覆盖 2/19（10.5%），将 `partial` 按 0.5 计的加权覆盖为 4.5/19（23.7%）。严格项是 DOOM/JSON/低延迟动作 token，以及 Agent 时代软件工程智慧仍在；实体名称、可验证边界、Intent–Spec–Implementation 和 MVP 只有部分覆盖，其余数字人微表情、品位/reward hacking、scaling/data distribution、训练飞轮、学术研究影响、打印扫描抽象、硬件协议探索、Computer Use、App→API 与产业冲击均缺失。逐项状态见 `baseline.json`，不要把这个分数当生产门槛。

旧书保留了 Apollo 容错与瀑布误读的大方向，但没有完整保留以下关键链：

- 低延迟模型 → 数字人微表情 → 实时人感；
- 即时奖励 → reward hacking → 长期质量下降；
- 数据分布/新领域反馈 → 训练飞轮 → 能力台阶；
- 物理设备 → scan/print 抽象 → 设计与实现解耦；
- Computer Use → App/API → 软件产业冲击。

### 19 个主题族同口径对照

新书仍按上面的 19 个主题族判定，但把**正文语义/机制是否覆盖**与**专名拼写、产品归属是否核定**分开。这样 `type c AI`、System One、DOOM 等内容链可以计入召回，同时不把校正字幕里的同音名或用户候选冒充为已核实产品名。`present` 只表示正文保留了主题的命题、限定或因果链，不表示外部事实已独立核验。

| 主题族 | 旧书 | 新书语义/机制 | 新书专名/归属 | 新书证据 |
|---|---:|---:|---|---|
| TypeSafe AI/新闻实体归属 | partial | present | `Jev / TypeSafe` 为用户线索候选；字幕变体 `JEFF`、`JB`、`type c AI` 待核 | §1 新闻实体与 DOOM 关联 |
| System One/快速模型赛道 | partial | present | System One 在校正字幕中明确；相关产品归属未核 | §1 实时决策模型 |
| DOOM、JSON、低延迟动作 token | present | present | — | §1 状态→JSON→动作 token→反馈 |
| 数字人微表情/机器人人感 | absent | present | — | §1 低延迟应用预测 |
| taste/reward hacking | absent | present | — | §2 即时奖励→捷径→长期质量风险 |
| 可验证/不可验证与形式化 gap | partial | present | — | §2 形式规格不等于真实意图 |
| scaling law | absent | present | 已给中文作用释义 | §3 规模—能力关系 |
| 数据分布工程 | absent | present | — | §3 领域、时机、比例与反馈 |
| 新领域训练反馈飞轮 | absent | present | — | §3 新领域→反馈→训练→下一轮探索 |
| 学术研究/论文与工业 RSI 影响 | absent | present | — | §3 AI slop、自动实验闭环与研究模式预测 |
| Intent–Spec–Implementation | partial | present | 三层均有中文作用释义 | §4 三层表格与 gap |
| MVP：小版本→暴露 gap→迭代 | partial | present | 首现有中文释义 | §4、§9 |
| 物理设备接入 | absent | present | 物理设备有中文解释 | §5 打印机、扫描仪、电子墨水屏 |
| 打印/扫描抽象接口 | absent | present | scan/print、PCL 有中文作用释义 | §5 接口与设备解耦 |
| Agent 探索硬件协议和参数 | absent | present | APK、蓝牙、协议以场景解释 | §5 试参、PCL、APK 分析 |
| 快速模型 Computer Use | absent | present | 首现有中文作用释义 | §6 快速决策与屏幕操作条件 |
| App→API/Agent capability | absent | present | API/Agent capability 有中文作用释义 | §6 App 路径与 API 调用区分 |
| 软件产业影响 | absent | present | 预测归因于讲师 | §6 成本、入口与软件公司预测 |
| Agent 时代软件工程智慧仍在 | present | present | — | §12 意图、接口、证据、契约与维护 |

因此，新书**主题语义/机制严格覆盖 19/19（100%）**；旧书的 2/19 严格覆盖、4.5/19 加权覆盖保持为历史基线。专名核定仍是独立风险维度，不拿 44 条黄金样本数与 19 个主题族直接比较。逐项机器可读记录在 `baseline.json` 的 `new_book_topic_scope`。

## 黄金集和新书语义复核

`lecture05.golden.jsonl` 有 44 条样本：A=40、B=3、C=1。每条包含校正字幕的短证据、时间、事实/观点/预测/推测属性、应保留语义、因果链、旧书映射、名称疑义和 A/B/C 处置；C 样本是重复的“他不说人话”，用于检查冗余压缩。最新书独立复核为 43 条 `covered`、0 条 `partial`、1 条 `redundant_ok`，没有发现整条高价值命题完全漏掉。

六项此前 partial 均已修复为语义 covered：书首以字幕支持的 `type c AI` 等待核名称为主，用户 `Jev / TypeSafe AI` 只列候选；Dijkstra 与 *Go To Statement Considered Harmful*、NATO 会议依清晰作品/历史上下文合理订正并作统一说明；QuickCheck、Eiffel、Dafny、Verus 以“字幕疑似对应”标识、机制优先并提供中文作用释义；“斩杀线”虽压缩原词，竞争门槛上移与人类判断仍在因果链中。遗留风险是原始字幕缺失导致的外部专名核验边界，不是正文把候选写成定论。

其余指定链均保留了原因、推理、示例、条件或限制：尤其是 reward hacking 不再只点名，而是写出即时奖励→捷径→长期质量风险；MVP 不再只给定义，而是写出小版本→暴露 gap→迭代；硬件案例同时区分真实人工反馈和接摄像头后的自动化设想；App/API 和“软件公司消亡”保留为预测。

## 新手可读性与冗余

`beginner-readability.json` 把首次实际出现的位置和应有的短中文作用释义分开记录，避免把编者释义误冒为讲师原话。第 05 讲已通过核心术语：Agent、JSON、token、reward hacking、scaling law、Intent/Specification/Implementation、MVP、API、Computer Use、PCL、goto、UML、traceability、contract、The Bitter Lesson、QuickCheck；第 10/28 讲最终书也通过 system call/libc/FFI、CIA、setuid/root、prompt injection 的首现中文作用释义。名称候选提示要保留，避免用百科式重复解释挤占正文。

冗余方面，重复口癖已压缩，AI 进步/“软件消亡”的重复感叹合并为带条件的论点；物理设备打印过程保留了反馈和验收信息，没有逐条复述等待/窗口操作。因此 C 处置符合语义目标，不能用删掉关键例证来换取阅读预算。

## 当前新书读时与执行边界

截至最终稳定快照的 `output/BV1Nyeq6qEt8/book.md`（SHA-256 `fb675c7ca2c070a86588755b2c692c098492408a79d7049f6e818c523eade3b7`），pipeline 公式计算为：7,926 阅读单位、19.82 分钟（15.85–26.42 分钟敏感性范围）、占约 100 分钟视频 19.82%；Markdown 字符数 11,209。指标由 `python src/book_quality.py metrics output/BV1Nyeq6qEt8` 重算，旧基线仍保留在 `baseline.json`。

当前第 05 讲和两讲回归书均已渲染 `book.html`，并通过 `book_quality.py check-triage` 与 `book_quality.py audit` 的结构/证据门禁；本审查没有运行生成模型 API，也没有发布，因此不把文件流程通过描述为模型 API 端到端成功。抽样两讲最终 book 已生成并完成独立正文复核，6/6 回归样本 covered：

| 回归书 | book SHA-256 | 阅读单位 | 400 单位/分钟 | 独立语义结果 |
|---|---|---:|---:|---|
| 第 10 讲 `BV1yu9cBCEAb` | `e12e7f2d765b6b32988696cfa5cb05bf5c57b2fb07fd11a71de41424a6183e79` | 5,281 | 13.20 分钟（10.56–17.60） | L10-001/002/003 全 covered；system call、libc、FFI 首现释义通过；CLI audit passed |
| 第 28 讲 `BV1qkEX6FEb5` | `38c3aa7c951088db0409c7bd27201faacc00a96a379e655bae4c3b1e70a17fca` | 6,435 | 16.09 分钟（12.87–21.45） | L28-001/002/003 全 covered；CIA、setuid/root、prompt injection 首现释义通过；CLI audit passed |

两讲结果详见 `cross-newbook.semantic_review.json`；这是最终书的静态来源/正文独立复核，不等于本审查独立重跑生成模型或发布流程。
