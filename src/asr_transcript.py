"""平台无字幕时的本地 ASR 兜底 → output/<id>/transcript.json。

用法:
  python src/asr_transcript.py <video_id> [--url URL]
  python src/asr_transcript.py <video_id> --sample-start 900 --sample-dur 180
  python src/asr_transcript.py <video_id> --restart
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from src.config import CAPTURE_PROFILE, get_video_dir  # noqa: E402


def _sys_python():
    return sys.executable


def download_audio(video_id: str, url: str) -> str:
    out_dir = get_video_dir(video_id)
    audio = os.path.join(out_dir, "audio.m4a")
    if os.path.isfile(audio) and os.path.getsize(audio) > 10000:
        print(f">> 已有音频 {audio}")
        return audio
    if not url:
        # 尝试从已有 transcript/meta 推断
        for name in ("transcript.json",):
            p = os.path.join(out_dir, name)
            if os.path.isfile(p):
                try:
                    url = json.load(open(p, encoding="utf-8")).get("video_url") or ""
                except (OSError, json.JSONDecodeError):
                    url = ""
    if not url:
        if video_id.startswith("BV"):
            url = f"https://www.bilibili.com/video/{video_id}/"
        else:
            raise SystemExit("请提供 --url")

    cookiefile = None
    # 简易：若 playwright 可用则从 profile 导出
    if os.path.isdir(CAPTURE_PROFILE) and os.listdir(CAPTURE_PROFILE):
        try:
            from playwright.sync_api import sync_playwright
            import tempfile

            tmp = os.path.join(tempfile.gettempdir(), "shelf_asr_cookies.txt")
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
                exp = int(c.get("expires") or 0)
                if exp < 0:
                    exp = 0
                lines.append(
                    f"{domain}\t{flag}\t{c.get('path','/')}\t{secure}\t{exp}\t"
                    f"{c.get('name','')}\t{c.get('value','')}"
                )
            open(tmp, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            cookiefile = tmp
        except Exception as e:
            print(f">> cookie 导出失败: {e}")

    cmd = [
        _sys_python(),
        "-m",
        "yt_dlp",
        "-f",
        "bestaudio/best",
        "-o",
        audio,
        "--no-playlist",
        url,
    ]
    if cookiefile:
        cmd[1:1] = []
        cmd = [_sys_python(), "-m", "yt_dlp", "--cookiefile", cookiefile, "-f", "bestaudio/best", "-o", audio, "--no-playlist", url]
    print(f">> 下载音频: {url}")
    subprocess.run(cmd, check=True)
    return audio


def fmt_ts(seconds: float) -> str:
    s = int(seconds)
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"


def transcribe(video_id: str, audio: str, sample_start=None, sample_dur=None, restart=False):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("未安装 faster-whisper，请: pip install faster-whisper")

    out_dir = get_video_dir(video_id)
    progress = os.path.join(out_dir, "_asr_progress.jsonl")
    prompt_file = os.path.join(out_dir, "_asr_prompt.txt")
    initial_prompt = None
    if os.path.isfile(prompt_file):
        initial_prompt = open(prompt_file, encoding="utf-8").read()[:220]

    done_from = 0.0
    segments = []
    if os.path.isfile(progress) and not restart and sample_start is None:
        with open(progress, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    segments.append(obj)
                    done_from = float(obj.get("end") or 0)
                except json.JSONDecodeError:
                    continue
        print(f">> 断点续跑，已有 {len(segments)} 段，从 {done_from:.0f}s 继续")

    print(">> 加载 faster-whisper ...")
    try:
        model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
    except Exception:
        model = WhisperModel("large-v3", device="cpu", compute_type="int8")

    kwargs = {"language": "zh", "initial_prompt": initial_prompt}
    if sample_start is not None:
        kwargs["clip_timestamps"] = [float(sample_start)]
        if sample_dur:
            # faster-whisper 支持 clip_timestamps 区间
            kwargs["clip_timestamps"] = [float(sample_start), float(sample_start) + float(sample_dur)]
    print(">> 开始转写 ...")
    seg_iter, info = model.transcribe(audio, **kwargs)

    with open(progress, "a", encoding="utf-8") as pf:
        for seg in seg_iter:
            if seg.end <= done_from:
                continue
            text = (seg.text or "").strip()
            if not text:
                continue
            item = {
                "start": fmt_ts(seg.start),
                "end": fmt_ts(seg.end),
                "text": text,
            }
            segments.append(item)
            pf.write(json.dumps(item, ensure_ascii=False) + "\n")
            pf.flush()
            print(f"  [{item['start']}] {text[:40]}")

    # 排序去重
    segments.sort(key=lambda s: s["start"])
    duration = 0.0
    if segments:
        parts = [int(x) for x in segments[-1]["end"].split(":")]
        duration = parts[0] * 3600 + parts[1] * 60 + parts[2]

    # 若 meta/url 已有则补全
    url = ""
    title = video_id
    meta_candidates = [
        os.path.join(out_dir, "transcript.json"),
    ]
    old = {}
    if os.path.isfile(meta_candidates[0]):
        try:
            old = json.load(open(meta_candidates[0], encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            old = {}
    url = old.get("video_url") or (
        f"https://www.bilibili.com/video/{video_id}/" if video_id.startswith("BV") else ""
    )
    title = old.get("title") or video_id
    chapters = old.get("chapters") or []

    payload = {
        "video_url": url,
        "title": title,
        "video_id": video_id,
        "duration": duration,
        "chapters": chapters,
        "segments": segments,
        "source": "asr-faster-whisper",
    }
    tpath = os.path.join(out_dir, "transcript.json")
    json.dump(payload, open(tpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(os.path.join(out_dir, "transcript.txt"), "w", encoding="utf-8").write(
        "\n".join(f"[{s['start']}] {s['text']}" for s in segments)
    )
    print(f"✅ ASR 完成: {len(segments)} 段 → {tpath}")
    if sample_start is not None:
        print(">> 抽样完成；全量请加 --restart 重跑")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--url", default=None)
    ap.add_argument("--sample-start", type=float, default=None)
    ap.add_argument("--sample-dur", type=float, default=None)
    ap.add_argument("--restart", action="store_true")
    args = ap.parse_args()
    audio = download_audio(args.video_id, args.url)
    transcribe(
        args.video_id,
        audio,
        sample_start=args.sample_start,
        sample_dur=args.sample_dur,
        restart=args.restart,
    )


if __name__ == "__main__":
    main()
