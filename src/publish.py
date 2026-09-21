"""发布成品到 pages 分支（orphan），目录名 = 视频标题。

机制对齐原项目：临时 index + plumbing，不切换工作区分支；
落地页视觉使用本项目「暖纸色书脊卡片」风格。

用法:
    python src/publish.py <video_id> [...]
    python src/publish.py --all
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GD = os.path.join(BASE, ".git")
PAGES = "pages"
CORRECTED = "transcript.corrected.txt"
SHELF_TITLE = "书架 · 电子书库"
SPINE = ["#0f766e", "#b45309", "#1d4ed8", "#9f1239"]


def run(args, env=None, cwd=BASE, check=True):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        env=e,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r


def safe_folder(title: str, bvid: str) -> str:
    name = (title or "").strip().replace("/", "／")
    name = re.sub(r'[\\:*?"<>|]', "", name)
    name = re.sub(r"\s+", " ", name).strip().strip(".")
    return name or bvid


def _src_blob_map(src: str) -> dict:
    rels = ["book.html", "book.md"]
    if os.path.isfile(os.path.join(src, CORRECTED)):
        rels.append(CORRECTED)
    img = os.path.join(src, "images")
    if os.path.isdir(img):
        rels += [
            "images/" + f for f in sorted(os.listdir(img)) if f.lower().endswith(".png")
        ]
    out = {}
    for rel in rels:
        path = os.path.join(src, *rel.split("/"))
        if not os.path.isfile(path):
            continue
        r = run(["hash-object", "--", path])
        out[rel] = r.stdout.strip()
    return out


def _pages_blob_map(folder: str) -> dict:
    if not folder:
        return {}
    r = run(
        ["-c", "core.quotePath=false", "ls-tree", "-r", PAGES, "--", folder],
        check=False,
    )
    if r.returncode != 0:
        return {}
    m = {}
    for line in r.stdout.splitlines():
        meta, _, path = line.partition("\t")
        m[path[len(folder) + 1 :]] = meta.split()[2]
    return m


def pages_tip():
    r = run(["rev-parse", "--verify", "--quiet", f"refs/heads/{PAGES}"], check=False)
    return r.stdout.strip() if r.returncode == 0 else None


def read_title(video_id: str) -> str:
    p = os.path.join(BASE, "output", video_id, "transcript.json")
    try:
        with open(p, encoding="utf-8") as f:
            return (json.load(f).get("title") or "").strip()
    except (OSError, json.JSONDecodeError):
        return ""


def _seq(meta: dict) -> int:
    m = re.search(r"\[(\d+)[-－/／]", meta.get("title", ""))
    return int(m.group(1)) if m else 10**9


def build_index_html(manifest: dict) -> str:
    """自有前端：暖纸底 + 书脊卡片。"""
    rows = sorted(
        manifest.items(), key=lambda kv: (_seq(kv[1]), kv[1].get("updated", ""))
    )
    cards = []
    for i, (vid, meta) in enumerate(rows):
        href = quote(meta["folder"]) + "/book.html"
        spine = SPINE[i % len(SPINE)]
        corrected = ""
        if meta.get("corrected"):
            corrected = (
                f'<a class="btn" href="{quote(meta["folder"])}/{CORRECTED}">字幕对照</a>'
            )
        meta_line = f"{vid} · 更新于 {meta.get('updated', '')[:10]}"
        cards.append(
            f"""      <a class="card" href="{href}" style="--spine:{spine}">
        <div class="badge">{i + 1:02d}</div>
        <h2>{html.escape(meta.get('title') or vid)}</h2>
        <p class="meta">{html.escape(meta_line)}</p>
        <div class="grow"></div>
        <div class="actions">{corrected}<span class="btn read">开始阅读</span></div>
      </a>"""
        )
    body = "\n".join(cards) or '      <div class="empty">暂无成品</div>'
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SHELF_TITLE}</title>
<style>
:root {{
  --paper:#f4efe6; --card:#fffdf8; --ink:#1c1917; --muted:#78716c;
  --accent:#0f766e; --warm:#b45309; --line:#e7e0d4;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
  font-family: system-ui, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--paper); color: var(--ink); line-height: 1.6;
}}
.wrap {{ max-width: 1080px; margin: 0 auto; padding: 56px 24px 64px; }}
header h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: .04em; margin-bottom: 8px; }}
header h1 span {{ color: var(--accent); }}
header p {{ color: var(--muted); font-size: 14px; margin-bottom: 32px; }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap:20px; }}
.card {{
  position:relative; display:flex; flex-direction:column; gap:10px;
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  padding:22px 20px 18px 28px; text-decoration:none; color:inherit; min-height:180px;
  transition: transform .16s ease, box-shadow .16s ease;
}}
.card:hover {{ transform:translateY(-3px); box-shadow:0 10px 28px rgba(28,25,23,.08); }}
.card::before {{
  content:""; position:absolute; left:0; top:14px; bottom:14px; width:6px;
  border-radius:0 4px 4px 0; background: var(--spine, var(--accent));
}}
.badge {{
  width:40px; height:40px; border-radius:10px; display:flex; align-items:center;
  justify-content:center; font-weight:700; color:#fff; font-size:14px;
  background: var(--spine, var(--accent));
}}
.card h2 {{ font-size:1.05rem; font-weight:650; line-height:1.45; }}
.meta {{ color:var(--muted); font-size:12.5px; }}
.grow {{ flex:1; }}
.actions {{ display:flex; gap:10px; justify-content:flex-end; align-items:center; }}
.btn {{
  font-size:12.5px; padding:6px 12px; border-radius:8px; background:#efe8db;
  color:var(--ink); text-decoration:none; border:1px solid var(--line);
}}
.btn:hover, .card:hover .btn.read {{ background:var(--accent); color:#fff; border-color:var(--accent); }}
.empty {{
  grid-column:1/-1; text-align:center; color:var(--muted); padding:48px;
  border:1px dashed var(--line); border-radius:14px; background:rgba(255,253,248,.6);
}}
footer {{ margin-top:40px; text-align:center; color:var(--muted); font-size:12px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>书<span>架</span></h1>
    <p>{SHELF_TITLE} · 共 {len(rows)} 本</p>
  </header>
  <div class="grid">
{body}
  </div>
  <footer>Shelf Pipeline · 与 VideoBook 工作流对齐 · 前端自有风格</footer>
</div>
</body>
</html>
"""


