from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, abort
import sqlite3
import os
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import html

# .env dosyasını yükle
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

app = Flask(__name__, static_folder='.')

# ==================== GÜVENLİK AYARLARI ====================
# Secret key - production'da environment variable olarak ayarlanmalı
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Session cookie ayarları
app.config['SESSION_COOKIE_SECURE'] = False  # True yapın HTTPS'de
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# ==================== ADMIN KİMLİK BİLGİLERİ ====================
# Production'da environment variable olarak ayarlanmalı
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
# Varsayılan şifre: olmezler123 (production'da değiştirilmeli)
DEFAULT_PASSWORD_HASH = generate_password_hash('olmezler123', method='pbkdf2:sha256')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', DEFAULT_PASSWORD_HASH)

DB_PATH = 'appointments.db'

# Rate limiting için basit sözlük
login_attempts = {}
RATE_LIMIT = 5  # 5 deneme
RATE_LIMIT_WINDOW = 300  # 5 dakika

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            vehicle TEXT,
            service TEXT NOT NULL,
            date TEXT,
            time TEXT,
            message TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            service_name TEXT NOT NULL,
            description TEXT,
            price TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS site_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            content_key TEXT NOT NULL,
            content_value TEXT,
            content_type TEXT DEFAULT 'text',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(section, content_key)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            service_name TEXT NOT NULL,
            price TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Varsayılan site içerikleri
    default_content = [
        # Hero Section
        ('hero', 'title', 'Ölmezler', 'text'),
        ('hero', 'subtitle', 'Araç Servis Merkezi', 'text'),
        ('hero', 'description', 'Aracınızın tüm bakım ve onarım ihtiyaçlarında profesyonel çözümler. Uzman kadro, orijinal yedek parça ve uygun fiyat garantisi.', 'text'),
        
        # Hakkımızda
        ('about', 'title', 'Kahramanmaraş\'ın Güvenilir Servisi', 'text'),
        ('about', 'description', 'Ölmezler - Honda Özel Servis olarak Kahramanmaraş\'ta uzun yıllardır araç sahiplerine profesyonel hizmet sunuyoruz. Honda marka araçlar başta olmak üzere tüm markalara uzman kadromuz ve modern ekipmanlarımızla hizmet veriyoruz.', 'text'),
        ('about', 'description2', 'Müşteri memnuniyetini ön planda tutarak, şeffaf fiyatlandırma ve garantili işçilik ile çalışıyoruz. Her marka ve model araç için uzman ekibimizle hizmetinizdeyiz.', 'text'),
        
        # Hizmetler
        ('services', 'title', 'Aracınız İçin Profesyonel Çözümler', 'text'),
        ('services', 'subtitle', 'Her marka ve model araç için kapsamlı servis hizmeti sunuyoruz.', 'text'),
        
        # Hizmet 1
        ('service_1', 'title', 'Motor Mekaniği', 'text'),
        ('service_1', 'description', 'Motor revizyonu, triger değişimi, segman, supap ayarı ve tüm mekanik onarımlar.', 'text'),
        
        # Hizmet 2
        ('service_2', 'title', 'Şanzıman & Diferansiyel', 'text'),
        ('service_2', 'description', 'Otomatik/manuel şanzıman tamiri, diferansiyel bakımı ve yağ değişimi.', 'text'),
        
        # Hizmet 3
        ('service_3', 'title', 'Kaporta & Boya', 'text'),
        ('service_3', 'description', 'Hasar onarımı, boya, pasta-cila, kaporta düzeltme ve koruma uygulamaları.', 'text'),
        
        # Hizmet 4
        ('service_4', 'title', 'Elektrik & Elektronik', 'text'),
        ('service_4', 'description', 'Arıza tespiti, kablo tesisatı, akü, marş dinamosu, şarj dinamosu tamiri.', 'text'),
        
        # Hizmet 5
        ('service_5', 'title', 'Periyodik Bakım', 'text'),
        ('service_5', 'description', 'Yağ değişimi, filtre değişimi, fren bakımı, antifriz ve genel kontrol.', 'text'),
        
        # Hizmet 6
        ('service_6', 'title', 'Rot-Balans & Ön Düzen', 'text'),
        ('service_6', 'description', 'Rot ayarı, balans, salıncak değişimi, rotil ve rotbaşı tamiri.', 'text'),
        
        # Hizmet 7
        ('service_7', 'title', 'Klima Servisi', 'text'),
        ('service_7', 'description', 'Klima gazı dolumu, kompresör tamiri, evaporatör ve kondenser değişimi.', 'text'),
        
        # Hizmet 8
        ('service_8', 'title', 'Yedek Parça', 'text'),
        ('service_8', 'description', 'Orijinal ve muadil yedek parça temini. Hızlı tedarik, uygun fiyat.', 'text'),
        
        # Neden Biz
        ('why_us', 'title', 'Bizi Tercih Etmeniz İçin 6 Neden', 'text'),
        
        # Neden 1
        ('reason_1', 'title', 'Kaliteli İşçilik', 'text'),
        ('reason_1', 'description', 'Her işte en yüksek kalite standartlarını uyguluyoruz.', 'text'),
        
        # Neden 2
        ('reason_2', 'title', 'Uygun Fiyat', 'text'),
        ('reason_2', 'description', 'Piyasa koşullarına göre adil ve rekabetçi fiyatlar.', 'text'),
        
        # Neden 3
        ('reason_3', 'title', 'Hızlı Servis', 'text'),
        ('reason_3', 'description', 'Aracınızı en kısa sürede teslim ediyoruz.', 'text'),
        
        # Neden 4
        ('reason_4', 'title', 'Güvenilir Hizmet', 'text'),
        ('reason_4', 'description', '15 yılı aşkın tecrübe ve binlerce mutlu müşteri.', 'text'),
        
        # Neden 5
        ('reason_5', 'title', '7/24 Destek', 'text'),
        ('reason_5', 'description', 'WhatsApp üzerinden her zaman ulaşabilirsiniz.', 'text'),
        
        # Neden 6
        ('reason_6', 'title', 'Garanti', 'text'),
        ('reason_6', 'description', 'Tüm işçilik ve parçalar garantilidir.', 'text'),
        
        # İletişim
        ('contact', 'address', 'Kahramanmaraş Merkez, Kahramanmaraş', 'text'),
        ('contact', 'phone', '0537 929 29 46', 'text'),
        ('contact', 'whatsapp', '905379292946', 'text'),
        ('contact', 'email', 'info@olmezler.com', 'text'),
        
        # Footer
        ('footer', 'description', 'Kahramanmaraş\'ta güvenilir Honda özel servis ve araç bakım merkezi. 15 yılı aşkın tecrübe ile hizmetinizdeyiz.', 'text'),
        ('footer', 'copyright', '© 2024 Ölmezler Araç Servis Merkezi. Tüm hakları saklıdır.', 'text'),
        
        # Çalışma Saatleri
        ('working_hours', 'weekday', 'Pazartesi - Cuma: 08:30 - 18:00', 'text'),
        ('working_hours', 'saturday', 'Cumartesi: 09:00 - 14:00', 'text'),
        ('working_hours', 'sunday', 'Pazar: Kapalı', 'text'),
    ]
    
    for section, key, value, content_type in default_content:
        conn.execute('INSERT OR IGNORE INTO site_content (section, content_key, content_value, content_type) VALUES (?, ?, ?, ?)', 
                     (section, key, value, content_type))
    
    # Varsayılan fiyatlar
    default_prices = [
        # Kategori, Hizmet Adı, Fiyat, Açıklama, Sıra
        ('Periyodik Bakım', 'Yağ Değişimi (Mineral)', '800 TL', 'Yağ + filtre dahil', 1),
        ('Periyodik Bakım', 'Yağ Değişimi (Sentetik)', '1.200 TL', 'Yağ + filtre dahil', 2),
        ('Periyodik Bakım', 'Büyük Bakım', '2.500 TL', 'Yağ, filtre, buji, hava filtresi dahil', 3),
        ('Periyodik Bakım', 'Fren Balata Değişimi (Ön)', '1.500 TL', 'Balata + işçilik', 4),
        ('Periyodik Bakım', 'Fren Balata Değişimi (Arka)', '1.200 TL', 'Balata + işçilik', 5),
        
        ('Motor Mekaniği', 'Triger Seti Değişimi', '3.500 TL', 'Triger kayışı + gergi + işçilik', 6),
        ('Motor Mekaniği', 'Motor Revizyonu', '15.000 TL', 'Kapsamlı motor onarımı', 7),
        ('Motor Mekaniği', 'Supap Ayarı', '1.000 TL', 'Tüm supaplar dahil', 8),
        ('Motor Mekaniği', 'Segman Değişimi', '8.000 TL', 'Segman + işçilik', 9),
        
        ('Şanzıman', 'Şanzıman Yağı Değişimi', '1.500 TL', 'Yağ + filtre + işçilik', 10),
        ('Şanzıman', 'Debriyaj Seti Değişimi', '4.000 TL', 'Debriyaj + bilya + işçilik', 11),
        ('Şanzıman', 'Diferansiyel Bakımı', '800 TL', 'Yağ değişimi + kontrol', 12),
        
        ('Elektrik', 'Akü Değişimi', '2.500 TL', 'Akü + montaj', 13),
        ('Elektrik', 'Marş Dinamosu Tamiri', '2.000 TL', 'Revizyon + işçilik', 14),
        ('Elektrik', 'Şarj Dinamosu Tamiri', '2.000 TL', 'Revizyon + işçilik', 15),
        ('Elektrik', 'Arıza Tespiti', '300 TL', 'Bilgisayarlı arıza tespiti', 16),
        
        ('Kaporta & Boya', 'Lokal Boya (1 Parça)', '3.000 TL', 'Pasta + cila dahil', 17),
        ('Kaporta & Boya', 'Tam Boya', '15.000 TL', 'Tüm araç boyama', 18),
        ('Kaporta & Boya', 'Kaporta Düzeltme', '1.500 TL', 'Göçük düzeltme (parça başı)', 19),
        
        ('Klima', 'Klima Gaz Dolumu', '800 TL', 'R134a gaz + işçilik', 20),
        ('Klima', 'Klima Kompresör Tamiri', '4.000 TL', 'Revizyon + işçilik', 21),
        ('Klima', 'Klima Bakımı', '500 TL', 'Kontrol + gaz ölçümü', 22),
        
        ('Rot-Balans', 'Rot-Balans (4 Teker)', '600 TL', 'Ön + arka balans', 23),
        ('Rot-Balans', 'Ön Düzen Ayarı', '800 TL', 'Rot + salıncak kontrolü', 24),
        ('Rot-Balans', 'Rotil Değişimi', '1.000 TL', 'Rotil + işçilik (parça başı)', 25),
    ]
    
    for category, name, price, desc, order in default_prices:
        conn.execute('''INSERT OR IGNORE INTO prices (category, service_name, price, description, sort_order) 
                        VALUES (?, ?, ?, ?, ?)''', (category, name, price, desc, order))
    
    # Varsayılan ayarlar
    default_settings = {
        'hero_badge': '7/24 hizmetimiz şu anda aktif',
        'site_title': 'Ölmezler Araç Servis Merkezi',
        'phone': '0537 929 29 46',
        'whatsapp': '905379292946'
    }
    for key, value in default_settings.items():
        conn.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

