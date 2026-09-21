"""提取视频字幕 → output/<id>/transcript.json（与原项目 CLI 对齐）。

用法:
    python src/dump_transcript.py "<VIDEO_URL>"
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import CAPTURE_PROFILE, get_video_dir  # noqa: E402

import yt_dlp  # noqa: E402


def extract_video_id(url: str) -> str:
    m = re.search(r"(BV[0-9A-Za-z]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    raise SystemExit(f"无法解析视频 ID: {url}")


def export_cookies() -> str | None:
    if not os.path.isdir(CAPTURE_PROFILE):
        return None
    if not os.listdir(CAPTURE_PROFILE):
        return None
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    tmp = os.path.join(tempfile.gettempdir(), "shelf_cookies.txt")
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                CAPTURE_PROFILE, headless=True, channel="chrome"
            )
            cookies = ctx.cookies()
            ctx.close()
        lines = ["# Netscape HTTP Cookie File"]
        for c in cookies:
            domain = c.get("domain", "")
            flag = "TRUE" if str(domain).startswith(".") else "FALSE"
            secure = "TRUE" if c.get("secure") else "FALSE"
            expires = int(c.get("expires") or 0)
            if expires < 0:
                expires = 0
            lines.append(
                f"{domain}\t{flag}\t{c.get('path', '/')}\t{secure}\t{expires}\t"
                f"{c.get('name', '')}\t{c.get('value', '')}"
            )
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(">> 已从 .capture-profile 导出登录态 cookies（临时文件，用完即删）")
        return tmp
    except Exception as e:
        print(f">> cookies 导出失败: {e}")
        return None


def parse_subtitle_text(raw: str, fmt_name: str | None) -> list[dict]:
    if (fmt_name in ("json3", None) and raw.lstrip().startswith("{")) or fmt_name == "json3":
        data = json.loads(raw)
        segments = []
        for ev in data.get("events") or []:
            segs = ev.get("segs") or []
            text = "".join(s.get("utf8", "") for s in segs).strip()
            if not text or text == "\n":
                continue
            t_ms = ev.get("tStartMs", 0)
            d_ms = ev.get("dDurationMs", 0)
            start, end = t_ms / 1000, (t_ms + d_ms) / 1000
            segments.append(
                {
                    "start": f"{int(start)//3600:02d}:{(int(start)%3600)//60:02d}:{int(start)%60:02d}",
                    "end": f"{int(end)//3600:02d}:{(int(end)%3600)//60:02d}:{int(end)%60:02d}",
                    "text": text.replace("\n", " ").strip(),
                }
            )
        return segments

    time_re = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})"
    )
    segments = []
    for block in re.split(r"\n\s*\n", raw.strip()):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        tm = None
        texts = []
        for ln in lines:
            m = time_re.search(ln)
            if m:
                g = [int(x) for x in m.groups()]
                start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
                end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
                tm = (start, end)
            elif ln.isdigit() or "-->" in ln:
                continue
            else:
                texts.append(ln)
        if tm and texts:
            start, end = tm
            fmt = lambda x: f"{int(x)//3600:02d}:{(int(x)%3600)//60:02d}:{int(x)%60:02d}"  # noqa: E731
            segments.append({"start": fmt(start), "end": fmt(end), "text": " ".join(texts)})
    return segments


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    url = sys.argv[1]
    video_id = extract_video_id(url)
    out_dir = get_video_dir(video_id)

    cookies = export_cookies()
    if not cookies:
        print(">> 未检测到 .capture-profile 登录态，尝试匿名抓取")
        print(">> 若失败请先: python src/capture_frames.py --setup-profile")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["zh-CN", "zh-Hans", "zh", "ai-zh", "en"],
        "subtitlesformat": "srt/vtt/best",
    }
    if cookies:
        ydl_opts["cookiefile"] = cookies

    print(f">> 正在拉取视频元数据与字幕: {video_id}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title") or video_id
        duration = float(info.get("duration") or 0)
        chapters = info.get("chapters") or []
        subs = info.get("subtitles") or {}
        auto = info.get("automatic_captions") or {}

        def pick(*tables):
            for table in tables:
                for key in ("zh-CN", "zh-Hans", "zh", "ai-zh", "en"):
                    if key in table and table[key]:
                        return key, table[key]
                for key, val in table.items():
                    if val:
                        return key, val
            return None

        picked = pick(subs, auto)
        if not picked:
            print("❌ 平台未提供字幕。可改用本地 ASR：python src/asr_transcript.py " + video_id)
            raise SystemExit(2)

        lang, formats = picked
        url_sub = None
        fmt_name = None
        for f in formats:
            ext = (f.get("ext") or "").lower()
            if ext in ("srt", "vtt", "json3", "srv1", "srv2", "srv3"):
                url_sub, fmt_name = f.get("url"), ext
                break
        if not url_sub and formats:
            url_sub, fmt_name = formats[0].get("url"), formats[0].get("ext") or "srt"
        if not url_sub:
            print("❌ 字幕轨道缺少下载 URL")
            raise SystemExit(2)

        print(f">> 字幕轨道: {lang} ({fmt_name})")
        raw = urlopen(Request(url_sub, headers={"User-Agent": "Mozilla/5.0"}), timeout=60)
        raw = raw.read().decode("utf-8", errors="replace")
        segments = parse_subtitle_text(raw, fmt_name)

    if not segments:
        print("❌ 字幕解析为空")
        raise SystemExit(2)

    last_parts = [int(x) for x in segments[-1]["end"].split(":")]
    last_sec = last_parts[0] * 3600 + last_parts[1] * 60 + last_parts[2]
    cover = (last_sec / duration * 100) if duration else 100.0
    print(f">> 字幕覆盖率自检: {cover:.1f}%（{len(segments)} 段 / 时长 {int(duration)}s）")
    if duration and cover < 50:
        print("❌ 覆盖率过低，请检查登录态/代理后重跑")
        raise SystemExit(3)

    chap_out = [
        {
            "start": ch.get("start_time") if isinstance(ch.get("start_time"), str) else None,
            "end": ch.get("end_time") if isinstance(ch.get("end_time"), str) else None,
            "title": ch.get("title") or "",
        }
        for ch in chapters or []
    ]
    # yt-dlp chapters 有时是数字秒
    for ch_in, ch_out in zip(chapters or [], chap_out):
        if ch_out["start"] is None and "start_time" in ch_in:
            try:
                s = int(float(ch_in["start_time"]))
                ch_out["start"] = f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"
            except (TypeError, ValueError):
                ch_out["start"] = ""
        if ch_out["end"] is None and "end_time" in ch_in:
            try:
                s = int(float(ch_in["end_time"]))
                ch_out["end"] = f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"
            except (TypeError, ValueError):
                ch_out["end"] = ""
        ch_out["start"] = ch_out.get("start") or ""
        ch_out["end"] = ch_out.get("end") or ""

    payload = {
        "video_url": url,
        "title": title,
        "video_id": video_id,
        "duration": duration,
        "chapters": chap_out,
        "segments": segments,
    }
    tpath = os.path.join(out_dir, "transcript.json")
    with open(tpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(f"[{s['start']}] {s['text']}" for s in segments))

    print(f"✅ 成功获取视频信息, Video ID: {video_id}")
    print(f"✅ 官方章节 {len(chap_out)} 个已写入")
    print(f"✅ 字幕数据已保存至: {tpath}")
    print("AI Agent，请阅读 transcript.json 并根据 prompts/stitcher_system.md 生成 book.md。")

    if cookies and os.path.exists(cookies):
        try:
            os.remove(cookies)
        except OSError:
            pass


if __name__ == "__main__":
    main()
