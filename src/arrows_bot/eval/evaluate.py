import json
import os

import cv2

from arrows_bot.eval.annotate import validate_annotation
from arrows_bot.eval.metrics import match_detections
from arrows_bot.vision.detector import ArrowDetector


def _find_image(data_root: str, annotations_root: str, ann_path: str, image_name: str):
    """Locate the screenshot for an annotation.

    Prefers the image in the same relative level directory as the annotation
    (supports nested level/viewport structures), then falls back to a recursive
    basename search (existing flat structure). Backward-compatible.
    """
    rel = os.path.relpath(ann_path, annotations_root)
    rel_dir = os.path.dirname(rel)
    if rel_dir:
        candidate = os.path.join(data_root, rel_dir, image_name)
        if os.path.exists(candidate):
            return candidate
    for dirpath, _, files in os.walk(data_root):
        if image_name in files:
            return os.path.join(dirpath, image_name)
    return None


def evaluate_image(image_path: str, annotation, detector: ArrowDetector, dist_threshold: float) -> dict:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"could not read image: {image_path}")
    h, w = img.shape[:2]

    mask = detector.preprocess_board(img)
    detections = detector.extract_arrows(mask)
    det_list = [
        {"x": int(a.head[0]), "y": int(a.head[1]), "direction": a.direction, "score": float(a.score)}
        for a in detections
    ]
    gt_list = [{"x": a["x"], "y": a["y"], "direction": a["direction"]} for a in annotation["arrows"]]

    matches, used_gt, used_det = match_detections(gt_list, det_list, dist_threshold)

    tp = len(matches)
    fp = len(det_list) - tp
    fn = len(gt_list) - tp
    dir_correct = sum(
        1 for m in matches if gt_list[m["gt"]]["direction"] == det_list[m["det"]]["direction"]
    )

    # Arrows in the top/bottom 11% band that the detector zeroes out by design.
    band = int(h * 0.11)
    band_gt = [g for g in gt_list if g["y"] < band or g["y"] >= h - band]

    return {
        "image": os.path.basename(image_path),
        "image_path": image_path,
        "size": [w, h],
        "detected_count": len(det_list),
        "ground_truth_count": len(gt_list),
        "detections": det_list,
        "ground_truth": gt_list,
        "matches": matches,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "direction_correct": dir_correct,
        "direction_accuracy": (dir_correct / tp) if tp else None,
        "precision": (tp / (tp + fp)) if (tp + fp) else None,
        "recall": (tp / (tp + fn)) if (tp + fn) else None,
        "band_ground_truth_count": len(band_gt),
    }


def run_evaluation(data_root: str, annotations_root: str, out_dir: str, dist_threshold: float) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    detector = ArrowDetector()

    ann_files = []
    for dirpath, _, files in os.walk(annotations_root):
        for fn in files:
            if fn.endswith(".json"):
                ann_files.append(os.path.join(dirpath, fn))
    ann_files.sort()

    results = []
    errors = []
    for ann_path in ann_files:
        try:
            with open(ann_path, "r", encoding="utf-8") as f:
                annotation = json.load(f)
            validate_annotation(annotation)
            image_path = _find_image(data_root, annotations_root, ann_path, annotation["image"])
            if image_path is None:
                raise FileNotFoundError(
                    f"image '{annotation['image']}' not found under {data_root}"
                )
            res = evaluate_image(image_path, annotation, detector, dist_threshold)
            res["annotation_file"] = ann_path
            results.append(res)
            print(
                f"[evaluate] {os.path.basename(ann_path)}: "
                f"det={res['detected_count']} gt={res['ground_truth_count']} "
                f"tp={res['tp']} fp={res['fp']} fn={res['fn']}"
            )
        except Exception as e:
            errors.append({"annotation_file": ann_path, "error": str(e)})
            print(f"[evaluate] ERROR {ann_path}: {e}")

    tp = sum(r["tp"] for r in results)
    fp = sum(r["fp"] for r in results)
    fn = sum(r["fn"] for r in results)
    dc = sum(r["direction_correct"] for r in results)

    aggregate = {
        "images": len(results),
        "errors": errors,
        "total_detected": sum(r["detected_count"] for r in results),
        "total_ground_truth": sum(r["ground_truth_count"] for r in results),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": (tp / (tp + fp)) if (tp + fp) else None,
        "recall": (tp / (tp + fn)) if (tp + fn) else None,
        "direction_correct": dc,
        "direction_accuracy": (dc / tp) if tp else None,
        "dist_threshold": dist_threshold,
    }

    payload = {"aggregate": aggregate, "per_image": results}
    out_json = os.path.join(out_dir, "results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[evaluate] wrote {out_json}")
    return payload
