"""Visual feature classifier for civic issue photos.

This is an implemented, testable pipeline (Pillow + NumPy). It scores four
municipal issue types from color, brightness, texture, and edge statistics.
It is not a deep neural network. Confidence is a softmax over heuristic scores.
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from PIL import Image

CATEGORIES = ("pothole", "garbage", "streetlight", "waterlogging")

def _softmax(scores: dict[str, float]) -> dict[str, float]:
    max_s = max(scores.values())
    exps = {k: math.exp(v - max_s) for k, v in scores.items()}
    total = sum(exps.values()) or 1.0
    return {k: exps[k] / total for k in scores}

def extract_features(image_path: str | Path) -> dict[str, float]:
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    brightness = float(gray.mean())
    saturation = float(np.abs(arr.max(axis=2) - arr.min(axis=2)).mean())
    color_std = float(arr.std())
    channel_spread = float(np.mean([r.std(), g.std(), b.std()]))
    blue_dom = float(((b > r) & (b > g) & (b > 0.28)).mean())
    green_dom = float(((g > r) & (g > b) & (g > 0.28)).mean())
    brown_gray = float(((np.abs(r-g)<0.12)&(np.abs(g-b)<0.12)&(gray>0.22)&(gray<0.58)).mean())
    yellow_warm = float(((r > 0.55) & (g > 0.4) & (b < 0.4)).mean())
    bright_spots = float((gray > 0.85).mean())
    dark_ratio = float((gray < 0.18).mean())
    dx = float(np.abs(np.diff(gray, axis=1)).mean())
    dy = float(np.abs(np.diff(gray, axis=0)).mean())
    return {"brightness":brightness,"saturation":saturation,"color_std":color_std,"channel_spread":channel_spread,"blue_dom":blue_dom,"green_dom":green_dom,"brown_gray":brown_gray,"yellow_warm":yellow_warm,"bright_spots":bright_spots,"dark_ratio":dark_ratio,"edges":dx+dy}

def classify_image(image_path: str | Path) -> dict:
    f = extract_features(image_path)
    scores = {
      "waterlogging": 3.2*f["blue_dom"]+0.8*(1.0-min(f["edges"]/0.12,1.0))+0.5*(1.0-f["saturation"])+0.3*f["green_dom"],
      "streetlight": 4.2*f["bright_spots"]+2.6*f["dark_ratio"]+1.4*f["yellow_warm"]+0.2*f["edges"]-1.5*f["brown_gray"],
      "pothole": 2.8*f["brown_gray"]+1.6*min(f["edges"]/0.1,1.5)+0.7*(1.0-f["saturation"])+0.4*(1.0-f["brightness"])-2.0*f["bright_spots"]-1.2*f["dark_ratio"],
      "garbage": 2.4*f["color_std"]+2.0*f["channel_spread"]+1.6*f["saturation"]+0.6*f["yellow_warm"],
    }
    probs = _softmax(scores)
    category = max(probs, key=probs.get)
    return {"category":category,"confidence":round(probs[category],4),"scores":{k:round(v,4) for k,v in probs.items()},"features":{k:round(v,4) for k,v in f.items()},"pipeline":"civic-eye-visual-features-v1"}

def average_hash(image_path: str | Path, size: int = 8) -> str:
    img = Image.open(image_path).convert("L").resize((size, size))
    pixels = np.asarray(img, dtype=np.float32)
    mean = pixels.mean()
    bits = (pixels > mean).flatten()
    value = 0
    for bit in bits: value = (value << 1) | int(bit)
    width = (size * size + 3) // 4
    return f"{value:0{width}x}"

def hash_distance(hash_a: str, hash_b: str) -> int:
    if not hash_a or not hash_b: return 64
    return (int(hash_a,16) ^ int(hash_b,16)).bit_count()
