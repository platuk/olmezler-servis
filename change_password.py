#!/usr/bin/env python3
"""
Admin şifresini değiştirmek için bu scripti çalıştırın.
Kullanım: python change_password.py
"""
import hashlib
from werkzeug.security import generate_password_hash

print("=" * 50)
print("🔐 Admin Şifre Değiştirme")
print("=" * 50)

# Yeni şifreyi al
new_password = input("\nYeni şifreyi girin: ")
confirm_password = input("Şifreyi tekrar girin: ")

if new_password != confirm_password:
    print("❌ Şifreler eşleşmiyor!")
    exit(1)

if len(new_password) < 6:
    print("❌ Şifre en az 6 karakter olmalı!")
    exit(1)

# Şifreyi hashle
password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')

print(f"\n✅ Şifre hash'i oluşturuldu!")
print(f"\n📋 Aşağıdaki satırı .env dosyasına ekleyin:")
print(f"\nADMIN_PASSWORD_HASH={password_hash}")
print(f"\n" + "=" * 50)
print("⚠️  Bu hash'i kopyalayıp .env dosyasına yapıştırın.")
print("=" * 50)
