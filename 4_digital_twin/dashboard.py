import streamlit as st
import pandas as pd
import time
import os

# Sayfa Ayarları
st.set_page_config(page_title="Akıllı Sınıf Dijital İkiz", layout="wide")
st.title("🎓 Akıllı Sınıf & Otonom HVAC - Canlı Dijital İkiz Panosu")

# Veri dosyasının yolu
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '2_data_collection', 'dataset.csv')

# Sol menüye canlı yenileme butonu ekleme
canli_yayin = st.sidebar.toggle("🔴 Canlı Veri Akışını Başlat", value=True)

import json

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎮 Simülatör Kontrolü")
st.sidebar.caption("Oda koşullarını canlı olarak değiştirin.")

ayarlar_dosyasi = os.path.join(os.path.dirname(__file__), '..', '2_data_collection', 'sim_settings.json')

# Session state'te ayarları tutalım (Sadece ilk çalışmada veya dosya güncellendiğinde okumak için)
if 'mevcut_ayarlar' not in st.session_state:
    st.session_state.mevcut_ayarlar = {
        "hedef_kisi": 0,
        "oturma_duzeni": "Karışık",
        "dis_sicaklik": 28.0,
        "cam_acik": False,
        "force_sicaklik": None
    }
    # İlk yüklemede dosyadan oku
    try:
        if os.path.exists(ayarlar_dosyasi):
            with open(ayarlar_dosyasi, "r") as f:
                st.session_state.mevcut_ayarlar.update(json.load(f))
    except Exception:
        pass

# Kullanıcının oynayacağı arayüz değişkenleri
ayarlar = st.session_state.mevcut_ayarlar.copy()

# 1. Kişi Kontrolü
col_arti, col_eksi = st.sidebar.columns(2)
with col_arti:
    if st.button("➕ 1 Kişi Girdi"):
        ayarlar["hedef_kisi"] += 1
with col_eksi:
    if st.button("➖ 1 Kişi Çıktı"):
        ayarlar["hedef_kisi"] = max(0, ayarlar["hedef_kisi"] - 1)

ayarlar["hedef_kisi"] = st.sidebar.slider("Hedef Kapasite", 0, 30, ayarlar["hedef_kisi"])

# 2. Oturma Düzeni
ayarlar["oturma_duzeni"] = st.sidebar.selectbox(
    "Öğrenci Oturma Düzeni", 
    ["Karışık", "Ön Sıralar", "Arka Sıralar"],
    index=["Karışık", "Ön Sıralar", "Arka Sıralar"].index(ayarlar["oturma_duzeni"])
)

# 3. Çevre Şartları
st.sidebar.markdown("### 🌤️ Çevre Şartları")
ayarlar["dis_sicaklik"] = st.sidebar.slider("Dışarıdaki Hava Sıcaklığı (°C)", -10.0, 45.0, ayarlar["dis_sicaklik"], 0.5)
ayarlar["cam_acik"] = st.sidebar.toggle("🪟 Camlar Açık", value=ayarlar["cam_acik"], key="cam_toggle")

# 4. Anlık Sıcaklık Müdahalesi
st.sidebar.markdown("### 🌡️ Anlık Müdahale")
manuel_sicaklik = st.sidebar.number_input("Sınıf Sıcaklığını Zorla Değiştir", min_value=10.0, max_value=40.0, value=23.0)
if st.sidebar.button("Uygula (Sıcaklığı Değiştir)"):
    ayarlar["force_sicaklik"] = manuel_sicaklik

# Değişiklik varsa dosyaya SADECE O ZAMAN yaz
if ayarlar != st.session_state.mevcut_ayarlar:
    st.session_state.mevcut_ayarlar = ayarlar.copy()
    try:
        with open(ayarlar_dosyasi, "w") as f:
            json.dump(ayarlar, f)
    except Exception:
        pass



# Ajan ayarları hakkında bilgi
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ AI Ajanı Hedefleri")
st.sidebar.markdown("- **İdeal Sıcaklık:** 22.5°C - 24.0°C")
st.sidebar.markdown("- **Enerji Tasarrufu:** Odada kimse yoksa veya koşullar idealse klima kapanır.")
st.sidebar.markdown("- **Kişi Sayısı:** Bilinmiyor (Yalnızca Radar Verisi kullanılıyor).")

