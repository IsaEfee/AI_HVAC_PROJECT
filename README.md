# 🎓 Akıllı Sınıf & Otonom HVAC Yönetimi (Sensor Fusion & Edge AI)

Bu proje; eğitim kurumları ve dersliklerde **enerji verimliliğini**, **termal konforu** ve **iç ortam hava kalitesini (IAQ)** maksimize etmek amacıyla geliştirilmiş çok girdili ve çok çıkışlı bir **Uç Yapay Zeka (Edge AI)** ve **Dijital İkiz (Digital Twin)** sistemidir.

Geleneksel HVAC (klima) sistemleri yalnızca termostat sıcaklığına bakar. Bu sistem ise **Sensör Füzyonu (Sensor Fusion)** ve derin öğrenme kullanarak sınıftaki insan yoğunluğunu, oturma dağılımını, CO₂ eğimini ve hissedilen sıcaklığı analiz eder; klimayı en optimum güç modunda (0-3) otonom olarak yönetir.

---

## 🌟 Öne Çıkan Mühendislik ve Bilimsel Özellikler

### 1. 📡 2D Line-of-Sight Radar ve Biyometrik Dağılım
- **LD2410C 24GHz FMCW Radar**: 8 farklı kapı (Gate 0-7) üzerinden sınıfı 8 sıra ve 4 sütun (32 koltuk) olarak tarar.
- **Dinamik Gölgeleme (Dynamic Occlusion)**: Arka sıralarda oturan kişilerin önlerindeki öğrenciler tarafından mikrodalga düzeyinde gölgelenmesi fiziksel olarak modellenmiştir.
- **Uzaklık Sönümlemesi**: Ters kare yasasına benzer biçimde arka sıralara giden sinyallerin doğal sönümlenmesi hesaba katılır.

### 2. 🫁 İki Yönlü Sensör Füzyonu (Radar + CO₂)
- **SCD41 NDIR CO₂ Sensörü**: Kalabalık arttıkça insan solunumu kaynaklı CO₂ artış ivmesini ($ppm/dk$) ölçer.
- **Çapraz Doğrulama (Cross-Validation)**: 
  - Radar arkadaki kişileri gölgelediğinde $\rightarrow$ CO₂ ivmesi kalabalığı ele verir.
  - Pencereler açılıp CO₂ temiz hava yüzünden hızla düştüğünde $\rightarrow$ Radar doluluğu teyit eder ve sistem sınıfın boşaldığı yanılgısına düşmez.

### 3. 🌡️ Termodinamik Konfor ve Hipotermi Koruması
- **SHT31 Sıcaklık ve Nem Sensörü**: Hissedilen sıcaklığı hesaplar.
- **İnsan Termal Yükü**: Oturan her bir bireyin ortalama 100 Watt biyolojik ısı yaydığı hesaba katılır; 25 kişi olduğunda oda ısınmadan önce klima proaktif olarak devreye alınır.
- **Kompresör Histerezisi (Deadband)**: Klimanın dur-kalk yaparak motorunu yıpratmasını ve şebekeyi yormasını önlemek için 60 saniyelik minimum anahtarlama koruması uygulanmıştır.

---

## 📊 Yapay Zeka Mimarisi & Başarım Metrikleri

- **Eğitim Verisi**: 25.000 satırlık kesintisiz (0-32 kişi aralığında pürüzsüz) termodinamik ve radar veri seti.
- **Model Tipi**: Çok Çıkışlı Derin Yapay Sinir Ağı (Multi-Output Deep Neural Network).
- **Overfitting Önleme**: Dropout (%10), Early Stopping ve Train/Val/Test (%80/%10/%10) ayrımı.
- **Çıkışlar**:
  1. `Kişi Sayısı Tahmini` (Sigmoid normalize edilmiş kesintisiz regresyon)
  2. `Klima Modu Kararı` (Softmax 4-Sınıflı Sınıflandırma: 0=Kapalı, 1=Eko, 2=Normal, 3=Maksimum)

### 📈 Test Seti Doğrulama Sonuçları:
| Metrik | Başarım | Açıklama |
| :--- | :--- | :--- |
| **Kişi Tahmini Hatası (MAE)** | **1.32 Kişi** | 32 kişilik sınıfta neredeyse hatasız tahmin |
| **Klima Kararı Doğruluğu (Accuracy)** | **%95.56** | Karmaşık sıcaklık-doluluk koşullarında doğru mod seçimi |
| **Edge AI Uyumluluğu** | **Tam Uyumlu** | ESP32-S3 için `ai_agent.tflite` (TFLite Micro) hazır |

---

## 🗂️ Klasör Yapısı

```text
AI_HVAC_PROJECT/
├── 1_hardware/                  # ESP32-S3 C++ PlatformIO donanım kaynak kodları
├── 2_data_collection/           # Gerçekçi 2D fizik motoru ve simülatör
│   ├── simulator.py             # Saniyede 1 veri üreten fizik motoru
│   └── dataset.csv              # Canlı veri akış kütüğü
├── 3_model_training/            # Yapay Zeka eğitim hattı
│   ├── generate_data.py         # 25.000 satırlık zengin sentetik veri üreticisi
│   ├── train_model.py           # Keras ve TFLite model eğitim komut dosyası
│   ├── model_training.ipynb     # Adım adım akademik analiz ve görselleştirme notebook'u
│   ├── ai_agent.keras           # Eğitilmiş üretim modeli (Dijital İkiz için)
│   ├── ai_agent.tflite          # Uç birim mikrodenetleyici modeli (ESP32 için)
│   └── scaler.json              # Özellik normalizasyon katsayıları
├── 4_digital_twin/              # Streamlit tabanlı canlı interaktif kontrol panosu
│   └── dashboard.py             # Canlı 2D sınıf haritası, grafikler ve simülasyon kontrolü
├── requirements.txt             # Gerekli Python kütüphaneleri
└── README.md                    # Proje dokümantasyonu
```

---

## 🚀 Hızlı Başlangıç (Hocanız ve Değerlendiriciler İçin)

Projeyi bilgisayarınızda **1 dakika içinde** canlı olarak çalıştırmak için şu adımları takip edebilirsiniz:

### 1. Depoyu Klonlayın ve Bağımlılıkları Yükleyin
```bash
git clone https://github.com/IsaEfee/AI_HVAC_PROJECT.git
cd AI_HVAC_PROJECT
pip install -r requirements.txt
```

### 2. Dijital İkizi Başlatın (Yan Yana 2 Terminal Açın)

* **1. Terminal (Fizik Simülatörü):**
  ```bash
  python 2_data_collection/simulator.py
  ```
  *(Sınıftaki termodinamik, biyolojik ısı, CO₂ ve 2D radar fizik motorunu başlatır.)*

* **2. Terminal (Canlı Kontrol Paneli & Dijital İkiz):**
  ```bash
  streamlit run 4_digital_twin/dashboard.py
  ```
  *(Açılan tarayıcı ekranında 2D Sınıf Haritasını, radara giden sinyalleri, Yapay Zeka tahminlerini ve klima kararlarını canlı izleyebilir; sol panelden kişi sayısını ve cam durumunu değiştirerek sistemi test edebilirsiniz.)*

---

## 👨‍💻 Geliştirici & Lisans
* **Geliştirici:** İsa Efe Eroğlu
* **Lisans:** MIT License