def ensure_git_repo():
    if not os.path.isdir(GD):
        print(">> 当前不是 git 仓库，正在 git init ...")
        run(["init"])
    # 确保有一次提交，否则 plumbing 可能不便
    r = run(["rev-parse", "--verify", "--quiet", "HEAD"], check=False)
    if r.returncode != 0:
        run(["add", "-A"])
        run(["commit", "-m", "chore: shelf init", "--allow-empty"])


def main():
    ensure_git_repo()
    ap = argparse.ArgumentParser(description="发布成品电子书到 pages 分支")
    ap.add_argument("video_id", nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    out = os.path.join(BASE, "output")
    if args.all:
        ids = [
            d
            for d in sorted(os.listdir(out))
            if os.path.isfile(os.path.join(out, d, "book.html"))
        ]
    else:
        ids = args.video_id
    if not ids:
        sys.exit("没有可发布的视频：请提供 video_id 或使用 --all")

    for vid in ids:
        if not os.path.isfile(os.path.join(out, vid, "book.html")):
            sys.exit(f"output/{vid}/book.html 不存在，先完成渲染步骤")

    tip = pages_tip()
    tmp = tempfile.mkdtemp(prefix="shelf_publish_")
    env = {"GIT_INDEX_FILE": tmp + ".index"}
    g = lambda *a, **k: run(list(a), env=env, **k)  # noqa: E731

    try:
        if tip:
            g("--git-dir", GD, "--work-tree", tmp, "read-tree", PAGES)
            g("--git-dir", GD, "--work-tree", tmp, "checkout-index", "-a", check=False)
        else:
            g("--git-dir", GD, "--work-tree", tmp, "read-tree", "--empty")

        manifest = {}
        if tip:
            r = run(["show", f"{PAGES}:manifest.json"], check=False)
            if r.returncode == 0:
                try:
                    manifest = json.loads(r.stdout)
                except json.JSONDecodeError:
                    manifest = {}

        now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")

        for vid in ids:
            title = read_title(vid)
            folder = safe_folder(title, vid)
            others = {k: v.get("folder") for k, v in manifest.items() if k != vid}
            if folder in others.values():
                folder = f"{folder} ({vid})"
            old = manifest.get(vid, {}).get("folder")
            src = os.path.join(out, vid)
            dst = os.path.join(tmp, folder)

            if old == folder and _pages_blob_map(old) == _src_blob_map(src):
                manifest[vid] = {
                    "folder": folder,
                    "title": title,
                    "updated": manifest[vid].get("updated", now),
                    "corrected": os.path.isfile(os.path.join(src, CORRECTED)),
                }
                print(f">> {vid}: 内容无变化，保持原发布")
                continue

            if old and old != folder:
                shutil.rmtree(os.path.join(tmp, old), ignore_errors=True)
                print(f">> {vid}: 目录改名 {old} -> {folder}")

            manifest[vid] = {
                "folder": folder,
                "title": title,
                "updated": now,
                "corrected": os.path.isfile(os.path.join(src, CORRECTED)),
            }

            shutil.rmtree(dst, ignore_errors=True)
            os.makedirs(os.path.join(dst, "images"), exist_ok=True)
            shutil.copyfile(os.path.join(src, "book.html"), os.path.join(dst, "book.html"))
            shutil.copyfile(os.path.join(src, "book.md"), os.path.join(dst, "book.md"))
            if os.path.isfile(os.path.join(src, CORRECTED)):
                shutil.copyfile(
                    os.path.join(src, CORRECTED), os.path.join(dst, CORRECTED)
                )
            n = 0
            img = os.path.join(src, "images")
            if os.path.isdir(img):
                for fn in sorted(os.listdir(img)):
                    if fn.lower().endswith(".png"):
                        shutil.copyfile(os.path.join(img, fn), os.path.join(dst, "images", fn))
                        n += 1
            print(f">> {vid}: {n} 张截图 -> {folder}/")

        with open(os.path.join(tmp, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        with open(os.path.join(tmp, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_index_html(manifest))

        g("-C", tmp, "--git-dir", GD, "--work-tree", tmp, "add", "-A")
        tree = g("--git-dir", GD, "--work-tree", tmp, "write-tree").stdout.strip()
        if tip:
            old_tree = run(["rev-parse", f"{PAGES}^{{tree}}"]).stdout.strip()
            if tree == old_tree:
                print(">> 内容无变化，跳过提交")
                return
        parent = ["-p", tip] if tip else []
        commit = run(
            ["commit-tree", tree]
            + parent
            + ["-m", f"publish: {', '.join(ids)}"]
        ).stdout.strip()
        run(["update-ref", f"refs/heads/{PAGES}", commit])
        print(f">> pages 分支已更新: {commit[:8]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        try:
            os.remove(tmp + ".index")
        except OSError:
            pass

    print(f"\n完成。本地预览可导出 pages；推送请执行: git push origin {PAGES}")


if __name__ == "__main__":
    main()
