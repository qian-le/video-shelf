"""由 transcript.json 生成 transcript.corrected.txt（对照稿）。

原则：逐段保留讲师原始字词与顺序；仅做 ASR 错词替换 + 口癖清理。
CLI 与原项目对齐：python src/make_corrected.py <video_id> | --all
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ASR 错词 → 正确词（可按视频扩充；按 key 长度降序替换）
MAP = {
    "深圳市软件工程": "生成式软件工程",
    "生成式软软件工程": "生成式软件工程",
    "威尔法尔": "verifier",
    "威尔法": "verifier",
    "chain of salt": "chain of thought",
    "chal thought": "chain of thought",
    "chap out": "chain of thought",
    "deep pick": "DeepSeek",
    "deep pick的": "DeepSeek 的",
    "deep sv4flash": "DeepSeek V4 Flash",
    "deep sick": "DeepSeek",
    "D4C": "DeepSeek",
    "KIMIK3": "Kimi K3",
    "GPT5.6": "GPT-5.6",
    "GBT5.6": "GPT-5.6",
    "GPP5.6": "GPT-5.6",
    "CHEGBT": "ChatGPT",
    "拆GBT": "ChatGPT",
    "拆GPT": "ChatGPT",
    "GBT": "ChatGPT",
    "agents点MD": "agents.md",
    "AGENTS点MD": "agents.md",
    "agency md": "agents.md",
    "AI slap": "AI slop",
    "AI SLOP": "AI slop",
    "passer": "parser",
    "sober": "solver",
    "get it": "git",
    "get rebase": "git rebase",
    "瑞贝斯": "rebase",
    "瑞贝斯mage": "rebase/merge",
    "JUJS": "Jujutsu",
    "JJ词": "Jujutsu",
    "句句词": "Jujutsu",
    "work tree": "worktree",
    "WORKTI": "worktree",
    "tm max": "tmux",
    "t max": "tmux",
    "tmMax": "tmux",
    "mvp的PARAA": "MVP 的范式",
    "minimal variable product": "minimum viable product",
    "of of mist optimistic": "optimistic",
    "OLBOT": "abort",
    "traction": "transaction",
    "slap out": "slop",
    "report点dB": "repo.db",
    "report点DB": "repo.db",
    "ripple": "repo",
    "rapport": "repo",
    "computing m": "CONTRIBUTING.md",
    "contributing点md": "CONTRIBUTING.md",
    "trace ability": "traceability",
    "suffer trace ability": "software traceability",
    "technical debt": "technical debt",
    "staging error": "staging area",
    "seating error": "staging area",
    "STH": "stash",
    "STATCH": "stash",
    "st a stack": "stash",
}

# 纯语气词整段删除
FILLER_ONLY = re.compile(
    r"^[\s，。、！？~…—-]*"
    r"(嗯+|啊+|哦+|呃+|呀+|哈+|哎+|这个|那个|对吧|好吧|好|OK|ok|Okay|Anyway|anyway)"
    r"[\s，。、！？~…—-]*$"
)
TRAIL_FILLER = re.compile(
    r"(嗯+|啊+|哦+|呃+|呀+|对吧|好吧)[\s，。、！？~…—-]*$"
)
STUTTER = re.compile(r"([一-鿿])\1{3,}")


def apply_map(text: str) -> str:
    for k in sorted(MAP.keys(), key=len, reverse=True):
        if k in text:
            text = text.replace(k, MAP[k])
    return text


def clean_line(text: str) -> str | None:
    text = text.strip()
    if not text:
        return None
    if FILLER_ONLY.match(text):
        return None
    text = apply_map(text)
    text = TRAIL_FILLER.sub("", text).strip()
    # 三字以上叠词压成双字（有意强调的双字保留）
    text = STUTTER.sub(r"\1\1", text)
    if not text or FILLER_ONLY.match(text):
        return None
    return text


def process_one(video_id: str) -> None:
    path = os.path.join(BASE, "output", video_id, "transcript.json")
    if not os.path.isfile(path):
        print(f"[ERR] 缺少 {path}")
        return
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    segments = data.get("segments") or []
    lines = []
    for seg in segments:
        cleaned = clean_line(seg.get("text") or "")
        if cleaned is None:
            continue
        start = seg.get("start", "00:00:00")
        # 与 transcript.txt 同构：[HH:MM:SS] 文本
        if start.count(":") == 2:
            # 按原项目习惯展示 MM:SS 也可；这里保留全时间戳便于对照
            stamp = start
        else:
            stamp = start
        lines.append(f"[{stamp}] {cleaned}")
    out = os.path.join(BASE, "output", video_id, "transcript.corrected.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{video_id}: {len(segments)} 段 -> {len(lines)} 行 → {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id", nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    out_root = os.path.join(BASE, "output")
    if args.all:
        ids = [
            d
            for d in sorted(os.listdir(out_root))
            if os.path.isfile(os.path.join(out_root, d, "transcript.json"))
        ]
    else:
        ids = args.video_id
    if not ids:
        sys.exit("请提供 video_id 或 --all")
    for vid in ids:
        process_one(vid)


if __name__ == "__main__":
    main()
