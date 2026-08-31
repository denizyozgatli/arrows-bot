import time
from arrows_bot.adb import connection

def tap(x: int, y: int):
    connection.run_shell(f"input tap {x} {y}")

def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
    connection.run_shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")

def zoom_out():
    """Çift parmakla ekranı küçültme (Pinch In) simülasyonu yapar."""
    print("🔍 Harita uzaklaştırılıyor (Zoom Out)...")
    # Çapraz köşelerden merkeze doğru eşzamanlı swipe atarak pinch simülasyonu yapar
    # ADB'de eşzamanlı multi-touch zor olduğu için arkaplan (&) komutuyla hile yapıyoruz.
    cmd = "input swipe 100 100 500 600 300 & input swipe 900 1100 500 600 300"
    connection.run_shell(cmd)
    time.sleep(1.0)