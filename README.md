# 🎵 Raspberry Pi WiFi Müzik Çalar

Aynı WiFi ağına bağlı telefon veya bilgisayardan uzaktan kontrol edilebilen müzik çalar. Python ve Flask ile yapılmıştır.

> Okul projesi — Elektrik-Elektronik Teknolojisi

---

## 📌 Proje Nedir?

Telefon bir **uzaktan kumanda** gibi çalışır, müziği ise **Raspberry Pi (veya bilgisayar)** çalar.

1. Raspberry Pi üzerinde Flask web sunucusu çalışır.
2. Aynı ağa bağlı bir cihaz (telefon/PC) tarayıcıdan bağlanır.
3. Web sitesindeki butonlarla müzik çalınır, durdurulur, ileri/geri sarılır.
4. Ses, sunucunun (Raspberry Pi'nin) hoparlöründen çıkar.

```
📱 Telefon  ──WiFi──>  📡 Ağ  ──>  🍓 Raspberry Pi (müziği çalar 🔊)
 (komut gönderir)                    (Flask sunucu)
```

---

## 🛠️ Kullanılan Teknolojiler

| Teknoloji | Görevi |
|-----------|--------|
| Python 3.12 | Programlama dili |
| Flask | Web sunucusu |
| pygame | Müziği çalar |
| mutagen | MP3 süresini okur |
| HTML/CSS/JS | Telefon uyumlu arayüz |

---

## 📁 Dosya Yapısı

```
music_player/
├── app.py                      # Ana program (sunucu)
├── requirements.txt            # Gerekli kütüphaneler
├── users.json                  # Kullanıcı/şifre (otomatik oluşur, paylaşılmaz)
├── login.log                   # Giriş kayıtları (otomatik oluşur, paylaşılmaz)
├── templates/
│   ├── index.html              # Müzik çalar sayfası
│   ├── login.html              # Giriş sayfası
│   └── change_password.html    # Şifre değiştirme sayfası
└── static/
    └── music/                  # MP3 dosyaları buraya
```

---

## ⚙️ Kurulum

**1. Kütüphaneleri kur:**
```bash
pip install -r requirements.txt
```

**2. MP3 dosyalarını ekle:**
`static/music/` klasörüne `.mp3` dosyalarını koy.

**3. Programı çalıştır:**
```bash
python app.py
```

**4. Tarayıcıdan aç:**
- Aynı bilgisayardan: `http://localhost:8080`
- Başka cihazdan: `http://<BILGISAYAR-IP>:8080`  (IP için: `ipconfig`)

> İlk çalıştırmada giriş bilgileri otomatik oluşur. Güvenlik için ilk girişten sonra şifreyi **"Şifre"** butonundan değiştirmen önerilir. Giriş bilgileri bu repoda paylaşılmaz.

**5. Başlangıçta Kullanıcı Adı/Şifre:**
- Kullanıcı adı : admin
- Şifre : 1234
-Güvenlik için Şifrenizi değiştirmeyi unutmayın

---

## 🔒 Güvenlik Özellikleri

- **Şifre hash'lenir** — SHA-256 ile, düz metin saklanmaz.
- **Brute-force koruması** — Aynı IP'den 5 yanlış denemede 1 dakika kilit (IP bazlı, diğer kullanıcılar etkilenmez).
- **Hareketsizlik zaman aşımı** — 15 dakika işlem yapılmazsa otomatik çıkış.
- **Giriş kayıtları** — Kim, ne zaman, hangi IP'den giriş yaptı/denedi `login.log`'a kaydedilir (şifre asla kaydedilmez).
- **Manuel çıkış** — "Çıkış" butonu.
- **Rastgele secret_key** — Oturum çerezleri güvenli şekilde imzalanır.

---

## 🎛️ Arayüz Özellikleri

- Her şarkı için tek oynat/duraklat butonu
- Şarkının gerçek süresini gösterir
- İleri/geri sarma çubuğu
- Telefon ekranına uyumlu tasarım
- Çalan şarkı yeşil çerçeveyle belirginleşir

---

## 🍓 Raspberry Pi Notları

**Açılışta otomatik başlat** — `/etc/rc.local` içine `exit 0` üstüne:
```bash
cd /home/pi/music_player && python3 app.py &
```

**Sabit IP** — `/etc/dhcpcd.conf` içine:
```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```
