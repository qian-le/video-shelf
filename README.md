# 书架 Shelf

与 VideoBook **工作流/CLI 对齐** 的自有视频电子书库；代码自研，前端为暖纸色书架风。

## 命令（Python: `.venv\Scripts\python.exe`）

```powershell
cd D:\书架\shelf
.\.venv\Scripts\python.exe src\dump_transcript.py "<url>"
# Agent 依 prompts/stitcher_system.md 写 output/<id>/book.md
.\.venv\Scripts\python.exe src\make_corrected.py <id>
.\.venv\Scripts\python.exe src\capture_frames.py <id> "<url>"
.\.venv\Scripts\python.exe src\post_process.py "<url>" output\<id>\book.md
.\.venv\Scripts\python.exe -m http.server 8080 --bind 127.0.0.1 --directory output
# 可选发布
.\.venv\Scripts\python.exe src\publish.py <id>
```

首次截帧：`src\capture_frames.py --setup-profile`

用户侧：丢一条 B 站链接并说「上架到书架」。