def veri_getir():
    try:
        df = pd.read_csv(DATA_PATH)
        return df.tail(60)
    except Exception:
        return None

df = veri_getir()

if df is not None and not df.empty:
    anlik_durum = df.iloc[-1]
    
    # --- 0. AI AJANI KARAR PANELİ (ÖNE ÇIKARILMIŞ) ---
    st.markdown("### 🤖 Otonom AI Ajanı Klima Kararı")
    # Eğer yeni termodinamik simülatör kullanılıyorsa 'Aktif_Klima' sütunu vardır, yoksa 'Hedef_Klima_Gucu' kullanılır.
    klima_gucu = int(anlik_durum.get('Aktif_Klima', anlik_durum.get('Hedef_Klima_Gucu', 0)))

    
    if klima_gucu == 0:
        klima_durum_metni = "KAPALI (Enerji Tasarrufu / İdeal Koşullar)"
        klima_renk = "normal"
    elif klima_gucu == 1:
        klima_durum_metni = "DÜŞÜK GÜÇ (Seviye 1)"
        klima_renk = "inverse" # Uyarı niteliğinde hafif bir renk verebiliriz (Streamlit varsayılanı)
    elif klima_gucu == 2:
        klima_durum_metni = "ORTA GÜÇ (Seviye 2)"
        klima_renk = "inverse"
    else:
        klima_durum_metni = "MAKSİMUM GÜÇ (Seviye 3)"
        klima_renk = "inverse"

    # Klima durumu kartı
    st.info(f"**Aktif Klima Komutu:** {klima_durum_metni}")
    st.divider()

    # --- YAPAY ZEKA TAHMİNİ (GERÇEK TFLITE / KERAS MODELİ ENTEGRASYONU) ---
    # Eğer eğitilmiş model varsa, o anki verileri modele sokup GERÇEK tahmini alalım
    ai_tahmini_kisi = None
    import numpy as np
    
    # Keras ve Scaler dosya yolları (Jupyter Notebook'un ürettiği dosyalar)
    model_path = os.path.join(os.path.dirname(__file__), '..', '3_model_training', 'ai_agent.keras')
    scaler_path = os.path.join(os.path.dirname(__file__), '..', '3_model_training', 'scaler.json')
    
    try:
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            import tensorflow as tf
            # modeli sadece ilk seferde yükleyip st.session_state'te tutabiliriz ama şimdilik basit tutalım
            if 'gercek_ai_modeli' not in st.session_state:
                st.session_state.gercek_ai_modeli = tf.keras.models.load_model(model_path, compile=False)
                with open(scaler_path, 'r') as f:
                    s_data = json.load(f)
                    st.session_state.scaler_min = np.array(s_data['min'])
                    st.session_state.scaler_scale = np.array(s_data['scale'])
            
            model = st.session_state.gercek_ai_modeli
            s_min = st.session_state.scaler_min
            s_scale = st.session_state.scaler_scale
            
            # Modeli besleyecek Girdi (Feature) dizisini hazırla (Notebook'taki sırayla: [Move0-7, Stat0-7, CO2_Egimi, Sicaklik, Nem])
            features = []
            for i in range(8): features.append(anlik_durum[f"Move_G{i}"])
            for i in range(8): features.append(anlik_durum[f"Stat_G{i}"])
            features.extend([anlik_durum["CO2_Egimi"], anlik_durum["Sicaklik"], anlik_durum["Nem"]])
            
            X_input = np.array([features])
            X_scaled = (X_input - s_min) * s_scale # Manuel MinMaxScaler Transform
            
            # Modelden Çıktı Al
            kisi_pred, klima_pred = model.predict(X_scaled, verbose=0)
            ai_tahmini_kisi = max(0, int(round(kisi_pred[0][0])))
            # Arayüzdeki 'Klima Kararı' göstergesini de modelin çıktısıyla değiştirebiliriz
            # klima_gucu = np.argmax(klima_pred[0]) # İsteseniz klima gücünü de gerçek AI'dan alabilirsiniz.
    except Exception as e:
        pass # Kütüphane yoksa veya model henüz eğitilmediyse pass geç

    # --- 1. ÜST PANEL: TEMEL METRİKLER ---
    # HAVALANDIRMA (CO2) ALARMI
    if anlik_durum['CO2'] > 1200.0:
        st.error(f"🚨 **KRİTİK UYARI:** Sınıftaki oksijen seviyesi alarm veriyor (CO2: {int(anlik_durum['CO2'])} ppm). Klima duvar tipi olduğu için CO2'yi düşüremez. Lütfen acilen camları açın!")
    elif anlik_durum['CO2'] > 1000.0:
        st.warning(f"⚠️ **UYARI:** Sınıf havasızlaşmaya başladı (CO2: {int(anlik_durum['CO2'])} ppm). Müsait olduğunuzda havalandırın.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        gercek_kisi = int(anlik_durum.get('Gercek_Kisi_Sayisi', 0))
        
        if ai_tahmini_kisi is not None:
            # Eğitilmiş gerçek yapay zeka modelinin tahmini
            st.metric("AI Doluluk Tahmini (Gerçek Model)", f"~ {ai_tahmini_kisi} Kişi", f"Gerçek: {gercek_kisi}", delta_color="off")
        else:
            # Model yoksa simüle edilmiş gürültülü tahmin (Eski mantık)
            import random
            tahmini_kisi = gercek_kisi
            if gercek_kisi > 0:
                sapma = random.choice([-1, 0, 1])
                tahmini_kisi = max(1, gercek_kisi + sapma)
            st.metric("AI Doluluk Tahmini (Simülasyon)", f"~ {tahmini_kisi} Kişi", f"Gerçek: {gercek_kisi}", delta_color="off")
    with col2:
        st.metric("CO2 Seviyesi", f"{int(anlik_durum['CO2'])} ppm", f"{anlik_durum['CO2_Egimi']:.1f} ppm/dk")
    with col3:
        # İdeal aralık 22.5 - 24.0. Bunu görsel olarak belli edelim.
        sicaklik_val = anlik_durum['Sicaklik']
        st.metric("Sıcaklık", f"{sicaklik_val} °C", 
                  "İdeal" if 22.5 <= sicaklik_val <= 24.0 else ("Sıcak" if sicaklik_val > 24.0 else "Soğuk"),
                  delta_color="off")
    with col4:
        st.metric("Nem", f"% {anlik_durum['Nem']}")

    st.divider()

    # --- 2. ALT PANEL: GRAFİKLER ---
    col_grafik1, col_grafik2 = st.columns(2)

    with col_grafik1:
        st.subheader("Radar Enerji Dağılımı (Sıralara Göre)")
        st.caption("AI ajanı sınıftaki kalabalığı bu profilden çıkarıyor")
        
        hareket = [anlik_durum[f"Move_G{i}"] for i in range(8)]
        statik = [anlik_durum[f"Stat_G{i}"] for i in range(8)]
        
        radar_df = pd.DataFrame({
            "Makro Hareket (Yürüme vs.)": hareket,
            "Mikro Hareket (Nefes, Oturma)": statik
        }, index=[f"Sıra {i}" for i in range(8)])
        
        st.bar_chart(radar_df, color=["#FF4B4B", "#0068C9"])

    with col_grafik2:
        st.subheader("Sıcaklık ve Klima Gücü Trendi")
        st.caption("Son 1 dakikalık değişim (Sıcaklığa karşı Klima Yanıtı)")
        
        ac_col = 'Aktif_Klima' if 'Aktif_Klima' in df.columns else 'Hedef_Klima_Gucu'
        
        st.markdown("**Sıcaklık Trendi (°C)**")
        st.line_chart(df.set_index('Zaman')['Sicaklik'], height=150)
        
        st.markdown("**Aktif Klima Modu (0-3)**")
        st.line_chart(df.set_index('Zaman')[ac_col], height=150)
        
else:
    st.warning("Veri bekleniyor veya dataset.csv bulunamadı. Simülatörü başlattığınıza emin olun.")

if canli_yayin:
    time.sleep(1)
    st.rerun()