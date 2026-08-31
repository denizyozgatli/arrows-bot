# Arrows Bot - Matematiksel Graf (Graph Theory) Mimarisi

Bu proje, "Arrows" isimli mobil bulmaca oyununu tam otomatik ve hatasız çözmek için geliştirilmiştir. Bot, ekrandaki pikselleri sürekli tarayan "reaktif" bir model yerine, haritayı tek seferde okuyup matematiksel bir ağaca çeviren "proaktif" bir model kullanır.

## Sistem İşleyişi (3 Ana Aşama)

### Aşama 1: Dijitalleştirme (Digitization - `vision/detector.py`)
1. Oyun başladığında ADB üzerinden tek bir ekran görüntüsü RAM'e çekilir.
2. OpenCV Şablon Eşleme (Template Matching) kullanılarak tahtadaki tüm okların Koordinatları (X, Y) ve Yönleri (UP, DOWN, LEFT, RIGHT) tespit edilir.
3. Bu veriler `Arrow` veri sınıfına (dataclass) aktarılır ve OpenCV'nin işi burada biter. (Zor bölümler için `mapper.py` ekranı kaydırarak tek bir dev sanal harita oluşturur).

### Aşama 2: Beyin ve Çözümleme (Graph & Solver - `solver/graph.py`)
1. Hafızaya alınan oklar arasında "Kim kimi engelliyor?" analizi yapılır.
2. Her ok başından, yönü doğrultusunda sanal bir ışın (raycast) fırlatılır. Eğer A okunun ışını, B okunun gövdesiyle veya başıyla kesişiyorsa şu kural yazılır: **"B, A'yı engelliyor" (B -> A).**
3. Bu ilişkiler bir Yönlü İlintisiz Graf (Directed Acyclic Graph - DAG) yapısına dönüştürülür.
4. Topolojik Sıralama (Topological Sorting) algoritması ile graf çözülür ve "Hangi sırayla tıklanırsa hiçbir ok çarpışmaz" sorusunun %100 kesin cevabı bir liste olarak çıkarılır.

### Aşama 3: Kör Yürütme ve Navigasyon (Executor - `executor/bot.py`)
1. Sistem artık ekrana bakmaz veya can kontrolü yapmaz.
2. Çözüm listesindeki okların koordinatlarına sırayla tıklama komutu (`input tap`) gönderir.
3. Eğer sıradaki okun koordinatı fiziksel ekranın dışında kalıyorsa (Hardcore bölümler), `navigator.py` ekranı o koordinata kaydıracak (swipe) vektörü hesaplar, kaydırır ve tıklar.