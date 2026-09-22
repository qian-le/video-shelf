# 第 28 讲回归报告：计算机系统安全

## 结果

Luna max 以 agent-assisted 方式逐窗阅读校正字幕和 `quality/source.md` 的 S01–S09，按 `stitcher_system.md` 做 triage → book → audit。新书保留 18 个 A 项、3 个 B 项，8 个 C 类删除类别；21 个 A/B 项全部逐项覆盖，18 个 A 项均有因果审查，47 个关键术语均有首次短释义和正文引文。正文没有重复附录，术语解释只在首次出现处给出。

核心信息链覆盖了：早期无内存保护→病毒入口；CIA→可用性/复杂性攻击；单向函数→摘要、trapdoor→加密/认证/签名；系统 API→访问控制矩阵→UNIX/setuid→ACL/程序沙箱；模糊测试→栈溢出→ROP 与多层防御；时间/缓存/物理侧信道；prompt injection→Agent 最小权限；供应链依赖→安装钩子→下游扩散。哈希低熵可枚举、累计工作量与“更长链”的简化说法、trapdoor 签名的课堂抽象边界均已在正文说明。

## 统一指标

| 指标 | 旧 `before.md` | Luna 新 `book.md` |
|---|---:|---:|
| Markdown 字符数 | 7,372 | 8,991 |
| 阅读单位 | 3,862 | 6,435 |
| 400 单位/分钟估算 | 9.65 分钟 | 16.09 分钟 |
| 300–500 单位/分钟范围 | 7.72–12.87 分钟 | 12.87–21.45 分钟 |
| 视频时长（估算） | 84.20 分钟 | 84.20 分钟 |
| 阅读/视频比例 | 11.47% | 19.11% |
| 400 单位/分钟节省估算 | 88.5% | 80.9% |

指标均由 `src/book_quality.py::metrics` 按同一公式计算：一个汉字或英文/数字词计一个阅读单位，去除 Markdown/URL/HTML；这是估算，不是实测阅读时长。新书仍在视频时长的 15%–30% 软区间内。

## 实际执行与边界

- `python3 src/book_quality.py prepare evals/quality-20260922/BV1qkEX6FEb5`：生成 9 个完整来源窗口。
- `python3 src/book_quality.py check-triage ...`：通过。
- `python3 src/post_process.py 'https://www.bilibili.com/video/BV1qkEX6FEb5/' .../book.md`：生成最终 `book.html`，无截图占位符。
- `python3 src/book_quality.py audit ...`：通过；仅有“原始字幕不可用”和“时长为估算”两项警告。
- `check_ready` 对最终 HTML fingerprint 检查通过；最终 HTML 文件为 31,717 bytes（Python 字符数 18,088）。

本次没有调用外部 LLM provider/API，也没有把脚本启发式结果当作语义分诊；分诊、正文和语义复核由 Luna agent-assisted 实际完成，脚本只校验来源引文、sidecar 完整性、fingerprint 和统一指标。目录只有 `transcript.corrected.txt`，没有原始 `transcript.json`，所以名称、课堂新闻和 xz-utils 等案例未做双源或外部事实核验；没有发布或 commit。
