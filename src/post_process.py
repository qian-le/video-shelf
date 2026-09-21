"""将 book.md 转为 book.html。

CLI 与原项目对齐；页面视觉使用本项目「暖纸色书架」风格（非照搬原 CSS）。

用法:
    python src/post_process.py "<VIDEO_URL>" output/<video_id>/book.md
"""
from __future__ import annotations

import argparse
import os
import re
import urllib.parse as urlparse

import markdown

# ── 平台 ──────────────────────────────────────────


def detect_platform(video_url: str) -> str:
    if "youtube.com" in video_url or "youtu.be" in video_url:
        return "youtube"
    if "bilibili.com" in video_url:
        return "bilibili"
    return "unknown"


def extract_youtube_id(url: str):
    parsed = urlparse.urlparse(url)
    if "youtube.com" in parsed.netloc:
        return urlparse.parse_qs(parsed.query).get("v", [None])[0]
    if "youtu.be" in parsed.netloc:
        return parsed.path[1:]
    return None


def extract_bilibili_bvid(url: str):
    m = re.search(r"(BV[a-zA-Z0-9]+)", url)
    return m.group(1) if m else None


def timestamp_to_seconds(ts: str) -> int:
    ts = ts.split(".")[0]
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0


def make_video_card(platform, video_id, video_url, timestamp, description, image_rel=None) -> str:
    seconds = timestamp_to_seconds(timestamp)
    desc = (description or "").replace('"', "'")

    if image_rel:
        open_url = video_url
        if platform == "bilibili":
            open_url = f"{video_url.split('?')[0]}?t={seconds}"
        elif platform == "youtube":
            open_url = f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"
        return (
            f'<div class="video-card screenshot-card">'
            f'<img src="{image_rel}" alt="{desc}" loading="lazy">'
            f'<p class="video-caption">📷 {desc}<br>'
            f'<a href="{open_url}" target="_blank" rel="noopener">在源站打开 ({timestamp})</a>'
            f"</p></div>"
        )

    if platform == "youtube":
        embed = (
            f"https://www.youtube-nocookie.com/embed/{video_id}"
            f"?start={seconds}&rel=0&modestbranding=1&playsinline=1"
        )
        open_url = f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"
        return (
            f'<div class="video-card">'
            f'<div class="video-wrapper"><iframe src="{embed}" frameborder="0" allowfullscreen loading="lazy"></iframe></div>'
            f'<p class="video-caption">▶ {desc}<br>'
            f'<a href="{open_url}" target="_blank" rel="noopener">在 YouTube 中打开 ({timestamp})</a></p></div>'
        )

    if platform == "bilibili":
        embed = (
            f"https://player.bilibili.com/player.html?bvid={video_id}"
            f"&t={seconds}&autoplay=0&high_quality=1&danmaku=0"
        )
        open_url = f"{video_url.split('?')[0]}?t={seconds}"
        return (
            f'<div class="video-card">'
            f'<div class="video-wrapper"><iframe src="{embed}" frameborder="0" allowfullscreen scrolling="no" loading="lazy"></iframe></div>'
            f'<p class="video-caption">▶ {desc}<br>'
            f'<a href="{open_url}" target="_blank" rel="noopener">在 B 站中打开 ({timestamp})</a></p></div>'
        )

    return (
        f'<div class="video-card fallback"><p>⚠️ 视频参考：{desc}（{timestamp}）— '
        f'<a href="{video_url}" target="_blank">{video_url}</a></p></div>'
    )


SCREENSHOT_PATTERN = (
    r"!\[([^\]]*)\]\("
    r"(?:SCREENSHOT:(\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
    r"|(?:images/)?shot_(\d{2})_(\d{2})_(\d{2})\.png"
    r")\)"
)


def replace_screenshots(md_content: str, video_url: str, images_dir: str | None = None) -> str:
    platform = detect_platform(video_url)
    video_id = None
    if platform == "youtube":
        video_id = extract_youtube_id(video_url)
    elif platform == "bilibili":
        video_id = extract_bilibili_bvid(video_url)

    def replacer(match: re.Match) -> str:
        desc = match.group(1)
        if match.group(2):
            ts = match.group(2).split(".")[0]
        else:
            ts = ":".join(match.group(i) for i in (3, 4, 5))
        image_rel = None
        if images_dir:
            fname = "shot_" + ts.replace(":", "_") + ".png"
            if os.path.exists(os.path.join(images_dir, fname)):
                image_rel = "images/" + fname
        return make_video_card(platform, video_id, video_url, ts, desc, image_rel)

    return re.sub(SCREENSHOT_PATTERN, replacer, md_content)