# ==================== GÜVENLİK FONKSİYONLARI ====================
def sanitize_input(text):
    """HTML ve SQL injection için input temizleme"""
    if not text:
        return ''
    # HTML escape
    text = html.escape(str(text))
    # Tehlikeli karakterleri temizle
    text = re.sub(r'[<>"\';]', '', text)
    return text.strip()

def validate_phone(phone):
    """Telefon numarası doğrulama"""
    if not phone:
        return False
    # Sadece rakam, boşluk, tire, parantez ve + kabul et
    pattern = r'^[\d\s\-\+\(\)]{10,20}$'
    return bool(re.match(pattern, phone))

def validate_name(name):
    """İsim doğrulama"""
    if not name or len(name) < 2 or len(name) > 100:
        return False
    # Sadece harf, boşluk ve Türkçe karakterler
    pattern = r'^[a-zA-ZçğıöşüÇĞİÖŞÜ\s]{2,100}$'
    return bool(re.match(pattern, name))

def check_rate_limit(ip):
    """Rate limiting kontrolü"""
    now = datetime.now()
    if ip in login_attempts:
        attempts, first_attempt = login_attempts[ip]
        if now - first_attempt > timedelta(seconds=RATE_LIMIT_WINDOW):
            login_attempts[ip] = (1, now)
            return True
        if attempts >= RATE_LIMIT:
            return False
        login_attempts[ip] = (attempts + 1, first_attempt)
    else:
        login_attempts[ip] = (1, now)
    return True

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated

