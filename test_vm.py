#!/usr/bin/env python3

"""
Script de test pour vérifier que tout fonctionne sur la VM Azure
"""

import sys
import os
from dotenv import load_dotenv

print("🧪 Test de configuration de la VM")
print("=" * 40)

# Test 1: Python version
print(f"✅ Python version: {sys.version}")

# Test 2: Platform
print(f"✅ Platform: {sys.platform}")

# Test 3: Modules
try:
    import seleniumbase
    print(f"✅ SeleniumBase installé: {seleniumbase.__version__}")
except ImportError:
    print("❌ SeleniumBase non installé!")

try:
    import requests
    print("✅ Requests installé")
except ImportError:
    print("❌ Requests non installé!")

try:
    from selenium import webdriver
    print("✅ Selenium installé")
except ImportError:
    print("❌ Selenium non installé!")

# Test 4: .env
load_dotenv()
api_key = os.getenv('TWOCAPTCHA_API_KEY') or os.getenv('api_key')
username = os.getenv('username', 'zCapsLock')

if api_key:
    print(f"✅ API Key trouvée: {api_key[:10]}...")
else:
    print("❌ API Key non trouvée dans .env!")

print(f"✅ Username: {username}")

# Test 5: Chrome
print("\n🌐 Test de Chrome headless:")
try:
    from seleniumbase import SB
    
    print("  Création du driver headless...")
    with SB(headless=True, xvfb=True) as sb:
        print("  ✅ Driver créé avec succès")
        
        print("  Test d'accès à une page...")
        sb.open("https://www.google.com")
        title = sb.get_title()
        print(f"  ✅ Page chargée: {title}")
        
        print("  ✅ Chrome headless fonctionne!")
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

print("\n✨ Test terminé!")
print("\nPour lancer le vote:")
print("python3 mtcaptcha_seleniumbase.py --headless")