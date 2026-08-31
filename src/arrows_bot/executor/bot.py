import time
from arrows_bot.adb import capture, input as adb_input
from arrows_bot.vision.detector import ArrowDetector
from arrows_bot.solver.graph import GraphSolver

class BotExecutor:
    def __init__(self):
        self.detector = ArrowDetector()
        self.solver = GraphSolver()

    def execute_blind_run(self, max_waves=500):
        print("🚀 Gerçek Zamanlı Canlı Takip Modu Başlatıldı...")
        print("👉 Lütfen haritayı elinizle en küçük hale (zoom-out) getirin!")
        
        for i in range(5, 0, -1):
            print(f"⏳ Başlamasına {i} saniye...")
            time.sleep(1)
            
        print("📸 Harita kilitlendi, TEKLİ ATIŞ ve canlı tarama başlıyor!")

        for wave in range(max_waves):
            # 1. HER ADIMDA SIFIRDAN YENİ EKRAN GÖRÜNTÜSÜ AL
            frame = capture.get_screenshot_cv2()
            if frame is None:
                continue

            lives = self.detector.quick_check_lives(frame)
            if lives == 0:
                print("🛑 DİKKAT: Can bitti veya menü ekranı geldi. İşlem durduruluyor.")
                break

            # 2. YENİ GÖRÜNTÜYE GÖRE STRATEJİ ÜRET
            mask = self.detector.preprocess_board(frame)
            arrows = self.detector.extract_arrows(mask)
            
            if len(arrows) == 0:
                print("🎉 Ekranda hiç ok kalmadı! Bölüm başarıyla temizlendi.")
                break

            sequence = self.solver.solve(mask, arrows)
            
            if not sequence:
                print("⚠️ Engelsiz ok bulunamadı. Tahtanın oturması bekleniyor...")
                time.sleep(1.0)
                continue

            # 3. LİSTEDEKİ SADECE İLK OKU FIRLAT VE DÖNGÜYÜ KIR!
            best_arrow = sequence[0]
            tx, ty = best_arrow.tap_point
            
            print(f"🌊 Dalga {wave + 1}: Sadece tek bir ok fırlatılıyor -> ({tx}, {ty})")
            adb_input.tap(tx, ty)
            
            # Okun ekrandan çıkması ve fizik motorunun durulması için bekle
            time.sleep(1.2)
            
            # DÖNGÜ BAŞA DÖNER VE BİR SONRAKİ ADIM İÇİN ANINDA YENİ EKRAN GÖRÜNTÜSÜ ALINIR

        print("🏁 İşlem sonlandı.")