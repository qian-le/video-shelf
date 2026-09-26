# 书架 Shelf — 架构（与 VideoBook 工作流对齐）

## 对齐什么

- 目录：`output/<video_id>/`
- 占位符：`![desc](SCREENSHOT:HH:MM:SS)`
- Chrome：`.capture-profile/`
- 脚本 CLI：`dump_transcript` / `capture_frames` / `post_process` / `make_corrected` / `publish` / `asr_transcript`
- 发布：orphan 分支 `pages` + manifest + 落地页
- Agent SOP：六步（字幕→写书→截帧→渲染→告知→发布）

## 不照搬什么

- 代码均为本目录自研重构
- **前端视觉**：暖纸色 `#f4efe6` + 青绿 `#0f766e` + 书脊卡片，而非原项目蓝紫渐变风

## 流水线

```text
dump_transcript → make_corrected → book_quality prepare(source windows)
       → Agent/editor knowledge.triage.json
       → Agent(stitcher_system.md) → book.md → capture_frames
       → post_process(book.html) → Agent/editor coverage.audit.json
       → book_quality audit → publish(pages)
```

`book_quality.py prepare` 只展开完整字幕来源窗口；它不调用模型。知识价值判断和书籍化由 Agent/编辑完成，必须保存 `knowledge.triage.json` 与 `coverage.audit.json`。最终质量顺序是渲染 `book.html` 后再审计；审计将 HTML 与 Markdown、sidecar 一起 fingerprint，不能让旧 HTML 搭配新正文通过。`book_quality.py audit` 只做证据、完整性、阅读预算和审查 provenance 的结构校验，不能自动证明语义覆盖；缺少逐项 Agent/编辑语义审查时保持 needs review，不能静默发布。

无字幕：`asr_transcript.py`（faster-whisper）。

## 产物

```text
output/<id>/
  transcript.json
  quality/source.json               # 完整来源窗口元数据
  quality/source.md                 # 带时间定位的来源材料
  knowledge.triage.json             # Agent/editor reviewed triage
  book.md / book.tagged.md
  book.html          # 暖纸色阅读页
  coverage.audit.json               # Agent/editor semantic review
  quality/report.json               # 结构审计结果
  images/shot_*.png
  transcript.corrected.txt
```
