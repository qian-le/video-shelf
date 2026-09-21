"""与原项目对齐的路径配置。"""
from __future__ import annotations

import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE, "output")
CAPTURE_PROFILE = os.path.join(BASE, ".capture-profile")
PROMPTS_DIR = os.path.join(BASE, "prompts")


def get_video_dir(video_id: str) -> str:
    path = os.path.join(OUTPUT_DIR, video_id)
    os.makedirs(path, exist_ok=True)
    return path


def get_image_dir(video_id: str) -> str:
    path = os.path.join(get_video_dir(video_id), "images")
    os.makedirs(path, exist_ok=True)
    return path
