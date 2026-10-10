import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import json

print("1. Veri seti yükleniyor (25.000 satır)...")
df = pd.read_csv("3_model_training/training_dataset.csv")

radar_cols = [col for col in df.columns if "Move" in col or "Stat" in col]
X = df[radar_cols + ["CO2_Egimi", "Sicaklik", "Nem"]].values

# Kişi sayısı 0-32 arasında olduğu için 32.0 ile bölerek [0.0, 1.0] sigmoid aralığına normalize ediyoruz
y_kisi = df["Gercek_Kisi_Sayisi"].values / 32.0
y_klima = df["Hedef_Klima_Gucu"].values

# Train/Val/Test Split (Overfitting kontrolü için 3'lü ayrım)
X_train, X_temp, y_kisi_train, y_kisi_temp, y_klima_train, y_klima_temp = train_test_split(
    X, y_kisi, y_klima, test_size=0.2, random_state=42
)
X_val, X_test, y_kisi_val, y_kisi_temp, y_klima_val, y_klima_temp = train_test_split(
    X_temp, y_kisi_temp, y_klima_temp, test_size=0.5, random_state=42
)

# Girdi Özelliklerini Ölçekleme
scaler_x = MinMaxScaler()
X_train_scaled = scaler_x.fit_transform(X_train)
X_val_scaled = scaler_x.transform(X_val)
X_test_scaled = scaler_x.transform(X_test)

with open("3_model_training/scaler.json", "w") as f:
    json.dump({"min": scaler_x.min_.tolist(), "scale": scaler_x.scale_.tolist()}, f)

print("2. Derin Öğrenme Modeli İnşa Ediliyor (Overfitting önleyici Dropout mimarisi)...")
input_layer = tf.keras.layers.Input(shape=(X_train_scaled.shape[1],), name="sensor_inputs")

# Ortak Gövde
x = tf.keras.layers.Dense(64, activation='relu')(input_layer)
x = tf.keras.layers.Dropout(0.1)(x) # Overfitting önleme
x = tf.keras.layers.Dense(32, activation='relu')(x)
x = tf.keras.layers.Dropout(0.1)(x) # Overfitting önleme

# Çıkış 1: Kişi Sayısı Tahmini (Sigmoid ile 0-1 arası pürüzsüz sürekli regresyon)
out_kisi = tf.keras.layers.Dense(1, activation='sigmoid', name='kisi_tahmini')(x)

# Çıkış 2: Otonom Klima Modu Kararı (Softmax 4 Sınıf)
x_klima = tf.keras.layers.Dense(16, activation='relu')(x)
out_klima = tf.keras.layers.Dense(4, activation='softmax', name='klima_karari')(x_klima)

model = tf.keras.models.Model(inputs=input_layer, outputs=[out_kisi, out_klima])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss={'kisi_tahmini': 'mse', 'klima_karari': 'sparse_categorical_crossentropy'},
    loss_weights={'kisi_tahmini': 1.0, 'klima_karari': 1.0},
    metrics={'kisi_tahmini': 'mae', 'klima_karari': 'accuracy'}
)

print("3. Model Eğitiliyor...")
early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)

model.fit(
    X_train_scaled, 
    {'kisi_tahmini': y_kisi_train, 'klima_karari': y_klima_train},
    validation_data=(X_val_scaled, {'kisi_tahmini': y_kisi_val, 'klima_karari': y_klima_val}),
    epochs=50, 
    batch_size=32, 
    verbose=0,
    callbacks=[early_stop]
)

print("4. Test Seti Üzerinde Doğrulama (Genelleme Gücü)...")
test_preds = model.predict(X_test_scaled, verbose=0)
kisi_test_preds = test_preds[0] * 32.0
kisi_test_true = y_kisi_temp * 32.0

mae = np.mean(np.abs(kisi_test_preds.flatten() - kisi_test_true))
klima_acc = np.mean(np.argmax(test_preds[1], axis=1) == y_klima_temp) * 100

print(f"--> Test Seti Ortalama Kişi Hatası (MAE): {mae:.2f} kişi!")
print(f"--> Test Seti Klima Kararı Doğruluğu (Accuracy): %{klima_acc:.2f}!")

# Modelleri Kaydet
model.save("3_model_training/ai_agent.keras")

# TFLite Dönüştürme (Mikrodenetleyici ESP32 İçin)
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
with open("3_model_training/ai_agent.tflite", "wb") as f:
    f.write(tflite_model)

print("5. Modeller başarıyla 'ai_agent.keras' ve 'ai_agent.tflite' olarak kaydedildi!")
