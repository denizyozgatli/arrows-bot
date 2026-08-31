import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Arrow:
    id: int
    head: Tuple[int, int]
    direction: str
    tap_point: Tuple[int, int]
    offset: int  # Okun merkezinden ucuna olan piksel mesafesi

class ArrowDetector:
    def __init__(self):
        self.templates = self._build_arrow_templates()

    def _build_arrow_templates(self):
        w, h = 23, 23
        templates = {}
        t_up = np.zeros((h, w), dtype=np.uint8)
        pts = np.array([[w // 2, 2], [3, h - 4], [w - 4, h - 4]], np.int32)
        cv2.fillPoly(t_up, [pts], 255)
        cv2.line(t_up, (w // 2, h - 4), (w // 2, h - 1), 255, thickness=3)
        
        templates['UP'] = t_up
        templates['RIGHT'] = cv2.rotate(t_up, cv2.ROTATE_90_CLOCKWISE)
        templates['DOWN'] = cv2.rotate(t_up, cv2.ROTATE_180)
        templates['LEFT'] = cv2.rotate(t_up, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return templates

    def preprocess_board(self, image: np.ndarray) -> np.ndarray:
        h, w, _ = image.shape
        b, g, r = image[:, :, 0], image[:, :, 1], image[:, :, 2]
        mask = ((b > 150) & (g > 140) & (r > 140)).astype(np.uint8) * 255
        mask[:int(h * 0.11), :] = 0
        mask[int(h * 0.89):, :] = 0
        return mask

    def quick_check_lives(self, image: np.ndarray) -> int:
        h, w, _ = image.shape
        roi = image[int(h * 0.05):int(h * 0.12), int(w * 0.3):int(w * 0.7)]
        r, g, b = roi[:, :, 2], roi[:, :, 1], roi[:, :, 0]
        red_pixels = np.sum((r > 160) & (g < 100) & (b < 100))
        
        if red_pixels > 900: return 3
        elif red_pixels > 400: return 2
        elif red_pixels > 80: return 1
        return 0

    def extract_arrows(self, binary_mask: np.ndarray) -> List[Arrow]:
        candidates = []
        scales = [0.6, 0.8, 1.0] 
        
        for scale in scales:
            for direction, tmpl in self.templates.items():
                scaled_tmpl = cv2.resize(tmpl, (0, 0), fx=scale, fy=scale)
                th, tw = scaled_tmpl.shape
                res = cv2.matchTemplate(binary_mask, scaled_tmpl, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= 0.65)
                for pt in zip(*loc[::-1]):
                    candidates.append((res[pt[1], pt[0]], (pt[0] + tw // 2, pt[1] + th // 2), direction, th))

        candidates.sort(key=lambda x: x[0], reverse=True)
        arrows = []
        visited = []
        idx = 1

        for score, (cx, cy), direction, th in candidates:
            if any(abs(cx - vx) < 15 and abs(cy - vy) < 15 for vx, vy in visited):
                continue
            
            # Okun kendi gövdesini yanlışlıkla engel sanmamak için kafasından güvenli bir çıkış noktası hesaplıyoruz (+4 piksel)
            safe_offset = int(th / 2) + 4 
            arrows.append(Arrow(id=idx, head=(cx, cy), direction=direction, tap_point=(cx, cy), offset=safe_offset))
            visited.append((cx, cy))
            idx += 1

        return arrows