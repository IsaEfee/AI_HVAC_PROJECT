import csv
import random
from datetime import datetime, timedelta
import os

DOSYA_ADI = os.path.join(os.path.dirname(__file__), '..', '3_model_training', 'training_dataset.csv')

IDEAL_SICAKLIK_MIN = 22.5
IDEAL_SICAKLIK_MAX = 24.0

gercek_kisi = 0
co2 = 450.0
sicaklik = 23.0
nem = 40.0
aktif_klima_gucu = 0
son_klima_degisim_zamani = 0
co2_egimi = 0.0

header = ["Zaman"]
header += [f"Move_G{i}" for i in range(8)]
header += [f"Stat_G{i}" for i in range(8)]
header += ["Sicaklik", "Nem", "CO2", "CO2_Egimi", "Gercek_Kisi_Sayisi", "Hedef_Klima_Gucu", "Aktif_Klima"]

print("Model eğitimi için GERÇEKÇİ 10.000 satırlık sentetik veri üretiliyor...")

with open(DOSYA_ADI, mode='w', newline='') as dosya:
    yazici = csv.writer(dosya)
    yazici.writerow(header)
    zaman = datetime.now() - timedelta(hours=3)
    co2_gecmisi = [co2] * 10
    kisi_matrisi = [[0]*4 for _ in range(8)]
    son_oturma_duzeni = ""

    for dongu_sayaci in range(10000):
        # 300 saniyede bir senaryo değişir
        if dongu_sayaci % 300 == 0:
            hedef_kisi = random.choice([0, 5, 12, 20, 30])
            dis_sicaklik = random.uniform(15.0, 35.0)
            cam_acik = random.choice([True, False, False])
            oturma_duzeni = random.choice(["Karışık", "Ön Sıralar", "Arka Sıralar"])

        if dongu_sayaci % 3 == 0:
            if gercek_kisi < hedef_kisi: gercek_kisi += 1
            elif gercek_kisi > hedef_kisi: gercek_kisi -= 1

        teorik_hedef = 0
        if gercek_kisi > 0:
            hissedilen_sicaklik = sicaklik + max(0, (nem - 40) * 0.05)
            if hissedilen_sicaklik > IDEAL_SICAKLIK_MAX + 1.5 or (hissedilen_sicaklik > IDEAL_SICAKLIK_MAX + 0.5 and gercek_kisi > 20):
                teorik_hedef = 3 
            elif hissedilen_sicaklik > IDEAL_SICAKLIK_MAX or (hissedilen_sicaklik > IDEAL_SICAKLIK_MIN + 0.5 and gercek_kisi > 8):
                teorik_hedef = 2
            elif hissedilen_sicaklik > IDEAL_SICAKLIK_MIN:
                teorik_hedef = 1
            else:
                teorik_hedef = 0
                
            if sicaklik < 22.0 and teorik_hedef > 1:
                teorik_hedef = 1
            if sicaklik < 20.5:
                teorik_hedef = 0

        if aktif_klima_gucu != teorik_hedef and (dongu_sayaci - son_klima_degisim_zamani) > 60:
            aktif_klima_gucu = teorik_hedef
            son_klima_degisim_zamani = dongu_sayaci

        yaltim_carpani = 0.001 if cam_acik else 0.0002
        isi_sizintisi = (dis_sicaklik - sicaklik) * yaltim_carpani
        insan_isisi = gercek_kisi * 0.0005
        klima_sogutmasi = 0
        if aktif_klima_gucu == 1: klima_sogutmasi = 0.005
        elif aktif_klima_gucu == 2: klima_sogutmasi = 0.015
        elif aktif_klima_gucu == 3: klima_sogutmasi = 0.030
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

        if oturma_duzeni != son_oturma_duzeni:
            kisi_matrisi = [[0]*4 for _ in range(8)]
            mevcut_kisi = 0
            son_oturma_duzeni = oturma_duzeni
        else:
            mevcut_kisi = sum(sum(row) for row in kisi_matrisi)

        while mevcut_kisi < gercek_kisi:
            bos_koltuklar = [(r, c) for r in range(8) for c in range(4) if kisi_matrisi[r][c] == 0]
            if not bos_koltuklar: break
            if oturma_duzeni == "Ön Sıralar": secilen = min(bos_koltuklar, key=lambda x: x[0])
            elif oturma_duzeni == "Arka Sıralar": secilen = max(bos_koltuklar, key=lambda x: x[0])
            else: secilen = random.choice(bos_koltuklar)
            kisi_matrisi[secilen[0]][secilen[1]] = 1
            mevcut_kisi += 1

        while mevcut_kisi > gercek_kisi:
            dolu_koltuklar = [(r, c) for r in range(8) for c in range(4) if kisi_matrisi[r][c] == 1]
            if not dolu_koltuklar: break
            if oturma_duzeni == "Ön Sıralar": secilen = max(dolu_koltuklar, key=lambda x: x[0])
            elif oturma_duzeni == "Arka Sıralar": secilen = min(dolu_koltuklar, key=lambda x: x[0])
            else: secilen = random.choice(dolu_koltuklar)
            kisi_matrisi[secilen[0]][secilen[1]] = 0
            mevcut_kisi -= 1

        move_gates = [0] * 8
        stat_gates = [0] * 8
        for r in range(8):
            hareket_toplam = 0
            statik_toplam = 0
            for c in range(4):
                if kisi_matrisi[r][c] == 1:
                    mesafe_zayiflamasi = 1.0 - (r * 0.08) 
                    onumdeki_kisi = sum(kisi_matrisi[row][c] for row in range(r))
                    golgeleme = max(0.3, 1.0 - (onumdeki_kisi * 0.15))
                    
                    kisi_hareket = 12 + random.gauss(0, 3)
                    kisi_statik = 18 + random.gauss(0, 4)
                    
                    hareket_toplam += kisi_hareket * mesafe_zayiflamasi * golgeleme
                    statik_toplam += kisi_statik * mesafe_zayiflamasi * golgeleme
                    
            move_gates[r] = max(0, min(100, int(hareket_toplam)))
            stat_gates[r] = max(0, min(100, int(statik_toplam)))

        # SENSÖR GÜRÜLTÜLERİ
        okunan_sicaklik = sicaklik + random.gauss(0, 0.05)
        okunan_nem = nem + random.gauss(0, 0.3)
        okunan_co2 = co2 + random.gauss(0, 3.0)
        move_gates = [max(0, min(100, int(g + random.gauss(0, 2)))) if g > 0 else 0 for g in move_gates]
        stat_gates = [max(0, min(100, int(g + random.gauss(0, 3)))) if g > 0 else 0 for g in stat_gates]

        zaman += timedelta(seconds=1)
        satir = [zaman.strftime("%Y-%m-%d %H:%M:%S")] + move_gates + stat_gates + [
            round(okunan_sicaklik, 3), round(okunan_nem, 2), int(okunan_co2), round(co2_egimi, 2), 
            gercek_kisi, teorik_hedef, aktif_klima_gucu
        ]
        yazici.writerow(satir)

print("Veri üretimi tamamlandı!")
