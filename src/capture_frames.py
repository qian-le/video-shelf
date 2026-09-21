"""截帧：专用 .capture-profile，CLI 与原项目对齐。

用法:
  python src/capture_frames.py --setup-profile
  python src/capture_frames.py <video_id> "<VIDEO_URL>"
  python src/capture_frames.py <video_id> --materialize-only
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import CAPTURE_PROFILE, get_image_dir, get_video_dir  # noqa: E402

SHOT_PLACEHOLDER = re.compile(
    r"!\[([^\]]*)\]\(SCREENSHOT:(\d{2}:\d{2}:\d{2}(?:\.\d+)?)\)"
)
SHOT_IMAGE = re.compile(
    r"!\[([^\]]*)\]\((?:images/)?shot_(\d{2})_(\d{2})_(\d{2})\.png\)"
)


def ts_to_sec(ts: str) -> int:
    ts = ts.split(".")[0]
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def collect_timestamps(md_path: str) -> list[str]:
    if not os.path.isfile(md_path):
        return []
    text = open(md_path, encoding="utf-8").read()
    found = []
    for m in SHOT_PLACEHOLDER.finditer(text):
        found.append(m.group(2).split(".")[0])
    for m in SHOT_IMAGE.finditer(text):
        found.append(f"{m.group(2)}:{m.group(3)}:{m.group(4)}")
    seen, out = set(), []
    for ts in found:
        if ts not in seen:
            seen.add(ts)
            out.append(ts)
    return out


def setup_profile() -> None:
    from playwright.sync_api import sync_playwright

    os.makedirs(CAPTURE_PROFILE, exist_ok=True)
    print(f">> 打开 Chrome（{CAPTURE_PROFILE}），请登录后关闭窗口")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            CAPTURE_PROFILE,
            headless=False,
            channel="chrome",
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.bilibili.com", wait_until="domcontentloaded")
        try:
            ctx.wait_for_event("close", timeout=0)
        except Exception:
            pass
        try:
            ctx.close()
        except Exception:
            pass
    print("✅ 登录态已写入 .capture-profile")


def materialize(video_id: str) -> None:
    vdir = get_video_dir(video_id)
    img_dir = get_image_dir(video_id)
    for name in ("book.md", "book.tagged.md"):
        path = os.path.join(vdir, name)
        # book.md 是主目标；tagged 只在首次备份
    md_path = os.path.join(vdir, "book.md")
    if not os.path.isfile(md_path):
        print(">> 无 book.md，跳过物化")
        return
    text = open(md_path, encoding="utf-8").read()
    tagged = os.path.join(vdir, "book.tagged.md")
    if SHOT_PLACEHOLDER.search(text) and not os.path.isfile(tagged):
        open(tagged, "w", encoding="utf-8").write(text)

    def repl(m: re.Match) -> str:
        desc, ts = m.group(1), m.group(2).split(".")[0]
        fname = f"shot_{ts.replace(':', '_')}.png"
        if os.path.isfile(os.path.join(img_dir, fname)):
            return f"![{desc}](images/{fname})"
        return m.group(0)

    new_text = SHOT_PLACEHOLDER.sub(repl, text)
    open(md_path, "w", encoding="utf-8").write(new_text)
    remain = len(SHOT_PLACEHOLDER.findall(new_text))
    print(f"✅ 物化完成，剩余 SCREENSHOT 占位 {remain} 个")


def capture(video_id: str, url: str) -> None:
    from playwright.sync_api import sync_playwright

    vdir = get_video_dir(video_id)
    md_path = os.path.join(vdir, "book.md")
    if not os.path.isfile(md_path):
        # 也支持 tagged 稿
        md_path = os.path.join(vdir, "book.tagged.md")
    if not os.path.isfile(md_path):
        raise SystemExit("缺少 book.md / book.tagged.md")

    # 占位清单优先读 tagged（幂等补帧）
    tagged = os.path.join(vdir, "book.tagged.md")
    list_path = tagged if os.path.isfile(tagged) else md_path
    stamps = collect_timestamps(list_path)
    if not stamps:
        print(">> 无 SCREENSHOT 占位")
        materialize(video_id)
        return

    img_dir = get_image_dir(video_id)
    missing = []
    for ts in stamps:
        fname = f"shot_{ts.replace(':', '_')}.png"
        if not os.path.isfile(os.path.join(img_dir, fname)):
            missing.append(ts)
    print(f">> {len(stamps)} 个时间点，待截 {len(missing)} 张")
    if missing:
        if not os.listdir(CAPTURE_PROFILE):
            raise SystemExit("请先: python src/capture_frames.py --setup-profile")
        if "bilibili" not in url and not video_id.startswith("BV"):
            print(">> 提示：当前实现面向 B 站播放器；YouTube 请确认代理")

        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                CAPTURE_PROFILE,
                headless=True,
                channel="chrome",
                viewport={"width": 1280, "height": 720},
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.add_init_script(
                """
                const st = document.createElement('style');
                st.textContent = `.bpx-player-control-wrap,.bpx-player-top-wrap,
                .bpx-player-ending-panel,.bpx-player-panel-wrap{display:none!important}`;
                document.addEventListener('DOMContentLoaded',()=>document.head.appendChild(st));
                """
            )
            bvid = video_id if video_id.startswith("BV") else None
            if not bvid:
                m = re.search(r"(BV[0-9A-Za-z]+)", url or "")
                bvid = m.group(1) if m else video_id
            for ts in missing:
                sec = ts_to_sec(ts)
                if bvid and bvid.startswith("BV"):
                    target = (
                        f"https://player.bilibili.com/player.html?bvid={bvid}"
                        f"&t={sec}&autoplay=0&high_quality=1&danmaku=0"
                    )
                else:
                    target = f"https://www.youtube.com/embed/{video_id}?start={sec}&autoplay=0"
                print(f"  · {ts}")
                try:
                    page.goto(target, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(4000)
                    page.evaluate("()=>{const v=document.querySelector('video'); if(v){try{v.pause()}catch(e){}}}")
                    page.wait_for_timeout(1200)
                    out = os.path.join(img_dir, f"shot_{ts.replace(':', '_')}.png")
                    el = page.query_selector("video")
                    if el:
                        try:
                            el.screenshot(path=out)
                        except Exception:
                            page.screenshot(path=out)
                    else:
                        page.screenshot(path=out)
                    size = os.path.getsize(out) if os.path.isfile(out) else 0
                    if size < 3000:
                        print(f"    ! 可能黑帧 ({size}B)")
                    else:
                        print(f"    saved {os.path.basename(out)}")
                except Exception as e:
                    print(f"    ! 失败 {ts}: {e}")
            try:
                ctx.close()
            except Exception:
                pass

    materialize(video_id)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    if args[0] == "--setup-profile":
        setup_profile()
        return
    if len(args) < 2:
        raise SystemExit(__doc__)
    video_id = args[0]
    if args[1] == "--materialize-only":
        materialize(video_id)
        return
    capture(video_id, args[1])


if __name__ == "__main__":
    main()
