# Akıllı Sınıf Klima Sistemi (Sensor Fusion & Edge AI)

Bu proje, sınıf ortamları için **Enerji Verimliliğini** ve **Hava Kalitesini** optimize etmeyi amaçlayan Otonom bir Yapay Zeka Ajanıdır. Standart klimalardaki mantıksız israfı engellemek için **Sensör Füzyonu (Sensor Fusion)** mimarisiyle çalışır.

## 🚀 Projenin Amacı
Geleneksel klimalar sadece sıcaklığa bakar. Bu sistem ise;
- **LD2410C Radar Sensörü** ile sınıftaki mikro ve makro hareketleri izleyerek *Kişi Sayısı Tahmini* yapar.
- **SCD41 (CO2 Sensörü)** ile oksijen/havasızlık seviyesini (ve artış ivmesini) ölçer.
- **SHT31 (Sıcaklık/Nem Sensörü)** ile gerçek *Hissedilen Sıcaklığı* hesaplar.
- Tüm bu verileri Çok Çıkışlı (Multi-Output) bir **Yapay Zeka (Keras/TensorFlow)** modelinde birleştirerek klimanın hangi modda (0-3) çalışması gerektiğine karar verir.

## 🧠 Sensör Füzyonu Zekası
Eğer cam açılırsa CO2 seviyesi hızla düşer, basit sistemler odanın boşaldığını sanır. Ancak bu model, CO2 düşse bile Radar verilerindeki yaşam belirtisini gördüğü an **"Sınıf hala kalabalık, sadece cam açıldı"** çıkarımını yapacak kadar akıllıdır.

Ayrıca sistemin klimayı yönetme önceliği **Termal Konfordur (Hipotermi Koruması)**. İçerisi havasız (yüksek CO2) olsa dahi oda soğuduysa klimayı zorlamaz, sadece **Kırmızı Işıklı Alarm** vererek insanlardan camları açmasını ister (Çünkü standart klimalar taze hava üretemez).

## 📂 Klasör Yapısı
- `1_hardware/`: C++ ile yazılmış ESP32-S3 sensör okuma ve Edge AI (TFLite Micro) çalıştırma kodları.
- `2_data_collection/`: Fiziksel termodinamik kurallarıyla çalışan Python tabanlı "Simülatör".
- `3_model_training/`: 10.000 satırlık verinin Keras ile eğitildiği ve TFLite formatına çevrildiği Jupyter Notebook.
- `4_digital_twin/`: Sistem sensörlerini canlı izleyip simülatördeki dünyayı manipüle edebildiğiniz Streamlit arayüzü.

## 🛠 Kurulum (Takım Arkadaşları İçin)
Projeyi kendi bilgisayarlarında çalıştırmak isteyen takım arkadaşlarınız terminalde şu komutları sırasıyla çalıştırmalıdır (Bilgisayarlarında Python yüklü olmalıdır):

1. Projeyi bilgisayarınıza indirin:
   ```bash
   git clone https://github.com/IsaEfee/AI_HVAC_PROJECT.git
   cd AI_HVAC_PROJECT
   ```
2. Gerekli yapay zeka ve arayüz kütüphanelerini yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 Kullanım (Dijital İkiz)
Kendi bilgisayarınızda simülasyonu başlatmak için 2 ayrı terminal açın:
1. Terminal: `python 2_data_collection/simulator.py` (Dünyanın fizik kurallarını başlatır)
2. Terminal: `streamlit run 4_digital_twin/dashboard.py` (Dijital ikiz panosunu açar)
