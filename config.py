# ==================== PRODUCTION CONFIG ====================
# Bu dosya production ortamı için yapılandırma ayarlarını içerir.

import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session ayarları
    SESSION_COOKIE_SECURE = True  # HTTPS zorunlu
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 saat
    
    # Güvenlik header'ları
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: http:; img-src 'self' data: https: http:; font-src 'self' https:;",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
