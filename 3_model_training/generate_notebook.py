import nbformat as nbf

nb = nbf.v4.new_notebook()

text1 = """\
# Akıllı Sınıf - İki Aşamalı AI Ajanı Eğitimi (Sensör Füzyonu)
Bu notebook'ta Radar ve CO2 verilerini birleştirerek sınıfın doluluğunu tahmin eden, ardından bu tahmin ve sıcaklığa bakarak Klima Gücüne (0-3) karar veren Uçtan Uca (End-to-End) bir model eğiteceğiz.
"""

code1 = """\
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout, Concatenate
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

print("Kütüphaneler yüklendi. TensorFlow Versiyonu:", tf.__version__)
"""

text2 = """\
## 1. Veri Setinin Yüklenmesi ve Hazırlanması
Radar, CO2, Sıcaklık verilerini alacağız.
Hedeflerimiz:
1. `Gercek_Kisi_Sayisi` (Bunu tahmin etmeyi öğreneceğiz - Sensör Füzyonu)
2. `Hedef_Klima_Gucu` (Nihai karar)
"""

code2 = """\
df = pd.read_csv("../2_data_collection/dataset.csv")

# Girdiler (Features)
radar_cols = [col for col in df.columns if "Move" in col or "Stat" in col]
X = df[radar_cols + ["CO2_Egimi", "Sicaklik", "Nem"]].values

# Hedef 1: Kişi Sayısı (Ara Çıktı / Sensör Füzyonu)
y_kisi = df["Gercek_Kisi_Sayisi"].values

# Hedef 2: Klima Gücü (Nihai Karar)
y_klima = df["Hedef_Klima_Gucu"].values

# Verileri Ölçeklendirme
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_kisi_train, y_kisi_test, y_klima_train, y_klima_test = train_test_split(
    X_scaled, y_kisi, y_klima, test_size=0.2, random_state=42
)

print(f"Eğitim verisi: {X_train.shape[0]} satır. Test verisi: {X_test.shape[0]} satır.")
"""

text3 = """\
## 2. İki Aşamalı Yapay Zeka Mimarisinin Kurulması
Burada Multi-Output (Çoklu Çıktılı) bir model tasarlayacağız.
* **Katman 1:** Radar ve CO2 eğimini işleyip *Kişi Yoğunluğunu* tahmin eder.
* **Katman 2:** Bu tahmin edilen yoğunluğu ve Sıcaklık verisini alıp *Klima Gücüne* karar verir.
"""

code3 = """\
# Girdi Katmanı
inputs = Input(shape=(X_train.shape[1],), name="sensor_inputs")

# Yoğunluk Tahmini Ağı (Radar + CO2)
x1 = Dense(32, activation='relu')(inputs)
x1 = Dropout(0.2)(x1)
x1 = Dense(16, activation='relu')(x1)
# Çıktı 1: Kişi Sayısı Tahmini (Regresyon)
kisi_ciktisi = Dense(1, activation='relu', name="kisi_tahmini")(x1)

# İklimlendirme Karar Ağı (Kişi Tahmini + Sıcaklık)
# Girdilerdeki son iki özellik [Sicaklik, Nem]'i ve kisi tahminini birleştiriyoruz
sicaklik_nem = inputs[:, -2:] 
birlestirilmis = Concatenate()([kisi_ciktisi, sicaklik_nem])

x2 = Dense(16, activation='relu')(birlestirilmis)
# Çıktı 2: Klima Gücü (Sınıflandırma: 0, 1, 2, 3)
klima_ciktisi = Dense(4, activation='softmax', name="klima_karari")(x2)

# Modeli Derleme
model = Model(inputs=inputs, outputs=[kisi_ciktisi, klima_ciktisi])

model.compile(
    optimizer='adam',
    loss={'kisi_tahmini': 'mse', 'klima_karari': 'sparse_categorical_crossentropy'},
    loss_weights={'kisi_tahmini': 1.0, 'klima_karari': 2.0}, # Klima kararı daha önemli
    metrics={'klima_karari': 'accuracy'}
)

model.summary()
"""

text4 = """\
## 3. Modelin Eğitilmesi
"""

code4 = """\
history = model.fit(
    X_train, 
    {'kisi_tahmini': y_kisi_train, 'klima_karari': y_klima_train},
    validation_data=(X_test, {'kisi_tahmini': y_kisi_test, 'klima_karari': y_klima_test}),
    epochs=50,
    batch_size=32,
    verbose=1
)
"""

text5 = """\
## 4. Eğitimi İnceleme ve TFLite Dönüşümü
"""

code5 = """\
# Başarı grafiği
plt.plot(history.history['klima_karari_accuracy'], label='Eğitim Başarısı')
plt.plot(history.history['val_klima_karari_accuracy'], label='Doğrulama Başarısı')
plt.title('Klima Kararı AI Ajanı Başarısı')
plt.legend()
plt.show()

# ESP32'de çalışması için TFLite'a dönüştürme
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open('ai_agent.tflite', 'wb') as f:
    f.write(tflite_model)
    
print("Model başarıyla ai_agent.tflite olarak kaydedildi! Artık ESP32'ye yüklenebilir.")
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(text1),
    nbf.v4.new_code_cell(code1),
    nbf.v4.new_markdown_cell(text2),
    nbf.v4.new_code_cell(code2),
    nbf.v4.new_markdown_cell(text3),
    nbf.v4.new_code_cell(code3),
    nbf.v4.new_markdown_cell(text4),
    nbf.v4.new_code_cell(code4),
    nbf.v4.new_markdown_cell(text5),
    nbf.v4.new_code_cell(code5)
]

with open('model_egitimi.ipynb', 'w') as f:
    nbf.write(nb, f)

