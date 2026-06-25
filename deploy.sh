#!/bin/bash
# ==================== PRODUCTION DEPLOYMENT ====================
# Bu script production ortamını hazırlar.

echo "🔧 Production Deployment Başlıyor..."

# 1. .env dosyası kontrolü
if [ ! -f .env ]; then
    echo "❌ .env dosyası bulunamadı!"
    echo "📝 .env.example dosyasını .env olarak kopyalayın:"
    echo "   cp .env.example .env"
    echo "   nano .env  # Değerleri düzenleyin"
    exit 1
fi

# 2. Bağımlılıkları yükle
echo "📦 Bağımlılıklar yükleniyor..."
pip install -r requirements.txt

# 3. Veritabanını başlat
echo "🗄️ Veritabanı başlatılıyor..."
python -c "from app import init_db; init_db()"

# 4. Güvenlik kontrolü
echo "🔒 Güvenlik kontrolü..."
python -c "
import os
from app import app

checks = []

# Secret key kontrolü
if app.secret_key == 'change-this-in-production':
    checks.append('❌ SECRET_KEY değiştirilmemiş!')
else:
    checks.append('✅ SECRET_KEY ayarlı')

# Debug kontrolü
if app.debug:
    checks.append('❌ Debug modu açık!')
else:
    checks.append('✅ Debug modu kapalı')

# Session cookie kontrolü
if not app.config.get('SESSION_COOKIE_SECURE'):
    checks.append('⚠️  SESSION_COOKIE_SECURE kapalı (HTTPS gerekli)')
else:
    checks.append('✅ SESSION_COOKIE_SECURE açık')

for check in checks:
    print(check)
"

# 5. Dosya izinleri
echo "📁 Dosya izinleri ayarlanıyor..."
chmod 600 .env
chmod 600 appointments.db
chmod 755 app.py

# 6. Log dizini oluştur
echo "📝 Log dizini oluşturuluyor..."
mkdir -p logs
chmod 755 logs

echo ""
echo "✅ Production deployment tamamlandı!"
echo ""
echo "🚀 Uygulamayı başlatmak için:"
echo "   python app.py"
echo ""
echo "🌐 Veya gunicorn ile:"
echo "   gunicorn -w 4 -b 0.0.0.0:5000 app:app"
echo ""
echo "📊 Monitoring:"
echo "   tail -f logs/app.log"
