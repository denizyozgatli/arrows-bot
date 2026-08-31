import numpy as np
import cv2
from typing import List
from arrows_bot.vision.detector import Arrow

class GraphSolver:
    def solve(self, mask: np.ndarray, arrows: List[Arrow]) -> List[Arrow]:
        safe_to_shoot = []
        h, w = mask.shape
        
        for arrow in arrows:
            cx, cy = int(arrow.head[0]), int(arrow.head[1])
            w_band = 1  # Işını ince çizgilerden kaçırmamak için 3 piksel kalınlığında atıyoruz
            blocked = False
            
            # 1. Merkezden ekranın sonuna kadar olan koridoru 1D (tek boyutlu) bir diziye çevir
            if arrow.direction == 'UP':
                band = mask[0 : cy+1, max(0, cx-w_band) : min(w, cx+w_band+1)]
                ray = np.max(band, axis=1)[::-1] # Ucu 0. index olacak şekilde ters çevir
            elif arrow.direction == 'DOWN':
                band = mask[cy : h, max(0, cx-w_band) : min(w, cx+w_band+1)]
                ray = np.max(band, axis=1)
            elif arrow.direction == 'LEFT':
                band = mask[max(0, cy-w_band) : min(h, cy+w_band+1), 0 : cx+1]
                ray = np.max(band, axis=0)[::-1]
            elif arrow.direction == 'RIGHT':
                band = mask[max(0, cy-w_band) : min(h, cy+w_band+1), cx : w]
                ray = np.max(band, axis=0)

            # 2. Işını Milim Milim Analiz Et
            zeros = np.where(ray == 0)[0]
            
            if len(zeros) == 0:
                # Eğer ekranın sonuna kadar hiç siyah boşluk yoksa ve bu mesafe 22 pikselden uzunsa
                # ok doğrudan bir duvara yapışık demektir.
                if len(ray) > 22:
                    blocked = True
            else:
                # İlk siyah boşluğu (okun kafasından çıktığımız anı) bul
                first_zero_idx = zeros[0]
                
                # Boşluktan sonraki KISMIN TAMAMINA bak
                after_zero = ray[first_zero_idx:]
                
                # Eğer boşluktan sonra HERHANGİ BİR beyaz piksel (engel) varsa:
                if np.any(after_zero > 0):
                    blocked = True

            if not blocked:
                safe_to_shoot.append(arrow)

        return safe_to_shoot