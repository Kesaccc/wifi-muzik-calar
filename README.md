# WiFi Müzik Çalar

Aynı WiFi ağındaki telefon veya bilgisayardan kontrol edilen müzik çalar. Müzik Raspberry Pi'de (ya da bir bilgisayarda) çalar, telefon tarayıcı üzerinden uzaktan kumanda gibi kullanılır. Python ve Flask ile yapıldı; Elektrik-Elektronik Teknolojisi okul projesidir.


## Kurulum

Kütüphaneleri kurun:

    pip install -r requirements.txt

MP3 dosyalarını static/music/ klasörüne koyun ve programı başlatın:

    python app.py

Tarayıcıdan açın: aynı bilgisayardan http://localhost:8080, başka bir cihazdan http://BILGISAYAR-IP:8080

İlk giriş: kullanıcı adı admin, şifre 1234. Giriş yaptıktan sonra şifreyi değiştirin.


## Özellikler

- Çal, duraklat, ileri ve geri sarma
- Telefon ekranına uyumlu arayüz
- Şifreler SHA-256 ile saklanır
- Aynı IP'den 5 yanlış denemede 1 dakika kilit
- 15 dakika işlem yapılmazsa otomatik çıkış
- Giriş denemeleri login.log dosyasına kaydedilir (şifreler kaydedilmez)
