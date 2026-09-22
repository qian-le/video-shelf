# 第 05 讲内容黄金评测集与独立审查

本目录是对 `BV1Nyeq6qEt8`（《软件工程的来龙去脉》）的独立内容审查，供回归评测使用。它不参与生产提示词或 Python 逻辑，也不把任何一行样本硬编码成生成规则。

## 证据范围

- 旧书快照：`../lecture05.before.md`（源文件为 `../lecture05.before.md`）。
- 可用字幕：`lecture05.transcript.corrected.txt`（与 `output/BV1Nyeq6qEt8/transcript.corrected.txt` 同 SHA），共 2,555 行，时长元数据 5,999 秒。
- 原始字幕：当前仓库快照中不存在第05讲的 `transcript.txt` 或 `transcript.json`；因此本集的 `evidence` 全部是校正字幕的逐字短摘录，不能宣称已经完成原始/校正双源核对。疑似产品名、模型名保留字幕原形并用 `entity_notes` 标记；清晰的作品标题（如 *Go To Statement Considered Harmful*）或课程历史上下文（如 NATO 会议）可以在书中合理订正，但不因此确认用户候选产品归属，必要时在统一说明中交代。

## 如何评测

每条 JSONL 样本同时约束短证据、命题、关系和书籍映射。`evidence` 中用 `/` 连接的片段分别逐字来自同一仓库字幕，分隔符只表示为保持短证据而抽取了多个时间行，不宣称这些片段在字幕中连续相邻。合格的新书可以改写措辞，但必须保住 `target_semantics` 与 `causal_chain`；只出现关键词而没有关系或因果含义，不算支持。若 `claim_type` 含 `opinion`、`prediction` 或 `uncertain_inference`，书中必须归因或保留不确定性，不能把讲师推测改成外部事实。`entity_notes` 中的疑义必须继续可见。

`retain_level` 是人工编辑标签：A=应保留为独立语义单元，B=可与相邻样本合并但不能丢掉关系，C=重复/口头噪声可删。它只描述本集回归期望，不是生产规则。

- `lecture05.golden.jsonl`：重点覆盖前 30–40 分钟，同时补足该讲旧书在后半段的历史链路与事实风险。
- `cross-lecture.regression.jsonl`：从第 10、28 讲校正字幕抽取的通用性样本，检查 schema 能否处理技术事实、操作因果和安全边界，而不是只识别第 05 讲的术语。
- `cross-newbook.semantic_review.json`：第 10、28 讲最终书的独立正文复核，逐条检查上述 6 条因果链和首现术语释义；它与抽样黄金集分开，不能用 schema 通过替代语义检查。
- `baseline.json`：旧 book 的字数、阅读时间、覆盖率和因果链状态；覆盖率按语义支持计算，不按关键词计分。
- `review-report.md`：旧书问题、证据缺口、候选抽样、独立检查方法和待新版复核清单。
