# 第10讲知识保留回归报告

本回归针对《调试 C 标准库》（BV1yu9cBCEAb），以 `before.md` 为旧稿、`book.md` 为新稿。旧新均用 `src/book_quality.py metrics` 同一口径统计：每个汉字或英文/数字词计 1 个阅读单位，按 400 单位/分钟估算，并给出 300–500 单位/分钟敏感性范围。视频时长按校正字幕末条 01:20:52 估算为 80.87 分钟。

| 指标 | 旧稿 before.md | 新稿 book.md |
|---|---:|---:|
| Markdown 字符数 | 9,618 | 8,177 |
| reading_units | 4,252 | 5,281 |
| reading_units / 400 | 10.63 分钟 | 13.20 分钟 |
| 300–500 单位/分钟 | 8.50–14.17 分钟 | 10.56–17.60 分钟 |
| 视频阅读比例（400） | 13.2% | 16.3% |

新稿增加 1,029 个阅读单位，但 Markdown 字符数下降；增加的篇幅用于补回启动栈、变参寄存器布局、setjmp/longjmp 保存责任、vDSO 一致性循环和 malloc 生命周期因果，仍处于 15%–30% 阅读软目标内。旧稿已有的 libc、debug info、vDSO、malloc/free 主线未被删除。

## 覆盖与压缩判断

- canonical triage 共 15 个 A 项、3 个 B 项、3 个 C 类别项；S01–S09 每个完整窗口均已回看。A 保留 libc 分层、调试信息/DWARF、符号表与行号限制、调试应用、CRT 初始栈、printf/变参、寄存器保存、vDSO、分配器机制与生命周期因果；B 压缩 OJ 背景、跨语言 source map/构建安全、分配器作业视角；C 删除口癖、重复操作走场和无信息闲聊。
- `coverage.audit.json` 对 18 个 A/B 项逐项给出正文引文、每条 `must_preserve` 检查、A 项因果检查及观点归属；不是通过关键词出现率推断覆盖。完整 audit 的 `semantic_review.performed=true`，`python src/book_quality.py audit ...` 通过。
- 关键术语按首现紧邻括号给短释义，后续不重复；本次清单登记并核对 47 个 key terms，补齐 GDB、musl、CRT、argc/argv/envp、FFI 等前文首现。freestanding 改为运行环境概念并与额外链接/启动设置区分；flame graph 改为样本聚合宽度，标注讲师现场“时间轴”说法与 flame chart 的边界。

## 实际执行边界

本次由 Luna agent 逐窗阅读校正字幕、生成 triage、重写正文并逐项语义复核；没有调用外部 LLM provider/API，`book_quality.py` 只做来源引文、结构、术语证据、预算和 freshness 检查。`post_process.py` 已在最终 `book.md` 后生成 `book.html`，随后 audit 检查最终 HTML 指纹并通过，`check_ready` 也通过。

本目录只有 corrected transcript，没有 `transcript.json` 原始稿，因此报告标记 corrected-only；视频时长为估算值。freestanding 释义参考 GCC 官方标准说明，flame graph 横轴释义参考 Brendan Gregg 原始说明，仅用于纠正短释义，未把外部材料扩写进课程覆盖。新书和 sidecars 仅写入本回归目录，未替换已发布书、未发布、未 commit。
