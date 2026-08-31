import cv2
import numpy as np
from arrows_bot.adb import connection

def get_screenshot_cv2() -> np.ndarray | None:
    """Ekranı diske yazmadan doğrudan RAM'e alır."""
    try:
        raw_png = connection.screencap()
        if not raw_png: return None
        image_array = np.frombuffer(raw_png, dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except Exception:
        return None