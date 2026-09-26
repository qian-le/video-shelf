# Shelf 内容质量报告

本报告记录 `quality/knowledge-retention-20260922` 分支在 2026-09-22 的文件门禁与语义审查结果。书籍正文、triage 和 coverage sidecar 由 Luna agent-assisted 工作流实际读取字幕后生成和审查；本次没有独立的供应商模型 API 调用，也没有用 API 驱动的自动生成测试。没有发布 `pages` 或合并 `master`；`src/book_quality.py` 只负责结构、来源、指标和 freshness 门禁。

## 结果

| 书 | 来源完整性 | triage | semantic audit | 阅读单位 | 400 单位/分钟估算 | 软预算占视频 |
|---|---|---|---|---:|---:|---:|
| 第 05 讲 `BV1Nyeq6qEt8` | corrected-only；原始 `transcript.json` 不在仓库 | pass | pass；43 条 A/B covered，1 条 C `redundant_ok` | 7,926 | 19.82 分钟（15.85–26.42） | 19.82% |
| 第 10 讲 `BV1yu9cBCEAb` | corrected-only；时长按字幕末条估算 | pass | pass | 5,281 | 13.20 分钟（10.56–17.60） | 16.33% |
| 第 28 讲 `BV1qkEX6FEb5` | corrected-only；时长按字幕末条估算 | pass | pass | 6,435 | 16.09 分钟（12.87–21.45） | 19.11% |
| 第 05 讲旧 → 新（同一校正字幕） | corrected-only；旧、新均无原始字幕 | 旧无 canonical triage → 新 pass | 旧 2/19 → 新 19/19 机制覆盖；关键链由缺失变为 covered；1 条重复口语归入 C | 2,900 → 7,926 | 7.25 → 19.82 分钟（5.80–9.67 → 15.85–26.42） | 7.25% → 19.82% |

第 05 讲独立黄金集的 19 个主题族从旧书严格覆盖 2/19 提升为正文机制覆盖 19/19；名称归属仍单独保留不确定性。两讲回归抽样共 6 条语义样本，`cross-newbook.semantic_review.json` 记录为 6/6 `covered`。旧书与新书的同口径比较、逐条字幕证据和时间定位见 `evals/quality-20260922/content-review/review-report.md`、`lecture05.golden.jsonl` 与 `baseline.json`。

## 为什么旧流程会过度压缩

这次回看的是基线文件的真实行为，不能把缺失全部归因于纠错脚本：

1. 基线 `prompts/stitcher_system.md` 要求“去除口语化”和啰嗦重复、翻译成成熟技术文档、按主题切章，但没有 A/B/C 保留清单，也没有要求保留每个重要命题的因果链、讲师观点/预测属性或字幕 source span。Agent 得到的是“压成结构化指南”的明确目标，缺少“哪些知识必须留下”的同等约束。
2. 基线只要求在重要章节或新思路开头“可适当”放时间锚点；章节按“合理主题”切分，未建立逐项主题覆盖表或完整 source sweep。因此跨较长字幕段落的细节、转折和具体链条没有可检查的保留接口。
3. 基线把 Mermaid（流程/条件/架构）和截图占位符（架构、界面、步骤、结果）列为硬性格式要求，却没有配套的知识预算、证据字段或缺项反馈。输出可以满足版式要求，同时遗漏没有显式列出的主题和因果关系。
4. 基线 `instructions.md` 的主流程是 `dump_transcript → Agent 写 book.md → capture_frames → post_process`；当时没有 transcript→triage→coverage audit→针对性修订回路。`post_process.py` 只把 Markdown 渲染为 HTML，不做内容保真检查。

`make_corrected.py` 不是主要压缩源：它逐段保留讲师原词和顺序，只做明确 ASR 词表替换、纯口癖段清理、行尾口癖清理和明显叠词压缩；基线真正缺少的是 Agent 重写后的保留约束与反馈门。当前流程补上 A/B/C、source spans、因果/归属审查、首现术语释义和 HTML freshness gate，旧书 2/19 到新书 19/19 的差异据此可回查。

