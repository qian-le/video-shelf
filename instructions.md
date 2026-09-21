# Shelf Agent 工作流指令（与 VideoBook 流水线对齐）

> 本文件是 AI 助手的操作手册。用户发来视频链接时，严格按步骤执行。
> 工作目录：`D:\书架\shelf`
> Python：`D:\书架\shelf\.venv\Scripts\python.exe`

## 触发条件

消息包含 `bilibili.com` / `youtube.com` / `youtu.be` 链接，且用户希望生成电子书/上架书架。

## 完整工作流

### 第一步：提取字幕

```powershell
.\.venv\Scripts\python.exe src\dump_transcript.py "<VIDEO_URL>"
```

- 产物：`output/<video_id>/transcript.json`（含 `duration`、`chapters`、`segments`）
- 登录态：使用 `.capture-profile/`；若无则先
  `.\.venv\Scripts\python.exe src\capture_frames.py --setup-profile`
- 覆盖率低于 50% 会退出码 3，**不得进入第二步**
- 平台无字幕时走 ASR 兜底：

```powershell
.\.venv\Scripts\python.exe src\asr_transcript.py <video_id> --url "<VIDEO_URL>"
# 可选抽样: --sample-start 900 --sample-dur 180
# 全量续跑: --restart
```

### 第二步：阅读字幕 + 生成电子书

1. 阅读 `output/<video_id>/transcript.json`
2. 阅读 `prompts/stitcher_system.md`
3. 重写为结构化 Markdown，写入 `output/<video_id>/book.md`
4. 截图占位必须是：`![场景描述](SCREENSHOT:HH:MM:SS)`
5. 官方 `chapters` 仅作参考，顶层章节按内容逻辑组织
6. 容忍 ASR 同音错词，动笔前建术语表
7. 运行修正版字幕：

```powershell
.\.venv\Scripts\python.exe src\make_corrected.py <video_id>
```

   产出 `transcript.corrected.txt`；必要时由 AI 做行级订正（保留讲师原词）。

### 第三步：截帧

```powershell
.\.venv\Scripts\python.exe src\capture_frames.py <video_id> "<VIDEO_URL>"
# 仅物化: python src\capture_frames.py <video_id> --materialize-only
# 登录一次: python src\capture_frames.py --setup-profile
```

- 产物：`output/<id>/images/shot_HH_MM_SS.png`，并回写 `book.md`
- 保留 `book.tagged.md`（含 SCREENSHOT 占位，供补帧）
- 优先用平台播放器截图，不下载视频源（除非另接 extract 兜底）

### 第四步：渲染 HTML + 本地预览

```powershell
.\.venv\Scripts\python.exe src\post_process.py "<VIDEO_URL>" output\<video_id>\book.md
.\.venv\Scripts\python.exe -m http.server 8080 --bind 127.0.0.1 --directory output
```

- 单本预览：`http://127.0.0.1:8080/<video_id>/book.html`
- 页面样式为本项目「暖纸色书架」风，流水线接口与原项目一致

### 第五步：告知用户

1. Markdown：`output/<video_id>/book.md`
2. HTML：`http://127.0.0.1:8080/<video_id>/book.html`
3. 字幕对照：`output/<video_id>/transcript.corrected.txt`（若已生成）
4. 关闭服务：终端 Ctrl+C

### 第六步（可选）：发布到 pages

```powershell
cd D:\书架\shelf
.\.venv\Scripts\python.exe src\publish.py <video_id>
# 或 --all
git push origin pages
```

- 发布 `book.html` / `book.md` / `images/` /（若有）`transcript.corrected.txt`
- 目录名 = 视频标题；落地页为本项目暖纸书脊卡片风
- 不触碰 `output/` 工作区；内容无变化则跳过提交

## 注意

- 所有命令在 `D:\书架\shelf` 下执行
- 不要修改 `D:\书架\videobook`（参考项目）
- cookies 只写系统临时目录，用完即删
- 流水线幂等：可重跑任一步
