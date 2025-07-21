#!/usr/bin/env python3
"""
Test simple pour comprendre la structure de oneblock.fr/vote
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def simple_test():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🌐 Accès à oneblock.fr/vote...")
        driver.get("https://oneblock.fr/vote")
        time.sleep(5)
        
        print("\n🔍 ANALYSE DE TOUS LES BOUTONS:")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Total boutons: {len(all_buttons)}")
        
        for i, btn in enumerate(all_buttons):
            text = btn.text.strip()
            visible = btn.is_displayed()
            enabled = btn.is_enabled()
            classes = btn.get_attribute('class')
            
            print(f"\nBouton {i+1}:")
            print(f"   Texte: '{text}'")
            print(f"   Visible: {visible}")
            print(f"   Enabled: {enabled}")
            print(f"   Classes: {classes}")
            
            if 'envoyer' in text.lower():
                print(f"   ⭐ BOUTON ENVOYER TROUVÉ!")
        
        print("\n✏️ Remplissage du pseudo...")
        try:
            pseudo_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
            pseudo_field.clear()
            pseudo_field.send_keys("zCapsLock")
            print("✅ Pseudo saisi")
            time.sleep(3)
        except Exception as e:
            print(f"❌ Erreur pseudo: {e}")
        
        print("\n🔍 ANALYSE APRÈS SAISIE PSEUDO:")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Total boutons après saisie: {len(all_buttons)}")
        
        for i, btn in enumerate(all_buttons):
            text = btn.text.strip()
            visible = btn.is_displayed()
            enabled = btn.is_enabled()
            
            print(f"   Bouton {i+1}: '{text}' (visible: {visible}, enabled: {enabled})")
            
            if 'envoyer' in text.lower():
                print(f"   ⭐ BOUTON ENVOYER: '{text}' - Cliquable: {visible and enabled}")
                
                if visible and enabled:
                    print("   🔘 Tentative de clic...")
                    try:
                        btn.click()
                        print("   ✅ Clic réussi!")
                        time.sleep(5)
                        
                        # Vérifier ce qui apparaît après
                        print("\n🔍 CONTENU APRÈS CLIC ENVOYER:")
                        
                        vote_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Vote')]")
                        print(f"   Éléments avec 'Vote': {len(vote_elements)}")
                        for j, elem in enumerate(vote_elements[:5]):
                            print(f"      {j+1}. '{elem.text.strip()[:60]}'")
                            
                        break
                        
                    except Exception as e:
                        print(f"   ❌ Erreur clic: {e}")
        
        print("\n⏸️ Page laissée ouverte pour inspection...")
        input("Appuyez sur Entrée pour fermer...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    simple_test()