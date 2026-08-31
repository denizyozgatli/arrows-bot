import json
import os
import time

import cv2
import numpy as np

from arrows_bot.adb import connection

VALID_DIFFICULTIES = {"easy", "hard", "super_hard"}


def collect_screenshots(out_dir: str, count: int = 10, prefix: str = "shot") -> list:
    """Capture `count` screenshots from the device and save them as PNGs.

    Reuses the existing ADB screencap implementation; no second ADB layer.
    """
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for i in range(count):
        raw = connection.screencap()
        if not raw:
            print(f"[collect] screencap returned empty for shot {i + 1}; skipping")
            continue
        img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[collect] failed to decode shot {i + 1}; skipping")
            continue
        path = os.path.join(out_dir, f"{prefix}_{i + 1:04d}.png")
        cv2.imwrite(path, img)
        saved.append(path)
        print(f"[collect] saved {path}")
        time.sleep(0.5)
    return saved


# ---------------------------------------------------------------------------
# Level-based collection (multi-viewport aware)
#
# A "level" and a "viewport" are different concepts. One level may produce
# several viewport screenshots (same board state / exploration sequence), or
# exactly one. Difficulty and viewport count are INDEPENDENT properties.
#
# Structure produced:
#   data/raw/<level_id>/
#       viewport_001.png
#       viewport_002.png
#       metadata.json
# ---------------------------------------------------------------------------


def device_connected() -> bool:
    """Return True if an ADB device is reachable via the existing screencap."""
    try:
        return bool(connection.screencap())
    except Exception:
        return False


def load_metadata(meta_path: str):
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_metadata(meta_path: str, meta) -> None:
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def validate_metadata(meta) -> bool:
    """Validate a level metadata object. Raises ValueError on problems."""
    if not isinstance(meta, dict):
        raise ValueError("metadata must be a JSON object")
    if "level_id" not in meta or not isinstance(meta["level_id"], str):
        raise ValueError("metadata missing string field 'level_id'")
    if meta.get("difficulty") not in VALID_DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {sorted(VALID_DIFFICULTIES)}")
    vc = meta.get("viewport_count")
    if not isinstance(vc, int) or vc < 0:
        raise ValueError("viewport_count must be a non-negative integer")
    viewports = meta.get("viewports", [])
    if not isinstance(viewports, list):
        raise ValueError("'viewports' must be a list")
    for v in viewports:
        if not isinstance(v, dict):
            raise ValueError("each viewport must be an object")
        if not isinstance(v.get("viewport_index"), int):
            raise ValueError("each viewport needs integer 'viewport_index'")
        if not isinstance(v.get("file"), str):
            raise ValueError("each viewport needs string 'file'")
    return True


def collect_level(
    level_id: str,
    difficulty: str,
    count: int = 1,
    notes: str = None,
    session: str = None,
    pause: float = 3.0,
) -> dict:
    """Capture one or more viewport screenshots for a single level.

    The human is responsible for changing the viewport between captures; this
    tool never scrolls, taps, or plays the game. It only captures screenshots,
    names them, and records metadata.
    """
    if difficulty not in VALID_DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {sorted(VALID_DIFFICULTIES)}")
    if count < 1:
        raise ValueError("count must be >= 1")
    if not device_connected():
        raise RuntimeError("No ADB device reachable; cannot capture. Check ADB_HOST/ADB_PORT.")

    level_dir = os.path.join("data", "raw", level_id)
    os.makedirs(level_dir, exist_ok=True)
    meta_path = os.path.join(level_dir, "metadata.json")
    meta = load_metadata(meta_path)
    if meta is None:
        meta = {"level_id": level_id, "difficulty": difficulty, "viewport_count": 0, "viewports": []}
    else:
        # Reusing an existing level_id: warn if difficulty differs (likely a duplicate level).
        if meta.get("difficulty") != difficulty:
            print(
                f"[collect-level] WARNING: {level_id} already has difficulty "
                f"{meta.get('difficulty')!r}; you supplied {difficulty!r}. "
                f"Use a unique level_id for a new level."
            )
        meta["difficulty"] = difficulty
    if session:
        meta["collection_session"] = session
    if notes:
        meta["notes"] = notes

    start = len(meta["viewports"]) + 1
    for i in range(count):
        idx = start + i
        raw = connection.screencap()
        if not raw:
            print(f"[collect-level] screencap empty for viewport {idx}; skipping")
            continue
        img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[collect-level] decode failed for viewport {idx}; skipping")
            continue
        h, w = img.shape[:2]
        fname = f"viewport_{idx:03d}.png"
        path = os.path.join(level_dir, fname)
        cv2.imwrite(path, img)
        meta["viewports"].append(
            {"viewport_index": idx, "file": fname, "screen_width": w, "screen_height": h}
        )
        print(f"[collect-level] saved {path} ({w}x{h})")
        if i < count - 1:
            print(f"[collect-level] change the viewport now; capturing next in {pause}s...")
            time.sleep(pause)

    meta["viewport_count"] = len(meta["viewports"])
    validate_metadata(meta)
    save_metadata(meta_path, meta)
    print(f"[collect-level] metadata written to {meta_path}")
    return meta