def process_markdown(video_url: str, md_file: str) -> None:
    if not os.path.exists(md_file):
        print(f"[ERR] 找不到文件: {md_file}")
        raise SystemExit(1)

    with open(md_file, encoding="utf-8") as f:
        content = f.read()

    title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "电子书"

    count = len(re.findall(SCREENSHOT_PATTERN, content))
    print(">> 正在将截图占位符替换为视频/截图卡片...")
    if count > 0:
        content = replace_screenshots(
            content,
            video_url,
            images_dir=os.path.join(os.path.dirname(os.path.abspath(md_file)), "images"),
        )
        print(f">> 已替换 {count} 处截图为卡片")
    else:
        print(">> 未发现截图占位符")

    print(">> 正在生成 HTML 电子书...")
    body_html = markdown.markdown(
        content,
        extensions=["tables", "fenced_code", "toc"],
    )
    page = HTML_TEMPLATE.replace("{title}", title).replace("{content}", body_html)
    html_file = md_file[:-3] + ".html" if md_file.endswith(".md") else md_file + ".html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"\n[OK] 电子书已生成: {html_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="将 book.md 转换为 book.html 电子书")
    parser.add_argument("video_url")
    parser.add_argument("md_file")
    args = parser.parse_args()
    process_markdown(args.video_url, args.md_file)


