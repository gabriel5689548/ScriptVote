#!/usr/bin/env python3

import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

print("Test minimal avec Selenium standard (headless)")

# Configuration Chrome headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

try:
    print("📍 Création du driver...")
    driver = webdriver.Chrome(options=chrome_options)
    print("✅ Driver créé")
    
    print("📍 Accès à oneblock.fr...")
    driver.get("https://oneblock.fr/vote")
    time.sleep(3)
    
    print(f"📄 Titre: {driver.title}")
    
    # Chercher le champ username
    try:
        username_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
        username_field.send_keys("zCapsLock")
        print("✅ Username saisi")
    except Exception as e:
        print(f"❌ Erreur username: {e}")
    
    # Chercher les boutons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"📋 {len(buttons)} boutons trouvés")
    
    for btn in buttons:
        if "ENVOYER" in btn.text.upper():
            print(f"✅ Bouton ENVOYER trouvé: '{btn.text}'")
            btn.click()
            print("✅ Clic effectué")
            break
    
    time.sleep(5)
    
    # Chercher SITE N°1
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "SITE N°1" in btn.text:
            print(f"📋 SITE N°1 trouvé: '{btn.text.replace(chr(10), ' ')}'")
            # Détecter le cooldown
            import re
            if re.search(r'\d+h\s*\d+min\s*\d+s', btn.text):
                print("⏰ COOLDOWN DÉTECTÉ!")
            break
    
    driver.quit()
    print("✅ Test terminé")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()