# 🚀 Ölmezler Araç Servis Merkezi - Production

## Hızlı Başlangıç

```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. .env dosyası oluştur
cp .env.example .env
nano .env  # Değerleri düzenleyin

# 3. Production deployment
chmod +x deploy.sh
./deploy.sh

# 4. Uygulamayı başlat
python app.py
```

## Production Ayarları

### .env Dosyası
```env
# Güçlü bir secret key oluşturun
SECRET_KEY=rastgele-64-karakter-string

# Admin şifresini değiştirin
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=yeni-sifre-hash

# Production
FLASK_ENV=production
FLASK_DEBUG=0
```

### HTTPS Ayarları
```python
# app.py'de
app.config['SESSION_COOKIE_SECURE'] = True
```

### Veritabanı Güvenliği
```bash
# Veritabanı dosyasını koru
chmod 600 appointments.db
chown www-data:www-data appointments.db
```

## Deployment Seçenekleri

### 1. PythonAnywhere (Ücretsiz)
```bash
# Dosyaları yükle
# WSGI yapılandırmasını yap
# Reload et
```

### 2. Railway.app
```bash
# GitHub'a push et
# Railway'de deploy et
```

### 3. VPS (DigitalOcean, Linode, vb.)
```bash
# Sunucuya SSH ile bağlan
git clone <repo-url>
cd olmezler-servis
./deploy.sh
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 4. Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Monitoring

```bash
# Logları izle
tail -f logs/app.log

# Sistem kaynaklarını kontrol et
htop

# Veritabanı boyutunu kontrol et
ls -lh appointments.db
```

## Yedekleme

```bash
# Günlük yedekleme crontab
0 2 * * * cp /path/to/appointments.db /backup/appointments_$(date +\%Y\%m\%d).db
```

## Güvenlik Kontrol Listesi

- [ ] .env dosyası oluşturuldu
- [ ] SECRET_KEY değiştirildi
- [ ] Admin şifresi değiştirildi
- [ ] HTTPS aktif edildi
- [ ] Debug modu kapalı
- [ ] Rate limiting aktif
- [ ] Güvenlik header'ları eklendi
- [ ] Veritabanı dosyası korunuyor
- [ ] Log dosyası oluşturuldu
- [ ] Yedekleme sistemi kuruldu

## Sorun Giderme

### "SECRET_KEY not set" hatası
```bash
# .env dosyasını kontrol et
cat .env | grep SECRET_KEY
```

### "Permission denied" hatası
```bash
chmod 600 .env
chmod 600 appointments.db
```

### "Port already in use" hatası
```bash
# Portu kullanan süreci bul
lsof -i :5000
# Süreci sonlandır
kill -9 <PID>
```

## İletişim

- **Telefon:** 0537 929 29 46
- **WhatsApp:** [wa.me/905379292946](https://wa.me/905379292946)
- **Adres:** Kahramanmaraş
