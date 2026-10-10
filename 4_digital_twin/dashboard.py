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
            X_scaled = X_input * s_scale + s_min # Doğru Scikit-Learn MinMaxScaler Formülü
            
            # Modelden Çıktı Al (Sigmoid ile 0-1 arası tahmin edilir, 32 ile çarpılır)
            kisi_pred, klima_pred = model.predict(X_scaled, verbose=0)
            ai_tahmini_kisi = max(0, int(round(kisi_pred[0][0] * 32.0)))
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
        # İdeal aralık 22.5 - 24.0
        sicaklik_val = anlik_durum['Sicaklik']
        durum_metni = "İdeal" if 22.5 <= sicaklik_val <= 24.0 else ("Sıcak" if sicaklik_val > 24.0 else "Soğuk")
        
        # Son 60 saniyelik (1 dakika) termal eğim / değişim hızını hesapla
        gecmis_adim = min(60, len(df))
        if gecmis_adim > 1:
            sicaklik_farki = df['Sicaklik'].iloc[-1] - df['Sicaklik'].iloc[-gecmis_adim]
            dakika_carpani = 60.0 / gecmis_adim
            hiz = sicaklik_farki * dakika_carpani
            
            if hiz > 0.04:
                delta_str = f"+{hiz:.2f} °C/dk (Isınıyor 🔥)"
            elif hiz < -0.04:
                delta_str = f"{hiz:.2f} °C/dk (Soğuyor ❄️)"
            else:
                delta_str = "0.00 °C/dk (Dengede ⚖️)"
        else:
            delta_str = "Hesaplanıyor..."
            
        st.metric(f"Sıcaklık ({durum_metni})", f"{sicaklik_val:.1f} °C", delta=delta_str, delta_color="off")
    with col4:
        st.metric("Nem", f"% {anlik_durum['Nem']}")

    st.divider()

    # --- YENİ: DİNAMİK SINIF HARİTASI VE GÖLGELEME GÖRSELİ ---
    st.subheader("🗺️ Canlı Sınıf Haritası (Oturma Düzeni ve Radar Gölgelenmesi)")
    st.caption("Her kutucuk bir sırayı temsil eder. 🔴=Dolu, ⚪️=Boş. Kırmızı renk tonu ve içindeki sayı, o sıradan Radara giden net Enerjiyi gösterir. Arkalara geçtikçe veya önünüz doldukça enerjinin nasıl sönümlendiğini (Gölgelendiğini) görebilirsiniz.")
    
    try:
        live_path = os.path.join(os.path.dirname(__file__), '..', 'live_classroom.json')
        if os.path.exists(live_path):
            with open(live_path, "r") as f:
                live_data = json.load(f)
                kisi_matrisi = live_data["matrix"]
                gorsel_enerjiler = live_data["energies"]
                
            html_str = "<div style='max-width: 520px; margin: auto;'>"
            html_str += "<div style='background-color: #2e7d32; color: white; text-align: center; padding: 10px; border-radius: 6px; font-weight: bold; margin-bottom: 12px;'>📡 RADAR & TAHTA (ÖN TARAF) 🧑‍🏫</div>"
            html_str += "<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;'>"
            for r in range(8):
                for c in range(4):
                    if kisi_matrisi[r][c] == 1:
                        enerji = gorsel_enerjiler[r][c]
                        opacity = max(0.25, min(1.0, enerji / 25.0))
                        bg_color = f"rgba(220, 53, 69, {opacity})"
                        html_str += f"<div style='background-color: {bg_color}; padding: 10px; text-align: center; border-radius: 8px; color: white;'><div style='font-size: 16px;'>🧑‍🎓</div><div style='font-size: 11px; font-weight: bold; margin-top: 3px;'>📶 {enerji}</div></div>"
                    else:
                        html_str += f"<div style='background-color: #f8f9fa; border: 1px dashed #ced4da; padding: 10px; text-align: center; border-radius: 8px; color: #adb5bd;'><div style='font-size: 16px;'>🪑</div><div style='font-size: 11px; margin-top: 3px;'>Boş</div></div>"
            html_str += "</div>"
            html_str += "<div style='background-color: #555; color: white; text-align: center; padding: 8px; border-radius: 6px; font-weight: bold; margin-top: 12px;'>🚪 ARKA SIRA & KAPI (EN UZAK)</div>"
            html_str += "</div><br>"
            st.markdown(html_str, unsafe_allow_html=True)
    except Exception as e:
        st.write(f"Sınıf haritası yüklenirken hata: {e}")
        
    st.divider()

    # --- 2. ALT PANEL: GRAFİKLER (TEMİZLENMİŞ VE GELİŞTİRİLMİŞ TRENDLER) ---
    st.subheader("📈 Gerçek Zamanlı Termodinamik & Otonom Klima Yanıtı")
    st.caption("Son 60 saniyelik dinamik sistem tepkisi (Gereksiz radar çubuk grafiği kaldırılarak haritaya entegre edilmiştir)")

    son_veriler = df.tail(60).copy()
    ac_col = 'Aktif_Klima' if 'Aktif_Klima' in df.columns else 'Hedef_Klima_Gucu'

    col_trend1, col_trend2 = st.columns(2)

    with col_trend1:
        st.markdown("**🌡️ Sıcaklık Eğrisi (°C)**")
        st.line_chart(son_veriler.set_index('Zaman')[['Sicaklik']], height=250, color="#FF4B4B")

    with col_trend2:
        st.markdown("**❄️ Otonom Klima Gücü Modu (0: Kapalı, 1: Eko, 2: Normal, 3: Turbo)**")
        st.line_chart(son_veriler.set_index('Zaman')[[ac_col]], height=250, color="#0068C9")
        
else:
    st.warning("Veri bekleniyor veya dataset.csv bulunamadı. Simülatörü başlattığınıza emin olun.")

if canli_yayin:
    time.sleep(1)
    st.rerun()