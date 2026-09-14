# 📊 Sensör Katalog

## Enerji Sistemi Sensörleri

### 1. Pil Yönetim Sistemi (BMS)
| Sensör | Tip | Aralık | Protokol | Notlar |
|--------|-----|--------|----------|--------|
| Pil Voltajı | Analog | 40-60V | Modbus RTU | Ana pil paketi |
| Pil Akımı | Analog | ±300A | Modbus RTU | Şarj/Deşarj |
| Pil SoC | Digital | 0-100% | Modbus RTU | Şarj durumu |
| Pil SoH | Digital | 0-100% | Modbus RTU | Sağlık durumu |
| Hücre Sıcaklığı | Analog | -20~60°C | Modbus RTU | NTC Thermistor |

### 2. Güneş Paneli (MPPT)
| Sensör | Tip | Aralık | Protokol | Notler |
|--------|-----|--------|----------|--------|
| Panel Voltajı | Analog | 0-100V | Modbus RTU | 2x 3kW panel |
| Panel Akımı | Analog | 0-50A | Modbus RTU | Her panel ayrı |
| Çıkış Gücü | Calculated | 0-6kW | Modbus RTU | V × I |
| Panel Sıcaklığı | Analog | -20~80°C | I2C | DS18B20 |

### 3. Motor Kontrolü
| Sensör | Tip | Aralık | Protokol | Notlar |
|--------|-----|--------|----------|--------|
| Motor 1 PWM | Digital | 0-255 | Arduino GPIO | Hız kontrolü |
| Motor 2 PWM | Digital | 0-255 | Arduino GPIO | Hız kontrolü |
| Motor 1 Akım | Analog | 0-100A | ADC | ACS712 sensör |
| Motor 2 Akım | Analog | 0-100A | ADC | ACS712 sensör |
| Motor 1 RPM | Digital | 0-5000 | Interrupt | Hall sensör |
| Motor 2 RPM | Digital | 0-5000 | Interrupt | Hall sensör |

---

## Çevre Sensörleri

### 4. Meteoroloji Sensörleri
| Sensör | Tip | Aralık | Protokol | Model |
|--------|-----|--------|----------|-------|
| Sıcaklık | Analog | -40~125°C | I2C | BME680 |
| Nem | Analog | 0-100% | I2C | BME680 |
| Hava Basıncı | Analog | 300-1100 hPa | I2C | BME680 |
| Rüzgar Hızı | Analog | 0-50 m/s | ADC | Anemometre |
| Rüzgar Yönü | Analog | 0-360° | ADC | Rüzgar vane |
| Hava Kalitesi (AQI) | Analog | 0-500 | I2C | BME680 |
| Gaz Sensörü (CO₂) | Analog | 400-5000 ppm | UART | MH-Z19B |

### 5. Işık Sensörleri
| Sensör | Tip | Aralık | Protokol | Notlar |
|--------|-----|--------|----------|--------|
| **Fotosel (LDR)** | Analog | 0-1023 | ADC | Gece/Gündüz algılama ✨ |
| UV Index | Analog | 0-16 | I2C | ML8511 |

### 6. 🌊 Deniz/Su Sensörleri (YENİ!)
| Sensör | Tip | Aralık | Protokol | Model | Notlar |
|--------|-----|--------|----------|-------|--------|
| **Deniz Suyu Sıcaklığı** | Analog | -5~40°C | 1-Wire | DS18B20 | Tekne gövdesine monte |
| Tuzluluk (Salinity) | Analog | 0-50 PSU | I2C | Atlas Scientific | Opsiyonel |
| Derinlik | Analog | 0-200m | UART | Garmin | GPS entegrasyonu |
| PH (Asitlik) | Analog | 0-14 | I2C | DFRobot | Su kalitesi |

---

## Su Sistemi Sensörleri

### 7. Su Seviyeleri
| Sensör | Tip | Aralık | Protokol | Notlar |
|--------|-----|--------|----------|--------|
| Tatlı Su Tankı | Analog | 0-100L | ADC | Kapasitif seviye |
| Gri Su Tankı | Analog | 0-50L | ADC | Kapasitif seviye |
| Sump Pit | Digital | Boş/Dolu | GPIO | Float switch |

### 8. Su Sızıntı Detektörleri
| Sensör | Tip | Konum | Protokol | Notlar |
|--------|-----|-------|----------|--------|
| Sızıntı 1 | Digital | Motor bölmesi | GPIO | Reed switch |
| Sızıntı 2 | Digital | Yaşam alanı altı | GPIO | Reed switch |
| Sızıntı 3 | Digital | Tekne gövdesi | GPIO | Reed switch |
| Sızıntı 4 | Digital | Su tankı etrafı | GPIO | Reed switch |

---

## 🚪 Kapı ve Pencere Sensörleri

