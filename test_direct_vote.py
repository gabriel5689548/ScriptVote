#!/usr/bin/env python3
"""
Test direct d'accès au site de vote sans passer par oneblock.fr
Pour voir si le vote direct fonctionne
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def test_direct_vote():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Test 1: Accès direct à l'URL de vote
        vote_url = "https://serveur-prive.net/oneblockbyrivrs/vote"
        print(f"🌐 Test 1: Accès direct à {vote_url}")
        driver.get(vote_url)
        time.sleep(5)
        
        # Vérifier si on arrive sur la page de vote
        current_url = driver.current_url
        print(f"   URL actuelle: {current_url}")
        
        # Chercher des éléments de captcha
        mtcaptcha_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'mtcaptcha') or contains(@data-sitekey, 'MT')]")
        print(f"   Éléments MTCaptcha trouvés: {len(mtcaptcha_elements)}")
        
        # Chercher des champs de vote
        vote_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'vote') or contains(text(), 'Vote')]")
        print(f"   Éléments de vote trouvés: {len(vote_elements)}")
        
        # Chercher des champs username/pseudo
        username_fields = driver.find_elements(By.CSS_SELECTOR, "input[name='username'], input[name='pseudo'], input[placeholder*='pseudo' i]")
        print(f"   Champs username/pseudo trouvés: {len(username_fields)}")
        
        for i, field in enumerate(username_fields):
            name = field.get_attribute('name')
            placeholder = field.get_attribute('placeholder')
            print(f"      Champ {i+1}: name='{name}', placeholder='{placeholder}'")
        
        # Test 2: Si ça fonctionne, tester avec oneblock.fr en referrer
        print(f"\n🌐 Test 2: Accès avec referrer oneblock.fr")
        driver.execute_script(f"window.location.href = '{vote_url}'; document.referrer = 'https://oneblock.fr/vote';")
        time.sleep(5)
        
        current_url2 = driver.current_url
        print(f"   URL après referrer: {current_url2}")
        
        # Test 3: Vérifier les cookies oneblock.fr
        print(f"\n🌐 Test 3: Vérification des cookies")
        driver.get("https://oneblock.fr")
        time.sleep(3)
        
        cookies = driver.get_cookies()
        print(f"   Cookies oneblock.fr: {len(cookies)}")
        for cookie in cookies:
            print(f"      {cookie['name']}: {cookie['value'][:50]}...")
        
        # Maintenant retester l'accès au vote
        print(f"\n🌐 Test 4: Accès au vote après visite oneblock.fr")
        driver.get(vote_url)
        time.sleep(5)
        
        current_url3 = driver.current_url
        print(f"   URL finale: {current_url3}")
        
        # Analyser la page finale
        print(f"\n🔍 ANALYSE PAGE FINALE:")
        
        # Chercher MTCaptcha sitekey
        page_source = driver.page_source
        if 'MTPublic-' in page_source:
            import re
            sitekey_match = re.search(r'MTPublic-[a-zA-Z0-9]+', page_source)
            if sitekey_match:
                print(f"   ✅ Sitekey MTCaptcha trouvée: {sitekey_match.group(0)}")
        
        # Chercher formulaires
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"   Formulaires trouvés: {len(forms)}")
        
        # Chercher boutons de vote
        vote_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'vote') or contains(text(), 'Vote')] | //input[@type='submit']")
        print(f"   Boutons de vote: {len(vote_buttons)}")
        
        for i, btn in enumerate(vote_buttons):
            text = btn.text or btn.get_attribute('value')
            print(f"      Bouton {i+1}: '{text}'")
        
        print("\n⏸️ Page laissée ouverte pour inspection...")
        input("Appuyez sur Entrée pour fermer...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_direct_vote()