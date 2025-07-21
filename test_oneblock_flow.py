#!/usr/bin/env python3
"""
Test manuel du flow oneblock.fr complet
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def test_oneblock_flow():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🌐 1. Accès à oneblock.fr/vote")
        driver.get("https://oneblock.fr/vote")
        time.sleep(3)
        
        print("✏️ 2. Remplissage du pseudo...")
        pseudo_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
        pseudo_field.clear()
        pseudo_field.send_keys("zCapsLock")
        print("✅ Pseudo 'zCapsLock' saisi")
        
        print("\n🔍 3. Recherche du bouton 'Envoyer'...")
        
        # Chercher tous les boutons
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        all_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
        
        print(f"Boutons trouvés: {len(all_buttons)}")
        for i, btn in enumerate(all_buttons):
            text = btn.text.strip()
            onclick = btn.get_attribute('onclick')
            print(f"  Button {i+1}: '{text}' onclick='{onclick}'")
            
        print(f"Inputs trouvés: {len(all_inputs)}")
        for i, inp in enumerate(all_inputs):
            value = inp.get_attribute('value')
            onclick = inp.get_attribute('onclick')
            print(f"  Input {i+1}: value='{value}' onclick='{onclick}'")
        
        # Essayer de trouver et cliquer sur "Envoyer"
        envoyer_found = False
        xpath_selectors = [
            "//button[contains(text(), 'Envoyer')]",
            "//input[@value='Envoyer']",
            "//button[contains(text(), 'ENVOYER')]"
        ]
        
        for xpath in xpath_selectors:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    for elem in elements:
                        if elem.is_displayed():
                            print(f"\n🎯 4. Bouton 'Envoyer' trouvé!")
                            elem.click()
                            print("✅ Clic sur 'Envoyer' effectué")
                            envoyer_found = True
                            time.sleep(5)
                            break
                    if envoyer_found:
                        break
            except:
                continue
                
        if not envoyer_found:
            print("❌ Bouton 'Envoyer' non trouvé")
            
        print("\n🔍 5. Recherche des sites de vote après 'Envoyer'...")
        
        # Chercher les sites après clic Envoyer
        time.sleep(3)
        
        site_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'SITE') or contains(text(), 'site')]")
        print(f"Éléments 'site' trouvés: {len(site_elements)}")
        for i, elem in enumerate(site_elements):
            text = elem.text.strip()[:100]
            print(f"  Site {i+1}: '{text}'")
            
        vote_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Votez') or contains(text(), 'Vote')]")
        print(f"Éléments 'Vote' trouvés: {len(vote_elements)}")
        for i, elem in enumerate(vote_elements):
            text = elem.text.strip()[:100]
            href = elem.get_attribute('href')
            print(f"  Vote {i+1}: '{text}' href='{href}'")
        
        print("\n⏸️ Page laissée ouverte pour inspection...")
        input("Appuyez sur Entrée pour fermer...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_oneblock_flow()