### 9. Kapı/Pencere Kontak Sensörleri
| Sensör | Tip | Konum | Protokol | Durum |
|--------|-----|-------|----------|-------|
| **Ön Kapı** | Digital | Giriş | GPIO | Açık/Kapalı |
| **Arka Kapı** | Digital | Çıkış | GPIO | Açık/Kapalı |
| **Yaşam Pencereleri (4x)** | Digital | Kenarlar | GPIO | Açık/Kapalı |
| **Kokpit Penceresi** | Digital | Üst | GPIO | Açık/Kapalı |
| **Havalandırma Deliği** | Digital | Tavan | GPIO | Açık/Kapalı |

**Otomasyon Senaryoları:**
- Kapı/pencere açıldığında bildirim gönder
- Motorlar çalışırken kapılar açıldıysa uyar
- Gece hareket algılandığında kapıları kontrol et

---

## Hareket ve Yön Sensörleri

### 10. İnersiyel Ölçü Ünitesi (IMU)
| Sensör | Tip | Aralık | Protokol | Model |
|--------|-----|--------|----------|-------|
| İvmeölçer | 3-Axis | ±16g | I2C | MPU6050 |
| Jirokop | 3-Axis | ±2000°/s | I2C | MPU6050 |
| Manyetometre | 3-Axis | ±4800µT | I2C | HMC5883L |

**Hesaplanan Değerler:**
- Tekne Eğimi (Pitch, Roll, Yaw)
- Dalga Yüksekliği (Vertical acceleration)
- Tekne Hızı (İvme integral)

### 11. GNSS/GPS
| Sensör | Tip | Doğruluk | Protokol | Notlar |
|--------|-----|----------|----------|--------|
| GPS Konum | Digital | ±5m | UART | NEO-6M |
| Hız Üstü | Digital | ±0.1 m/s | UART | GPS'ten hesaplanır |

---

## 💡 Aydınlatma Sistemi

### 12. ARGB LED Kontrolü + Akıllı Sistem

| Bileşen | Tip | Kanal | Protokol | Notlar |
|---------|-----|--------|----------|--------|
| LED Şerit 1 | ARGB | 4-pin | PWM/GPIO | Yaşam alanı |
| LED Şerit 2 | ARGB | 4-pin | PWM/GPIO | Mutfak |
| LED Şerit 3 | ARGB | 4-pin | PWM/GPIO | Yatak odası |
| Dış Işık | ARGB | 4-pin | PWM/GPIO | Güverte aydınlatma |

**Akıllı Aydınlatma Özellikleri:**

#### Fotosel ile Otomatik Kontrol
```
Gündüz (Fotosel > 500):       → Işıklar kapalı ✓
Alacakaranlık (200-500):      → Otomatik aç (50% parlaklık) ✓
Gece (Fotosel < 200):         → Tam açma moduna geç ✓
```

#### Renk Tonu Otomatik Ayarı (Circadian Rhythm)
```
06:00 - Sabah:     Soğuk beyaz (6500K) [255,200,100]  60% parlaklık
09:00 - Gün:       Nötr beyaz (4000K)  [255,255,255]  30% parlaklık
18:00 - Akşam:     Sıcak turuncu (3000K) [255,150,80] 80% parlaklık  
21:00 - Gece:      Kırmızı (2000K)     [255,80,60]    40% parlaklık
```

#### Manuel Kontrol
- Mobil app'ten her LED şeridi bağımsız kontrol
- Parlaklık: 0-100%
- Renk seçimi: RGB palette veya hex kodu
- İçinde zamanlı aç/kapat

#### İleri Özellikler
- 🎬 Eğlence modu (müzik senkronizasyon)
- 🚨 Alarm modu (kırmızı yanıp sönen)
- 🌈 Rainbow mode
- ⏰ Kişiselleştirilmiş gündüz ritmi

---

## Sayısal Özet

**Toplam Sensör Sayısı:** ~42-45 sensör

### Sensör Protokolleri Dağılımı
- **Modbus RTU:** 8 (BMS, MPPT)
- **I2C:** 10 (BME680, IMU, Işık, Su kalitesi) ✨ +2 su sensörü
- **ADC (Analog):** 12 (Voltaj, Akım, Su, Işık)
- **GPIO (Digital):** 11 (Kapı, Pencere, Sızıntı)
- **UART:** 3 (GPS, CO₂, Derinlik) ✨ +1 derinlik
- **1-Wire:** 1 (Deniz suyu sıcaklığı) ✨ YENİ!
- **PWM:** 6 (Motor, LED)
- **Interrupt:** 2 (Motor RPM)

### Sensör Maliyeti Tahmini
- BMS/MPPT: 200-300€
- Çevre sensörleri: 80-120€
- Su sensörleri: 30-50€
- **Deniz/Su sensörleri: 50-100€** ✨ YENİ!
- Kapı/Pencere: 40-60€
- IMU/GPS: 50-80€
- LED sistemi: 100-150€
- Arduino/Raspberry Pi: 100€
- **Toplam:** ~650-1050€

---

## Gelecek Sürüm Sensörleri

- 🔍 Lidar (Çevre Tarama)
- 📷 Kamera Sistemi (Kış göz)
- ⛵ Gemi Hava Durumu Radyosu
- 🌊 Akımı ve Dalga Yönü (Wave Direction)
