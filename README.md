# 书架 Shelf

与 VideoBook **工作流/CLI 对齐** 的自有视频电子书库；代码自研，前端为暖纸色书架风。

## 命令（Python: `.venv\Scripts\python.exe`）

```powershell
cd D:\书架\shelf
.\.venv\Scripts\python.exe src\dump_transcript.py "<url>"
# 先生成/核对带时间戳的修正版字幕，后续来源窗口以它为主
.\.venv\Scripts\python.exe src\make_corrected.py <id>
# 准备完整、带时间窗口的来源材料（不调用模型，不等于完成分诊）
.\.venv\Scripts\python.exe src\book_quality.py prepare output\<id>
# Agent 依据 prompts/stitcher_system.md 和 prompts/knowledge_triage.md
# 审核全部 source chunks，并写 output/<id>/knowledge.triage.json
# Agent 依 transcript + reviewed knowledge.triage.json 写 output/<id>/book.md
.\.venv\Scripts\python.exe src\book_quality.py check-triage output\<id>
.\.venv\Scripts\python.exe src\capture_frames.py <id> "<url>"
.\.venv\Scripts\python.exe src\post_process.py "<url>" output\<id>\book.md
# Agent 按 prompts/coverage_audit.md 写 coverage.audit.json；最终 book.html 存在后再审计
.\.venv\Scripts\python.exe src\book_quality.py audit output\<id>
.\.venv\Scripts\python.exe -m http.server 8080 --bind 127.0.0.1 --directory output
# 可选发布
.\.venv\Scripts\python.exe src\publish.py <id>
```

首次截帧：`src\capture_frames.py --setup-profile`

用户侧：丢一条 B 站链接并说「上架到书架」。

## 内容质量流水线

Shelf 的压缩目标是最大化单位阅读时间获得的有效知识：A 类概念、机制、因果链、讲师判断和高价值案例必须实质保留；B 类压缩保留；C 类口癖、等待和重复表达删除。`book_quality.py prepare` 只准备完整来源窗口；triage 和书籍化仍由 Agent/编辑依据原字幕完成，不假装离线脚本具备语义判断或自动写书能力。最终顺序是 `book.md → capture_frames → post_process(book.html) → coverage.audit.json → book_quality audit → publish`；审计会把 `book.html` 纳入 fingerprint，缺失、过期或缺少语义审查 provenance 时报告 needs review。

阅读时长统一按以下公开估算式计算，结果不是实测：

```text
阅读单位 = 中文字符数 + 英文/数字词数；估算分钟 = 阅读单位 / 400
阅读时长范围 = 阅读单位 / 500 ～ 阅读单位 / 300（仅作敏感性分析）
```