# ==================== GÜVENLİK HEADER'LARI ====================
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: http:; img-src 'self' data: https: http:; font-src 'self' https:;"
    return response

# ==================== ADMIN ROUTES ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # Rate limiting kontrolü
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            with open('admin_login.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content.replace('<!-- ERROR_PLACEHOLDER -->', 
                '<div class="error" style="display:block;">Ç fazla deneme! 5 dakika bekleyin.</div>'), 429
        
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if not username or not password:
            with open('admin_login.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content.replace('<!-- ERROR_PLACEHOLDER -->', 
                '<div class="error" style="display:block;">Kullanıcı adı ve şifre gerekli!</div>')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            session.permanent = True
            # Rate limiting sıfırla
            if client_ip in login_attempts:
                del login_attempts[client_ip]
            return redirect('/admin')
        else:
            with open('admin_login.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content.replace('<!-- ERROR_PLACEHOLDER -->', 
                '<div class="error" style="display:block;">Kullanıcı adı veya şifre hatalı!</div>')
    
    return send_from_directory('.', 'admin_login.html')

# ==================== CONTENT API ====================
@app.route('/api/content', methods=['GET'])
def get_all_content():
    conn = get_db()
    content = conn.execute('SELECT * FROM site_content ORDER BY section, content_key').fetchall()
    conn.close()
    result = {}
    for row in content:
        section = row['section']
        if section not in result:
            result[section] = {}
        result[section][row['content_key']] = row['content_value']
    return jsonify(result)

