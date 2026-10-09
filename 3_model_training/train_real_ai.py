import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout, Concatenate
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import json
import os
import random

print("1. Yeni fizik kurallarıyla 10.000 satırlık hiper-gerçekçi veri üretiliyor...")
# Generate data logic (copying new physics from simulator)
DIŞ_SICAKLIK = 28.0
IDEAL_SICAKLIK_MIN = 22.5
IDEAL_SICAKLIK_MAX = 24.0
gercek_kisi = 0
hedef_kisi = 0
co2 = 450.0
sicaklik = 23.0
nem = 40.0
aktif_klima_gucu = 0
son_klima_degisim_zamani = 0

data = []
co2_gecmisi = [co2] * 10

for dongu_sayaci in range(10000):
    if dongu_sayaci % 300 == 0:
        hedef_kisi = random.choice([0, 5, 12, 20, 30])
        cam_acik = random.choice([True, False, False, False]) # %25 cam açık
    if dongu_sayaci % 3 == 0:
        if gercek_kisi < hedef_kisi: gercek_kisi += 1
        elif gercek_kisi > hedef_kisi: gercek_kisi -= 1

    teorik_hedef = 0
    if gercek_kisi > 0:
        if sicaklik > IDEAL_SICAKLIK_MAX + 1.5: teorik_hedef = 3
        elif sicaklik > IDEAL_SICAKLIK_MAX: teorik_hedef = 2
        elif sicaklik > IDEAL_SICAKLIK_MIN and co2 > 1000.0: teorik_hedef = 1
        else: teorik_hedef = 0

    if aktif_klima_gucu != teorik_hedef and (dongu_sayaci - son_klima_degisim_zamani) > 60:
        aktif_klima_gucu = teorik_hedef
        son_klima_degisim_zamani = dongu_sayaci

    yaltim_carpani = 0.001 if cam_acik else 0.0002
    isi_sizintisi = (DIŞ_SICAKLIK - sicaklik) * yaltim_carpani
    insan_isisi = gercek_kisi * 0.0005
    klima_sogutmasi = 0
    if aktif_klima_gucu == 1: klima_sogutmasi = 0.002
    elif aktif_klima_gucu == 2: klima_sogutmasi = 0.005
    elif aktif_klima_gucu == 3: klima_sogutmasi = 0.010
    if cam_acik: klima_sogutmasi *= 0.5 
    sicaklik += isi_sizintisi + insan_isisi - klima_sogutmasi

    co2_uretimi = gercek_kisi * 0.4
    klima_temizlemesi = (aktif_klima_gucu * 0.3) if aktif_klima_gucu > 0 else 0
    dogal_sizinti = (co2 - 400.0) * (0.02 if cam_acik else 0.0005) 
    co2 += co2_uretimi - klima_temizlemesi - dogal_sizinti
    co2 = max(400.0, co2)
    co2_gecmisi.pop(0)
    co2_gecmisi.append(co2)
    co2_egimi = co2_gecmisi[-1] - co2_gecmisi[0]

    nem += (gercek_kisi * 0.01) - (aktif_klima_gucu * 0.05)
    if cam_acik: nem += (45.0 - nem) * 0.01
    nem = max(30.0, min(70.0, nem))

    move_gates = [0] * 8
    stat_gates = [0] * 8
    if gercek_kisi > 0:
        aktif_sira = int((gercek_kisi / 30.0) * 8) + 1 
        aktif_sira = max(1, min(8, aktif_sira))
        for i in range(aktif_sira):
            move_gates[i] = random.randint(15, 50) + int(gercek_kisi * 1.5)
            stat_gates[i] = random.randint(30, 80) + int(gercek_kisi * 1.5)

    okunan_sicaklik = sicaklik + random.gauss(0, 0.05)
    okunan_nem = nem + random.gauss(0, 0.3)
    okunan_co2 = co2 + random.gauss(0, 3.0)
    move_gates = [max(0, min(100, int(g + random.gauss(0, 5)))) for g in move_gates]
    stat_gates = [max(0, min(100, int(g + random.gauss(0, 8)))) for g in stat_gates]

    row = move_gates + stat_gates + [round(co2_egimi, 2), round(okunan_sicaklik, 3), round(okunan_nem, 2)]
    data.append([row, gercek_kisi, teorik_hedef])

print("2. Veri hazır, Model Eğitiliyor...")
X = np.array([r[0] for r in data])
y_kisi = np.array([r[1] for r in data])
y_klima = np.array([r[2] for r in data])

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# Scaler parametrelerini JSON'a kaydet (Streamlit okuyabilsin diye)
scaler_params = {
    "min": scaler.data_min_.tolist(),
    "scale": scaler.scale_.tolist()
}
with open('3_Model_Egitimi/scaler.json', 'w') as f:
    json.dump(scaler_params, f)

X_train, X_test, y_kisi_train, y_kisi_test, y_klima_train, y_klima_test = train_test_split(
    X_scaled, y_kisi, y_klima, test_size=0.2, random_state=42)

inputs = Input(shape=(X_train.shape[1],), name="sensor_inputs")
x1 = Dense(32, activation='relu')(inputs)
x1 = Dropout(0.2)(x1)
x1 = Dense(16, activation='relu')(x1)
kisi_ciktisi = Dense(1, activation='relu', name="kisi_tahmini")(x1)

sicaklik_nem = inputs[:, -2:] 
birlestirilmis = Concatenate()([kisi_ciktisi, sicaklik_nem])
x2 = Dense(16, activation='relu')(birlestirilmis)
klima_ciktisi = Dense(4, activation='softmax', name="klima_karari")(x2)

model = Model(inputs=inputs, outputs=[kisi_ciktisi, klima_ciktisi])
model.compile(optimizer='adam', loss={'kisi_tahmini': 'mse', 'klima_karari': 'sparse_categorical_crossentropy'}, loss_weights={'kisi_tahmini': 1.0, 'klima_karari': 2.0}, metrics={'klima_karari': 'accuracy'})

model.fit(X_train, {'kisi_tahmini': y_kisi_train, 'klima_karari': y_klima_train}, epochs=15, batch_size=32, verbose=0)

model.save('3_Model_Egitimi/ai_ajani.keras')
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
with open('3_Model_Egitimi/ai_ajani.tflite', 'wb') as f:
    f.write(tflite_model)

print("3. Eğitim Tamam! Model ve Scaler kaydedildi.")
