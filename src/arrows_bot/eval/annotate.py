import json
import os

import numpy as np

VALID_DIRECTIONS = {"UP", "DOWN", "LEFT", "RIGHT"}

# Annotation JSON schema (designed so bounding-box / size fields can be added later):
# {
#   "image": "0001.png",
#   "arrows": [
#       {"x": 120, "y": 340, "direction": "UP"},
#       ...
#   ]
# }
# Optional future fields per arrow: "bbox": [x, y, w, h], "size": w, "confidence": 1.0


def validate_annotation(data) -> bool:
    """Validate the structure of an annotation object. Raises ValueError on problems."""
    if not isinstance(data, dict):
        raise ValueError("annotation must be a JSON object")
    if "image" not in data or not isinstance(data["image"], str):
        raise ValueError("annotation missing string field 'image'")
    arrows = data.get("arrows", [])
    if not isinstance(arrows, list):
        raise ValueError("'arrows' must be a list")
    for a in arrows:
        if not isinstance(a, dict):
            raise ValueError("each arrow must be an object")
        if "x" not in a or "y" not in a:
            raise ValueError("each arrow needs 'x' and 'y'")
        if not isinstance(a["x"], (int, float)) or not isinstance(a["y"], (int, float)):
            raise ValueError("arrow 'x'/'y' must be numbers")
        d = a.get("direction")
        if d not in VALID_DIRECTIONS:
            raise ValueError(f"invalid direction {d!r}; expected one of {sorted(VALID_DIRECTIONS)}")
    return True


def load_annotation(path: str):
    """Load and validate an annotation file. Returns None if the file does not exist."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    validate_annotation(data)
    return data


def save_annotation(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def default_annotation_path(image_path: str) -> str:
    """Map data/raw/<scenario>/<name>.png -> data/annotations/<scenario>/<name>.json"""
    name = os.path.splitext(os.path.basename(image_path))[0] + ".json"
    parent = os.path.basename(os.path.dirname(image_path))
    return os.path.join("data", "annotations", parent, name)


def annotate_image(image_path: str, out_path: str, use_terminal: bool = False) -> None:
    """Interactively annotate a screenshot.

    By default, uses a matplotlib clicker when a GUI backend is available,
    otherwise falls back to terminal coordinate entry. If `use_terminal` is True,
    the terminal annotator is used directly.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"image not found: {image_path}")

    existing = load_annotation(out_path) if os.path.exists(out_path) else None
    if existing is None:
        existing = {"image": os.path.basename(image_path), "arrows": []}

    if use_terminal:
        _terminal_annotate(image_path, existing, out_path)
        return

    if _try_matplotlib_annotate(image_path, existing, out_path):
        return
    _terminal_annotate(image_path, existing, out_path)


def _try_matplotlib_annotate(image_path: str, data, out_path: str) -> bool:
    """Return True if the GUI annotator handled the session."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.image import imread
    except Exception as e:  # pragma: no cover - depends on environment
        print(f"[annotate] matplotlib unavailable ({e}); using terminal input")
        return False

    try:
        img = imread(image_path)
    except Exception as e:
        print(f"[annotate] could not read image with matplotlib ({e}); using terminal input")
        return False

    points = [(a["x"], a["y"], a["direction"]) for a in data["arrows"]]

    fig, ax = plt.subplots()
    ax.imshow(img)
    ax.set_title(
        "Click an arrow, then press U/D/L/R for its direction. "
        "'s' save, 'u' undo last, 'q' quit."
    )
    scatter = ax.scatter([p[0] for p in points], [p[1] for p in points], c="red", s=40)

    def redraw():
        if points:
            scatter.set_offsets([(p[0], p[1]) for p in points])
        else:
            scatter.set_offsets(np.zeros((0, 2)))
        fig.canvas.draw_idle()

    def onclick(event):
        if event.inaxes is None:
            return
        points.append((int(event.xdata), int(event.ydata), None))
        redraw()

    def onkey(event):
        nonlocal points
        k = event.key
        if k in ("u", "U"):
            if points:
                points.pop()
                redraw()
        elif k in ("s", "S"):
            data["arrows"] = [{"x": x, "y": y, "direction": d} for (x, y, d) in points if d]
            save_annotation(out_path, data)
            print(f"[annotate] saved {len(data['arrows'])} arrows to {out_path}")
        elif k in ("q", "Q"):
            plt.close(fig)
        elif k and k.upper() in VALID_DIRECTIONS and points:
            x, y, _ = points[-1]
            points[-1] = (x, y, k.upper())
            redraw()

    fig.canvas.mpl_connect("button_press_event", onclick)
    fig.canvas.mpl_connect("key_press_event", onkey)
    try:
        # Force window onto the primary monitor so it is visible in the agent environment.
        fig.canvas.manager.window.wm_geometry("+0+0")
        plt.show()
    except Exception as e:  # pragma: no cover - depends on environment
        print(f"[annotate] GUI annotator failed ({e}); using terminal input")
        return False
    return True


def _terminal_annotate(image_path: str, data, out_path: str) -> None:
    import cv2
    img = cv2.imread(image_path)
    dims = f"{img.shape[1]}x{img.shape[0]}" if img is not None else "unknown"

    print(f"Annotating {image_path}")
    print(f"Image dimensions: {dims}")
    print("Enter each arrow as: x y DIRECTION")
    print("  x, y       - integer pixel coordinates")
    print("  DIRECTION  - one of: UP (U), DOWN (D), LEFT (L), RIGHT (R)")
    print("Commands:")
    print("  done       - finish and save annotation")
    print("  undo       - remove the last arrow")
    print("  quit       - abort without saving")
    print("Example: 120 340 UP")
    arrows = list(data["arrows"])
    while True:
        line = input("> ").strip()
        if not line:
            continue
        low = line.lower()
        if low in ("done", "d"):
            break
        if low in ("quit", "q"):
            print("[annotate] aborted, nothing saved")
            return
        if low == "undo":
            if arrows:
                arrows.pop()
                print(f"[annotate] removed last ({len(arrows)} remain)")
            continue
        parts = line.split()
        if len(parts) != 3:
            print("Expected: x y DIRECTION")
            continue
        try:
            x = int(parts[0])
            y = int(parts[1])
        except ValueError:
            print("x and y must be integers")
            continue
        d = parts[2].upper()
        if d not in VALID_DIRECTIONS:
            print(f"direction must be one of {sorted(VALID_DIRECTIONS)}")
            continue
        arrows.append({"x": x, "y": y, "direction": d})
        print(f"[annotate] added ({x}, {y}) {d}  ({len(arrows)} total)")

    data["arrows"] = arrows
    save_annotation(out_path, data)
    print(f"[annotate] saved {len(arrows)} arrows to {out_path}")