@app.route('/api/content/<section>/<key>', methods=['GET'])
def get_content(section, key):
    conn = get_db()
    content = conn.execute('SELECT content_value FROM site_content WHERE section = ? AND content_key = ?', (section, key)).fetchone()
    conn.close()
    if content:
        return jsonify({'value': content['content_value']})
    return jsonify({'value': ''})

@app.route('/api/content/<section>/<key>', methods=['PUT'])
@login_required
def update_content(section, key):
    data = request.json
    if not data or 'value' not in data:
        return jsonify({'success': False, 'message': 'Değer gerekli'}), 400
    
    value = data.get('value', '')
    content_type = data.get('content_type', 'text')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO site_content (section, content_key, content_value, content_type, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(section, content_key) DO UPDATE SET
        content_value = excluded.content_value,
        content_type = excluded.content_type,
        updated_at = CURRENT_TIMESTAMP
    ''', (section, key, value, content_type))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/content/sections', methods=['GET'])
def get_content_sections():
    conn = get_db()
    sections = conn.execute('SELECT DISTINCT section FROM site_content ORDER BY section').fetchall()
    conn.close()
    return jsonify([row['section'] for row in sections])

@app.route('/api/content/section/<section>', methods=['GET'])
def get_section_content(section):
    conn = get_db()
    content = conn.execute('SELECT * FROM site_content WHERE section = ? ORDER BY content_key', (section,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in content])

@app.route('/admin')
@login_required
def admin_panel():
    return send_from_directory('.', 'admin.html')

@app.route('/admin/content')
@login_required
def admin_content():
    return send_from_directory('.', 'admin-content.html')

@app.route('/admin/prices')
@login_required
def admin_prices():
    return send_from_directory('.', 'admin-prices.html')

@app.route('/fiyatlar')
def prices_page():
    return send_from_directory('.', 'prices.html')

# ==================== PRICES API ====================
@app.route('/api/prices', methods=['GET'])
def get_prices():
    """Tüm fiyatları getir (sadece aktif olanlar)"""
    conn = get_db()
    prices = conn.execute('''
        SELECT * FROM prices WHERE is_active = 1 ORDER BY category, sort_order, id
    ''').fetchall()
    conn.close()
    
    # Kategorilere göre grupla
    result = {}
    for price in prices:
        cat = price['category']
        if cat not in result:
            result[cat] = []
        result[cat].append(dict(price))
    
    return jsonify(result)

@app.route('/api/prices/all', methods=['GET'])
@login_required
def get_all_prices():
    """Tüm fiyatları getir (admin - aktif/pasif hepsi)"""
    conn = get_db()
    prices = conn.execute('SELECT * FROM prices ORDER BY category, sort_order, id').fetchall()
    conn.close()
    return jsonify([dict(p) for p in prices])

@app.route('/api/prices', methods=['POST'])
@login_required
def add_price():
    """Yeni fiyat ekle"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Geçersiz veri'}), 400
    
    category = sanitize_input(data.get('category', ''))
    service_name = sanitize_input(data.get('service_name', ''))
    price = sanitize_input(data.get('price', ''))
    description = sanitize_input(data.get('description', ''))
    sort_order = data.get('sort_order', 0)
    
    if not category or not service_name or not price:
        return jsonify({'success': False, 'message': 'Kategori, hizmet adı ve fiyat zorunludur'}), 400
    
    conn = get_db()
    
    # Check for duplicate
    existing = conn.execute(
        'SELECT id FROM prices WHERE category = ? AND service_name = ?',
        (category, service_name)
    ).fetchone()
    
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Bu hizmet zaten mevcut'}), 400
    
    cursor = conn.execute('''
        INSERT INTO prices (category, service_name, price, description, sort_order)
        VALUES (?, ?, ?, ?, ?)
    ''', (category, service_name, price, description, sort_order))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': new_id, 'message': 'Fiyat eklendi'})

@app.route('/api/prices/<int:id>', methods=['PUT'])
@login_required
def update_price(id):
    """Fiyat güncelle"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Geçersiz veri'}), 400
    
    category = sanitize_input(data.get('category', ''))
    service_name = sanitize_input(data.get('service_name', ''))
    price = sanitize_input(data.get('price', ''))
    description = sanitize_input(data.get('description', ''))
    is_active = data.get('is_active', 1)
    sort_order = data.get('sort_order', 0)
    
    if not category or not service_name or not price:
        return jsonify({'success': False, 'message': 'Kategori, hizmet adı ve fiyat zorunludur'}), 400
    
    conn = get_db()
    conn.execute('''
        UPDATE prices 
        SET category=?, service_name=?, price=?, description=?, is_active=?, sort_order=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (category, service_name, price, description, is_active, sort_order, id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Fiyat güncellendi'})

@app.route('/api/prices/<int:id>', methods=['DELETE'])
@login_required
def delete_price(id):
    """Fiyat sil"""
    conn = get_db()
    conn.execute('DELETE FROM prices WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Fiyat silindi'})

@app.route('/api/prices/categories', methods=['GET'])
def get_price_categories():
    """Tüm kategorileri getir"""
    conn = get_db()
    categories = conn.execute('SELECT DISTINCT category FROM prices WHERE is_active = 1 ORDER BY category').fetchall()
    conn.close()
    return jsonify([c['category'] for c in categories])

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect('/')

# ==================== STATIC FILES ====================
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/yerimiz')
def yerimiz():
    return send_from_directory('.', 'yerimiz.html')

@app.route('/chat')
def chat():
    return send_from_directory('.', 'chat.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Yüklenen dosyaları serve et"""
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return send_from_directory(upload_dir, filename)

# ==================== API ====================
@app.route('/api/appointment', methods=['POST'])
def create_appointment():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Geçersiz veri'}), 400
    
    # Input validation
    name = sanitize_input(data.get('name', ''))
    phone = sanitize_input(data.get('phone', ''))
    vehicle = sanitize_input(data.get('vehicle', ''))
    service = sanitize_input(data.get('service', ''))
    date = sanitize_input(data.get('date', ''))
    time = sanitize_input(data.get('time', ''))
    message = sanitize_input(data.get('message', ''))
    
    if not name or not phone or not service:
        return jsonify({'success': False, 'message': 'Ad, telefon ve hizmet alanları zorunludur'}), 400
    
    if not validate_name(name):
        return jsonify({'success': False, 'message': 'Geçersiz ad formatı'}), 400
    
    if not validate_phone(phone):
        return jsonify({'success': False, 'message': 'Geçersiz telefon formatı'}), 400
    
    conn = get_db()
    conn.execute('''
        INSERT INTO appointments (name, phone, vehicle, service, date, time, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, phone, vehicle, service, date, time, message))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Randevu talebiniz alındı!'})

@app.route('/api/appointments', methods=['GET'])
@login_required
def get_appointments():
    conn = get_db()
    status = request.args.get('status', 'all')
    if status == 'all':
        appointments = conn.execute('SELECT * FROM appointments ORDER BY created_at DESC').fetchall()
    else:
        # Status değerini doğrula
        allowed_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        if status not in allowed_statuses:
            return jsonify({'success': False, 'message': 'Geçersiz durum'}), 400
        appointments = conn.execute('SELECT * FROM appointments WHERE status = ? ORDER BY created_at DESC', (status,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in appointments])

@app.route('/api/appointment/<int:id>/status', methods=['PUT'])
@login_required
def update_status(id):
    data = request.json
    if not data or 'status' not in data:
        return jsonify({'success': False, 'message': 'Durum bilgisi gerekli'}), 400
    
    # Status değerini doğrula
    allowed_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
    status = data.get('status')
    if status not in allowed_statuses:
        return jsonify({'success': False, 'message': 'Geçersiz durum'}), 400
    
    conn = get_db()
    conn.execute('UPDATE appointments SET status = ? WHERE id = ?', (status, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/appointment/<int:id>', methods=['DELETE'])
@login_required
def delete_appointment(id):
    conn = get_db()
    conn.execute('DELETE FROM appointments WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'pending'").fetchone()[0]
    confirmed = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'confirmed'").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'completed'").fetchone()[0]
    conn.close()
    return jsonify({'total': total, 'pending': pending, 'confirmed': confirmed, 'completed': completed})

# ==================== SETTINGS API ====================
@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = get_db()
    settings = conn.execute('SELECT * FROM settings').fetchall()
    conn.close()
    return jsonify({row['key']: row['value'] for row in settings})

@app.route('/api/settings/<key>', methods=['GET'])
def get_setting(key):
    # Key değerini doğrula
    allowed_keys = ['hero_badge', 'site_title', 'phone', 'whatsapp']
    if key not in allowed_keys:
        return jsonify({'error': 'Geçersiz ayar'}), 400
    
    conn = get_db()
    setting = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    if setting:
        return jsonify({'key': key, 'value': setting['value']})
    return jsonify({'error': 'Ayar bulunamadı'}), 404

@app.route('/api/settings/<key>', methods=['PUT'])
@login_required
def update_setting(key):
    # Key değerini doğrula
    allowed_keys = ['hero_badge', 'site_title', 'phone', 'whatsapp']
    if key not in allowed_keys:
        return jsonify({'success': False, 'message': 'Geçersiz ayar'}), 400
    
    data = request.json
    if not data or 'value' not in data:
        return jsonify({'success': False, 'message': 'Değer gerekli'}), 400
    
    value = sanitize_input(data.get('value', ''))
    if not value:
        return jsonify({'success': False, 'message': 'Boş değer kabul edilmez'}), 400
    
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'success': False, 'message': 'Ad gerekli'}), 400
    
    visitor_name = sanitize_input(data.get('name', ''))
    if not visitor_name or len(visitor_name) < 2 or len(visitor_name) > 100:
        return jsonify({'success': False, 'message': 'Geçersiz ad (2-100 karakter)'}), 400
    
    conn = get_db()
    cursor = conn.execute('INSERT INTO chats (visitor_name) VALUES (?)', (visitor_name,))
    chat_id = cursor.lastrowid
    # Hoşgeldin mesajı
    welcome_msg = f'Merhaba {visitor_name}! Ölmezler Servis canlı destek hattına hoş geldiniz. Size nasıl yardımcı olabiliriz?'
    conn.execute('INSERT INTO chat_messages (chat_id, sender, message) VALUES (?, ?, ?)',
                 (chat_id, 'admin', welcome_msg))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'chat_id': chat_id, 'visitor_name': visitor_name})

@app.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    conn = get_db()
    # Chat'in var olduğunu kontrol et
    chat = conn.execute('SELECT id FROM chats WHERE id = ?', (chat_id,)).fetchone()
    if not chat:
        conn.close()
        return jsonify({'success': False, 'message': 'Sohbet bulunamadı'}), 404
    
    messages = conn.execute('SELECT * FROM chat_messages WHERE chat_id = ? ORDER BY created_at', (chat_id,)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in messages])

@app.route('/api/chat/<int:chat_id>/send', methods=['POST'])
def send_chat_message(chat_id):
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'success': False, 'message': 'Mesaj gerekli'}), 400
    
    sender = data.get('sender', 'visitor')
    message = sanitize_input(data.get('message', ''))
    
    if not message:
        return jsonify({'success': False, 'message': 'Boş mesaj kabul edilmez'}), 400
    
    if len(message) > 1000:
        return jsonify({'success': False, 'message': 'Mesaj çok uzun (maks 1000 karakter)'}), 400
    
    # Sender doğrulama
    allowed_senders = ['visitor', 'admin']
    if sender not in allowed_senders:
        return jsonify({'success': False, 'message': 'Geçersiz gönderici'}), 400
    
    # Admin mesajı göndermek için giriş yapmış olmalı
    if sender == 'admin' and 'logged_in' not in session:
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
    
    conn = get_db()
    # Chat'in var olduğunu kontrol et
    chat = conn.execute('SELECT id FROM chats WHERE id = ?', (chat_id,)).fetchone()
    if not chat:
        conn.close()
        return jsonify({'success': False, 'message': 'Sohbet bulunamadı'}), 404
    
    conn.execute('INSERT INTO chat_messages (chat_id, sender, message) VALUES (?, ?, ?)',
                 (chat_id, sender, message))
    if sender == 'visitor':
        conn.execute('UPDATE chat_messages SET is_read = 0 WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/chats', methods=['GET'])
@login_required
def get_chats():
    conn = get_db()
    chats = conn.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM chat_messages WHERE chat_id = c.id AND sender = 'visitor' AND is_read = 0) as unread_count,
               (SELECT message FROM chat_messages WHERE chat_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message
        FROM chats c 
        WHERE c.status = 'active'
        ORDER BY c.created_at DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(c) for c in chats])

@app.route('/api/chat/<int:chat_id>/read', methods=['POST'])
@login_required
def mark_chat_read(chat_id):
    conn = get_db()
    conn.execute("UPDATE chat_messages SET is_read = 1 WHERE chat_id = ? AND sender = 'visitor'", (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/chat/<int:chat_id>/close', methods=['POST'])
@login_required
def close_chat(chat_id):
    conn = get_db()
    conn.execute("UPDATE chats SET status = 'closed' WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/chat/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE sender = 'visitor' AND is_read = 0").fetchone()[0]
    conn.close()
    return jsonify({'count': count})

# ==================== SERVICES API ====================
@app.route('/api/services', methods=['GET'])
def get_services():
    # Default services - production'da veritabanından gelecek
    services = [
        {'id': 1, 'title': 'Motor Mekaniği', 'desc': 'Motor revizyonu, triger değişimi, segman, supap ayarı ve tüm mekanik onarımlar.', 'icon': 'fa-engine'},
        {'id': 2, 'title': 'Şanzıman & Diferansiyel', 'desc': 'Otomatik/manuel şanzıman tamiri, diferansiyel bakımı ve yağ değişimi.', 'icon': 'fa-gears'},
        {'id': 3, 'title': 'Kaporta & Boya', 'desc': 'Hasar onarımı, boya, pasta-cila, kaporta düzeltme ve koruma uygulamaları.', 'icon': 'fa-car-burst'},
        {'id': 4, 'title': 'Elektrik & Elektronik', 'desc': 'Arıza tespiti, kablo tesisatı, akü, marş dinamosu, şarj dinamosu tamiri.', 'icon': 'fa-bolt'},
        {'id': 5, 'title': 'Periyodik Bakım', 'desc': 'Yağ değişimi, filtre değişimi, fren bakımı, antifriz ve genel kontrol.', 'icon': 'fa-oil-can'},
        {'id': 6, 'title': 'Rot-Balans & Ön Düzen', 'desc': 'Rot ayarı, balans, salıncak değişimi, rotil ve rotbaşı tamiri.', 'icon': 'fa-circle-notch'},
        {'id': 7, 'title': 'Klima Servisi', 'desc': 'Klima gazı dolumu, kompresör tamiri, evaporatör ve kondenser değişimi.', 'icon': 'fa-snowflake'},
        {'id': 8, 'title': 'Yedek Parça', 'desc': 'Orijinal ve muadil yedek parça temini. Hızlı tedarik, uygun fiyat.', 'icon': 'fa-box-open'}
    ]
    return jsonify(services)

@app.route('/api/services', methods=['PUT'])
@login_required
def update_services():
    data = request.json
    if not data or 'services' not in data:
        return jsonify({'success': False, 'message': 'Hizmet verisi gerekli'}), 400
    
    # Services verisini doğrula
    services = data.get('services', [])
    for service in services:
        if not isinstance(service.get('title'), str) or not isinstance(service.get('desc'), str):
            return jsonify({'success': False, 'message': 'Geçersiz hizmet verisi'}), 400
    
    # Production'da veritabanına kaydedilecek
    # Şimdilik başarılı dön
    return jsonify({'success': True, 'message': f'{len(services)} hizmet kaydedildi'})

# ==================== STATIC FILES (CATCH-ALL) ====================
@app.route('/<path:filename>')
def static_files(filename):
    # Directory traversal engelleme
    if '..' in filename or filename.startswith('/'):
        abort(404)
    # Sadece izinli dosya uzantılarına erişim
    allowed_extensions = {'.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf'}
    ext = os.path.splitext(filename)[1].lower()
    if ext and ext not in allowed_extensions:
        abort(404)
    return send_from_directory('.', filename)

# ==================== HATA YÖNETİMİ ====================
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Sayfa bulunamadı'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Sunucu hatası'}), 500

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({'error': 'Çok fazla istek'}), 429

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("Ölmezler Araç Servis Merkezi - Admin Paneli")
    print("=" * 50)
    print(f"Site: http://localhost:5000")
    print(f"Admin: http://localhost:5000/admin")
    print(f"Giriş: admin / olmezler123")
    print("=" * 50)
    print("⚠️  GÜVENLİK UYARISI: Production'da şifreyi değiştirin!")
    print("=" * 50)
    # Production'da debug=False olmalı
    app.run(debug=False, port=5000)