# ── 本项目视觉：暖纸色 + 青绿强调（自有设计，不照搬原项目） ──

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  color-scheme: light;
  --paper: #f4efe6;
  --card: #fffdf8;
  --ink: #1c1917;
  --muted: #78716c;
  --accent: #0f766e;
  --warm: #b45309;
  --line: #e7e0d4;
  --code-bg: #efe8db;
  --radius: 12px;
  --shadow: 0 8px 24px rgba(28, 25, 23, 0.06);
}
html { scroll-behavior: smooth; }
body {
  font-family: "Noto Serif SC", "Songti SC", Georgia, serif;
  background: var(--paper);
  color: var(--ink);
  line-height: 1.85;
  font-size: 16.5px;
  -webkit-font-smoothing: antialiased;
}
.book-content { max-width: 760px; margin: 0 auto; padding: 48px 24px 120px; }
h1 {
  font-size: 2.05em; font-weight: 700; margin: 8px 0 18px;
  letter-spacing: .02em; color: var(--ink); line-height: 1.35;
}
h1::after {
  content: ""; display: block; width: 48px; height: 3px;
  margin-top: 12px; border-radius: 2px;
  background: linear-gradient(90deg, var(--accent), var(--warm));
}
h2 {
  font-size: 1.4em; font-weight: 650; margin: 48px 0 14px;
  padding-bottom: 8px; border-bottom: 2px solid var(--line); color: var(--ink);
}
h3 { font-size: 1.12em; margin: 28px 0 10px; color: var(--accent); }
p { margin: 0 0 14px; }
strong { color: #0c0a09; font-weight: 650; }
em { color: var(--muted); font-style: italic; }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid transparent; transition: border-color .15s; }
a:hover { border-bottom-color: var(--accent); }
blockquote {
  margin: 20px 0; padding: 16px 20px; background: var(--card);
  border-left: 3px solid var(--accent); border-radius: 0 var(--radius) var(--radius) 0;
  color: #44403c;
}
.book-content > blockquote:first-of-type {
  border-left-color: var(--warm);
  box-shadow: var(--shadow);
  margin-bottom: 28px;
}
blockquote p { margin: 0; }
ul, ol { margin: 12px 0 18px 24px; }
li { margin: 5px 0; }
hr { border: none; height: 1px; background: var(--line); margin: 40px 0; }
table {
  width: 100%; border-collapse: separate; border-spacing: 0;
  margin: 20px 0; border-radius: var(--radius); overflow: hidden;
  border: 1px solid var(--line); background: var(--card); box-shadow: var(--shadow);
}
thead { background: #ebe4d6; }
th {
  padding: 11px 14px; text-align: left; color: var(--accent);
  font-family: system-ui, sans-serif; font-size: .88em; letter-spacing: .04em;
}
td { padding: 11px 14px; border-top: 1px solid var(--line); }
tbody tr { background: var(--card); transition: background .15s; }
tbody tr:hover { background: #f7f1e6; }
code {
  font-family: "JetBrains Mono", Consolas, monospace;
  background: var(--code-bg); padding: 2px 7px; border-radius: 5px;
  font-size: .88em; color: #9a3412;
}
pre {
  margin: 18px 0; padding: 18px 20px; background: var(--code-bg);
  border: 1px solid var(--line); border-radius: var(--radius); overflow-x: auto;
}
pre code { background: none; padding: 0; color: var(--ink); font-size: .9em; }
.video-card {
  margin: 28px 0; border-radius: var(--radius); overflow: hidden;
  background: var(--card); border: 1px solid var(--line); box-shadow: var(--shadow);
  transition: transform .18s ease, box-shadow .18s ease;
}
.video-card:hover { transform: translateY(-2px); box-shadow: 0 12px 32px rgba(28,25,23,.1); }
.video-wrapper { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; background: #111; }
.video-wrapper iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
.video-card img { width: 100%; display: block; cursor: zoom-in; }
.video-card img:hover { opacity: .92; }
.video-caption {
  padding: 12px 16px; font-family: system-ui, sans-serif; font-size: .88em;
  color: var(--muted); text-align: center; line-height: 1.6; margin: 0;
}
.video-caption a { color: var(--accent); font-weight: 500; }
.video-card.fallback { padding: 20px; text-align: center; }
.mermaid { display: flex; justify-content: center; margin: 28px 0; overflow-x: auto; }
.lightbox {
  position: fixed; inset: 0; z-index: 999; display: none;
  align-items: center; justify-content: center;
  background: rgba(28, 25, 23, 0.9); backdrop-filter: blur(4px);
  cursor: zoom-out; padding: 24px;
}
.lightbox.open { display: flex; }
.lightbox img { max-width: 96vw; max-height: 90vh; border-radius: 8px; box-shadow: 0 12px 60px rgba(0,0,0,.45); }
.lightbox-caption {
  position: absolute; bottom: 16px; left: 0; right: 0; text-align: center;
  color: #d6d3d1; font-family: system-ui, sans-serif; font-size: .85em;
}
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--line); border-radius: 4px; }
@media (max-width: 640px) {
  .book-content { padding: 28px 16px 80px; }
  h1 { font-size: 1.55em; }
  h2 { font-size: 1.25em; }
}
</style>
</head>
<body>
<article class="book-content">
{content}
</article>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function () {
  mermaid.initialize({ startOnLoad: false, theme: "neutral" });
  document.querySelectorAll("pre code, .highlight code").forEach(function (node) {
    var text = node.textContent.trim();
    if (/^(graph |sequenceDiagram|gantt|pie|classDiagram|stateDiagram|mindmap)/.test(text)) {
      var div = document.createElement("div");
      div.className = "mermaid";
      div.textContent = text;
      var wrap = node.closest(".highlight") || node.parentNode;
      wrap.replaceWith(div);
    }
  });
  mermaid.run();

  var lb = document.createElement("div");
  lb.className = "lightbox";
  lb.innerHTML = '<img alt=""><div class="lightbox-caption"></div>';
  document.body.appendChild(lb);
  var img = lb.querySelector("img");
  var cap = lb.querySelector(".lightbox-caption");
  function open(src, alt) {
    img.src = src; img.alt = alt || ""; cap.textContent = alt || "";
    lb.classList.add("open"); document.body.style.overflow = "hidden";
  }
  function close() {
    lb.classList.remove("open"); img.src = ""; document.body.style.overflow = "";
  }
  document.querySelectorAll(".screenshot-card img").forEach(function (el) {
    el.addEventListener("click", function () { open(el.src, el.alt); });
  });
  lb.addEventListener("click", close);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
});
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