所有阅读时间使用同一公开估算式：去掉 Markdown 标签、链接 URL 和 HTML 标签后，每个汉字或英文/数字词计一个阅读单位，估算分钟为 `reading_units / 400`；`/500` 到 `/300` 只作敏感性范围，不是实测阅读时间。代码和 Mermaid 标签按可见文本近似计一次，没有额外重复计算代码行。

## 质量门禁

`prepare` 按 600 秒窗口展开完整校正字幕，保留所有 segment，只统计相邻重复候选；跨窗口知识仍由 Agent 按 source spans 聚合。A/B 条目必须有可回查的字幕短引文、保留理由和完整来源回扫；C 只记录删除类别。coverage sidecar 必须逐项提供正文证据、语义 review provenance、A 项因果检查、观点/预测归属检查及关键术语首现释义。

`key_terms` 与 `term_checks` 现在按精确术语集合匹配，重复、空条目、缺项或错误名称都会阻断审计。术语检查记录 `first_use` 和含短中文作用释义的原文证据，缩写不能只展开英文。审计不会从关键词或跨章节拼接自动推出语义覆盖；缺少 `semantic_review.performed=true`、逐项证据或完整 source sweep 时保持 `needs_review`。

最终可发布文件是 `book.html`。审计把 `book.md`、`book.html`、两个 sidecar、字幕和元数据一起写入 fingerprints；缺 HTML、HTML 过期或审计报告过期时，`publish.py` 的 `check_ready` 会拒绝发布。顺序固定为：修正字幕 → prepare → triage → book → 截帧 → render HTML → coverage audit → `book_quality audit` → publish。

## 限制

- 第 05、10、28 讲当前都只有带时间戳的校正字幕；不能声称完成原始字幕与校正字幕的双源核验。第 05 讲用户提供的 `Jev`、`TypeSafe AI` 等名称只作为候选线索，正文保留字幕实际变体和待核说明。
- 书籍正文、triage 和 Agent/editor 语义复核已经实际完成；质量报告表示这些文件的证据和门禁通过，不表示外部新闻、产品归属或讲师机制已经独立事实核验。
- 本次没有供应商模型 API 端到端调用或独立 API 驱动生成测试，也没有执行站点发布；两讲和第 05 讲的 HTML 都是由当前仓库 `post_process.py` 对最终 Markdown 渲染的产物。

## 变更清单

- `src/book_quality.py`：完整来源窗口、A/B/C triage 校验、来源证据、语义审查接口、统一阅读指标、HTML freshness 与发布前 gate。
- `src/publish.py`：发布前调用 `check_ready`，审计未通过或过期时停止。
- `prompts/stitcher_system.md`、`prompts/knowledge_triage.md`、`prompts/coverage_audit.md`：A/B/C 有损压缩、因果/归属、不确定性、零基础首现术语释义和逐项语义审查标准。
- `tests/test_book_quality.py`：9 个测试，覆盖有效审查、空学习内容、缺 provenance、缺 key terms、错误/重复 term checks、缺 HTML、HTML freshness 和指标公式。
- `README.md`、`instructions.md`、`DESIGN.md`：统一 canonical sidecar 路径和 render → audit → publish 顺序。
- `output/BV1Nyeq6qEt8/`：第 05 讲最终 Markdown、HTML、校正字幕、canonical triage/coverage sidecar、source windows 和质量报告。
- `evals/quality-20260922/`：第 05 讲黄金集、独立审查、初始基线、两讲回归书/triage/coverage/HTML/quality report 及跨讲语义复核。

验证命令：`python -m unittest discover -s tests -v`（9/9）；三个视频目录分别运行 `python src/book_quality.py check-triage <dir>` 和 `python src/book_quality.py audit <dir>`，均返回通过并通过 `check_ready`；`python -m py_compile src/book_quality.py src/publish.py` 通过。`git diff --check` 仅报告三本生成 Markdown 引用行用于硬换行的两个行尾空格及生成稿 EOF 空行，代码、prompt、报告和测试没有其它空白问题。
