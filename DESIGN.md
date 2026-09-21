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
dump_transcript  →  Agent(stitcher_system.md)  →  capture_frames
       →  post_process  →  make_corrected  →  publish(pages)
```

无字幕：`asr_transcript.py`（faster-whisper）。

## 产物

```text
output/<id>/
  transcript.json
  book.md / book.tagged.md
  book.html          # 暖纸色阅读页
  images/shot_*.png
  transcript.corrected.txt
```
