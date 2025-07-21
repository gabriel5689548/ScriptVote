#!/usr/bin/env python3
"""
Test de détection de sitekey uniquement
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_sitekey_detection(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Accès à: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Test de récupération de la sitekey
        sitekey = driver.execute_script("""
            if (typeof mtcaptchaConfig !== 'undefined' && mtcaptchaConfig.sitekey) {
                return mtcaptchaConfig.sitekey;
            }
            return null;
        """)
        
        if sitekey:
            print(f"✅ Sitekey détectée: {sitekey}")
            
            # Afficher la configuration complète
            config = driver.execute_script("""
                if (typeof mtcaptchaConfig !== 'undefined') {
                    return mtcaptchaConfig;
                }
                return null;
            """)
            
            if config:
                print(f"📋 Configuration MTCaptcha:")
                for key, value in config.items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Aucune sitekey détectée")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    test_sitekey_detection("https://serveur-prive.net/minecraft/oneblockbyrivrs/vote")