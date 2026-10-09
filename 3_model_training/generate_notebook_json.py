import json

cells = []

def add_md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in text.split("\n")[:-1]] + [text.split("\n")[-1]]})

def add_code(text):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [line + "\n" for line in text.split("\n")[:-1]] + [text.split("\n")[-1]]})

add_md("""# Akıllı Sınıf - İki Aşamalı AI Ajanı Eğitimi (Sensör Füzyonu)\nBu notebook'ta Radar ve CO2 verilerini birleştirerek sınıfın doluluğunu tahmin eden, ardından bu tahmin ve sıcaklığa bakarak Klima Gücüne (0-3) karar veren Uçtan Uca (End-to-End) bir model eğiteceğiz.""")

add_code("""import pandas as pd\nimport numpy as np\nimport tensorflow as tf\nfrom tensorflow.keras.models import Model\nfrom tensorflow.keras.layers import Input, Dense, Dropout, Concatenate\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import MinMaxScaler\nimport matplotlib.pyplot as plt\nimport json\n\nprint("Kütüphaneler yüklendi. TensorFlow Versiyonu:", tf.__version__)""")

add_md("""## 1. Veri Setinin Yüklenmesi ve Hazırlanması\nRadar, CO2, Sıcaklık verilerini alacağız.""")

add_code("""df = pd.read_csv("../2_data_collection/dataset.csv")\n\nradar_cols = [col for col in df.columns if "Move" in col or "Stat" in col]\nX = df[radar_cols + ["CO2_Egimi", "Sicaklik", "Nem"]].values\n\ny_kisi = df["Gercek_Kisi_Sayisi"].values\ny_klima = df["Hedef_Klima_Gucu"].values\n\nscaler = MinMaxScaler()\nX_scaled = scaler.fit_transform(X)\n\n# Scaler değerlerini kaydet (Arayüzde gerçek tahmin için)\nwith open('scaler.json', 'w') as f:\n    json.dump({"min": scaler.data_min_.tolist(), "scale": scaler.scale_.tolist()}, f)\n\nX_train, X_test, y_kisi_train, y_kisi_test, y_klima_train, y_klima_test = train_test_split(\n    X_scaled, y_kisi, y_klima, test_size=0.2, random_state=42\n)\n\nprint(f"Eğitim verisi: {X_train.shape[0]} satır. Test verisi: {X_test.shape[0]} satır.")""")

add_md("""## 2. İki Aşamalı Yapay Zeka Mimarisinin Kurulması""")

add_code("""inputs = Input(shape=(X_train.shape[1],), name="sensor_inputs")\n\nx1 = Dense(32, activation='relu')(inputs)\nx1 = Dropout(0.2)(x1)\nx1 = Dense(16, activation='relu')(x1)\nkisi_ciktisi = Dense(1, activation='relu', name="kisi_tahmini")(x1)\n\nsicaklik_nem = inputs[:, -2:] \nbirlestirilmis = Concatenate()([kisi_ciktisi, sicaklik_nem])\n\nx2 = Dense(16, activation='relu')(birlestirilmis)\nklima_ciktisi = Dense(4, activation='softmax', name="klima_karari")(x2)\n\nmodel = Model(inputs=inputs, outputs=[kisi_ciktisi, klima_ciktisi])\n\nmodel.compile(\n    optimizer='adam',\n    loss={'kisi_tahmini': 'mse', 'klima_karari': 'sparse_categorical_crossentropy'},\n    loss_weights={'kisi_tahmini': 1.0, 'klima_karari': 2.0},\n    metrics={'klima_karari': 'accuracy'}\n)\n\nmodel.summary()""")

add_md("""## 3. Modelin Eğitilmesi""")

add_code("""history = model.fit(\n    X_train, \n    {'kisi_tahmini': y_kisi_train, 'klima_karari': y_klima_train},\n    validation_data=(X_test, {'kisi_tahmini': y_kisi_test, 'klima_karari': y_klima_test}),\n    epochs=50,\n    batch_size=32,\n    verbose=1\n)""")

add_md("""## 4. Eğitimi İnceleme ve TFLite Dönüşümü""")

add_code("""plt.plot(history.history['klima_karari_accuracy'], label='Eğitim Başarısı')\nplt.plot(history.history['val_klima_karari_accuracy'], label='Doğrulama Başarısı')\nplt.title('Klima Kararı AI Ajanı Başarısı')\nplt.legend()\nplt.show()\n\n# Hem Keras hem TFLite olarak kaydet (Keras'ı Streamlit kullanacak)\nmodel.save('ai_agent.keras')\n\nconverter = tf.lite.TFLiteConverter.from_keras_model(model)\ntflite_model = converter.convert()\n\nwith open('ai_agent.tflite', 'wb') as f:\n    f.write(tflite_model)\n    \nprint("Modeller kaydedildi!")""")

notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.9"}}, "nbformat": 4, "nbformat_minor": 5}

with open('3_Model_Egitimi/model_egitimi.ipynb', 'w') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)
