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

### 第二步：知识分诊 + 生成电子书

1. 阅读 `output/<video_id>/transcript.json` 和 `prompts/stitcher_system.md`
2. 先运行修正版字幕，之后所有来源窗口、分诊和书籍化都以它为主，并保留讲师原词：

   ```powershell
   .\.venv\Scripts\python.exe src\make_corrected.py <video_id>
   ```

   必要时由 AI 做行级订正；不确定的词保留疑点，不补造原话。

3. 准备完整的来源窗口（脚本不调用模型，也不把启发式结果当作分诊）：

   ```powershell
   .\.venv\Scripts\python.exe src\book_quality.py prepare output\<video_id>
   ```

   `quality/source.md` 展开完整字幕窗口并保留时间上下文。Agent/编辑必须逐窗阅读、聚合跨窗知识，形成 `knowledge.triage.json`：每个 A/B 单元有真实 source span 和保留理由；C 类只汇总删除类别，不把口癖做成完整垃圾清单；A 项的 `key_terms` 只列确实需要首现释义的术语。

4. 检查 triage 是否覆盖所有来源窗口：

   ```powershell
   .\.venv\Scripts\python.exe src\book_quality.py check-triage output\<video_id>
   ```

5. 阅读 `transcript.json`、`transcript.corrected.txt`、`quality/source.md` 和 reviewed `knowledge.triage.json`，依照 Prompt 重写结构化 Markdown，写入 `output/<video_id>/book.md`。
6. 截图占位必须是：`![场景描述](SCREENSHOT:HH:MM:SS)`
7. 官方 `chapters` 仅作参考，顶层章节按内容逻辑组织；不要按视频分钟数固定分配篇幅。
8. 容忍 ASR 同音错词，动笔前建术语表；不确定的专名保留原文并标注待核实。

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

### 第五步：最终质量审计

在最终 `book.md`、截图和 `book.html` 都完成后，按 `prompts/coverage_audit.md` 完成人工/Agent 逐项覆盖审查，写 `coverage.audit.json`，再运行：

```powershell
.\.venv\Scripts\python.exe src\book_quality.py audit output\<video_id>
```

审计会把 `book.html` 纳入 fingerprint；缺少语义审查 provenance、A 项引文/checks、因果/归属判断或关键术语首现释义时必须阻断。阅读时长是统一公式的估算，不是实测。

### 第六步：告知用户

1. Markdown：`output/<video_id>/book.md`
2. HTML：`http://127.0.0.1:8080/<video_id>/book.html`
3. 字幕对照：`output/<video_id>/transcript.corrected.txt`（若已生成）
4. 关闭服务：终端 Ctrl+C

### 第七步（可选）：发布到 pages

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
