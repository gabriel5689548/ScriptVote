#!/usr/bin/env python3
"""
Test de différentes URLs de vote pour trouver la bonne page
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def test_vote_urls():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # URLs à tester
    test_urls = [
        "https://serveur-prive.net/oneblockbyrivrs/vote",
        "https://serveur-prive.net/oneblockbyrivrs/voter",  
        "https://serveur-prive.net/oneblockbyrivrs/",
        "https://serveur-prive.net/vote/oneblockbyrivrs",
        "https://serveur-prive.net/oneblockbyrivrs/index.php?p=vote",
        "https://serveur-prive.net/",
        "https://oneblockbyrivrs.serveur-prive.net/vote",
        "https://oneblockbyrivrs.serveur-prive.net/"
    ]
    
    try:
        for i, url in enumerate(test_urls):
            print(f"\n🌐 Test {i+1}: {url}")
            
            try:
                driver.get(url)
                time.sleep(3)
                
                current_url = driver.current_url
                title = driver.title
                
                print(f"   URL finale: {current_url}")
                print(f"   Titre: {title}")
                
                # Vérifier si on trouve des éléments de vote/captcha
                mtcaptcha_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'mtcaptcha') or contains(@data-sitekey, 'MT')]")
                username_fields = driver.find_elements(By.CSS_SELECTOR, "input[name='username'], input[name='pseudo'], input[placeholder*='pseudo' i]")
                vote_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'vote') or contains(text(), 'Vote')] | //input[@type='submit']")
                
                print(f"   MTCaptcha: {len(mtcaptcha_elements)}")
                print(f"   Champs username: {len(username_fields)}")
                print(f"   Boutons vote: {len(vote_buttons)}")
                
                # Chercher sitekey dans le code source
                page_source = driver.page_source
                if 'MTPublic-' in page_source:
                    import re
                    sitekey_match = re.search(r'MTPublic-[a-zA-Z0-9]+', page_source)
                    if sitekey_match:
                        print(f"   ✅ SITEKEY TROUVÉE: {sitekey_match.group(0)}")
                
                # Si on trouve des éléments prometteurs, analyser plus
                if mtcaptcha_elements or username_fields or vote_buttons or 'MTPublic-' in page_source:
                    print(f"   🎯 PAGE PROMETTEUSE! Analyse détaillée:")
                    
                    # Analyser les champs username
                    for j, field in enumerate(username_fields):
                        name = field.get_attribute('name')
                        placeholder = field.get_attribute('placeholder')
                        print(f"      Username {j+1}: name='{name}', placeholder='{placeholder}'")
                    
                    # Analyser les boutons
                    for j, btn in enumerate(vote_buttons):
                        text = btn.text or btn.get_attribute('value')
                        onclick = btn.get_attribute('onclick')
                        print(f"      Bouton {j+1}: '{text}', onclick='{onclick}'")
                    
                    # Si c'est vraiment prometteur, on s'arrête là
                    if 'MTPublic-' in page_source and username_fields:
                        print(f"   🎉 BINGO! Cette URL semble être la bonne!")
                        return url
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                continue
        
        print(f"\n❌ Aucune URL prometteuse trouvée")
        return None
        
    finally:
        driver.quit()

if __name__ == "__main__":
    best_url = test_vote_urls()
    if best_url:
        print(f"\n✅ Meilleure URL trouvée: {best_url}")
    else:
        print(f"\n❌ Aucune URL de vote fonctionnelle trouvée")