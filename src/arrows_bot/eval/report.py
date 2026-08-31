import json
import os

_DIR_VECTORS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
}


def _fmt(v) -> str:
    return "n/a" if v is None else f"{v:.3f}"


def _draw_annotated(image_path: str, res: dict, out_path: str) -> bool:
    """Draw ground truth, detections, false positives and false negatives.

    Returns False if OpenCV is unavailable (report still written without images).
    """
    try:
        import cv2
    except ImportError:
        return False
    img = cv2.imread(image_path)
    if img is None:
        return False

    # Ground truth: green circles.
    for g in res["ground_truth"]:
        cv2.circle(img, (int(g["x"]), int(g["y"])), 12, (0, 200, 0), 2)

    # Detections: blue circles + direction line.
    for d in res["detections"]:
        x, y = int(d["x"]), int(d["y"])
        cv2.circle(img, (x, y), 8, (255, 0, 0), 2)
        vx, vy = _DIR_VECTORS[d["direction"]]
        cv2.arrowedLine(img, (x, y), (x + vx * 20, y + vy * 20), (255, 0, 0), 2)

    # False positives: red X.
    matched_det = {m["det"] for m in res["matches"]}
    for i, d in enumerate(res["detections"]):
        if i not in matched_det:
            x, y = int(d["x"]), int(d["y"])
            cv2.line(img, (x - 8, y - 8), (x + 8, y + 8), (0, 0, 255), 2)
            cv2.line(img, (x - 8, y + 8), (x + 8, y - 8), (0, 0, 255), 2)

    # False negatives: yellow X.
    matched_gt = {m["gt"] for m in res["matches"]}
    for i, g in enumerate(res["ground_truth"]):
        if i not in matched_gt:
            x, y = int(g["x"]), int(g["y"])
            cv2.line(img, (x - 8, y - 8), (x + 8, y + 8), (0, 255, 255), 2)
            cv2.line(img, (x - 8, y + 8), (x + 8, y - 8), (0, 255, 255), 2)

    cv2.imwrite(out_path, img)
    return True


def generate_report(results_dir: str) -> None:
    results_path = os.path.join(results_dir, "results.json")
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"no results.json found in {results_dir}; run 'evaluate' first")
    with open(results_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    agg = payload["aggregate"]
    per_image = payload["per_image"]

    with open(os.path.join(results_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)

    annotated_dir = os.path.join(results_dir, "annotated")
    os.makedirs(annotated_dir, exist_ok=True)
    images_written = 0
    for res in per_image:
        out = os.path.join(annotated_dir, f"annotated_{res['image']}")
        if _draw_annotated(res["image_path"], res, out):
            images_written += 1

    lines = []
    lines.append("# Arrow Detector — Offline Evaluation Report")
    lines.append("")
    lines.append(f"- Images evaluated: {agg['images']}")
    lines.append(f"- Matching distance threshold: {agg['dist_threshold']} px")
    lines.append(f"- Total detections: {agg['total_detected']}")
    lines.append(f"- Total ground truth: {agg['total_ground_truth']}")
    lines.append("")
    lines.append("## Aggregate metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| True Positives | {agg['tp']} |")
    lines.append(f"| False Positives | {agg['fp']} |")
    lines.append(f"| False Negatives | {agg['fn']} |")
    lines.append(f"| Precision | {_fmt(agg['precision'])} |")
    lines.append(f"| Recall | {_fmt(agg['recall'])} |")
    lines.append(f"| Direction accuracy | {_fmt(agg['direction_accuracy'])} |")
    lines.append("")
    lines.append("## Per-image results")
    lines.append("")
    lines.append("| Image | Detected | GT | TP | FP | FN | Precision | Recall | Dir acc | Band GT |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in per_image:
        lines.append(
            f"| {r['image']} | {r['detected_count']} | {r['ground_truth_count']} | "
            f"{r['tp']} | {r['fp']} | {r['fn']} | {_fmt(r['precision'])} | "
            f"{_fmt(r['recall'])} | {_fmt(r['direction_accuracy'])} | {r['band_ground_truth_count']} |"
        )
    lines.append("")
    lines.append("## Errors")
    lines.append("")
    if agg["errors"]:
        for e in agg["errors"]:
            lines.append(f"- `{e['annotation_file']}`: {e['error']}")
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Legend (annotated images)")
    lines.append("")
    lines.append("- Green circle: ground-truth arrow")
    lines.append("- Blue circle + line: detection (line shows direction)")
    lines.append("- Red X: false positive")
    lines.append("- Yellow X: false negative")
    lines.append(
        "- 'Band GT' = ground-truth arrows in the top/bottom 11% band that the detector "
        "zeroes out by design (reported separately, not counted as normal false negatives)."
    )

    report_path = os.path.join(results_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[report] wrote {report_path}")
    print(f"[report] wrote {os.path.join(results_dir, 'metrics.json')}")
    if images_written:
        print(f"[report] wrote {images_written} annotated images to {annotated_dir}")
    else:
        print("[report] WARNING: no annotated images written (OpenCV unavailable or images missing)")
