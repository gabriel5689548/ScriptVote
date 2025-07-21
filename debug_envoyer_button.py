#!/usr/bin/env python3
"""
Debug spécifique du bouton ENVOYER sur oneblock.fr/vote
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_envoyer_button():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🌐 1. Accès à oneblock.fr/vote...")
        driver.get("https://oneblock.fr/vote")
        time.sleep(3)
        
        print("✏️ 2. Remplissage du pseudo...")
        pseudo_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
        pseudo_field.clear()
        pseudo_field.send_keys("zCapsLock")
        print("✅ Pseudo 'zCapsLock' saisi")
        time.sleep(2)
        
        print("\n🔍 3. ANALYSE COMPLÈTE DU BOUTON ENVOYER:")
        
        # Méthode 1: Chercher tous les boutons
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\n📊 Total boutons trouvés: {len(all_buttons)}")
        
        envoyer_buttons = []
        for i, btn in enumerate(all_buttons):
            text = btn.text.strip()
            visible = btn.is_displayed()
            enabled = btn.is_enabled()
            classes = btn.get_attribute('class')
            onclick = btn.get_attribute('onclick')
            
            print(f"   Bouton {i+1}: '{text}' | Visible: {visible} | Enabled: {enabled}")
            print(f"      Classes: {classes}")
            print(f"      OnClick: {onclick}")
            
            if 'envoyer' in text.lower():
                envoyer_buttons.append(btn)
                print(f"      ✅ BOUTON ENVOYER IDENTIFIÉ!")
        
        if not envoyer_buttons:
            print("\n❌ Aucun bouton avec 'envoyer' trouvé dans le texte")
            
            # Chercher avec XPath plus large
            xpath_patterns = [
                "//button[contains(text(), 'Envoyer')]",
                "//button[contains(text(), 'ENVOYER')]",
                "//input[@value='Envoyer']",
                "//input[@value='ENVOYER']",
                "//button[contains(@onclick, 'submit')]",
                "//input[contains(@onclick, 'submit')]"
            ]
            
            for pattern in xpath_patterns:
                try:
                    elements = driver.find_elements(By.XPATH, pattern)
                    if elements:
                        print(f"\n🎯 Trouvé avec pattern '{pattern}': {len(elements)} élément(s)")
                        envoyer_buttons.extend(elements)
                except Exception as e:
                    print(f"   Erreur pattern '{pattern}': {e}")
        
        print(f"\n🎯 Total boutons ENVOYER candidats: {len(envoyer_buttons)}")
        
        # Tester chaque bouton candidat
        for i, btn in enumerate(envoyer_buttons):
            print(f"\n🧪 TEST BOUTON ENVOYER #{i+1}:")
            
            try:
                # Informations détaillées
                text = btn.text.strip()
                tag = btn.tag_name
                visible = btn.is_displayed()
                enabled = btn.is_enabled()
                clickable = btn.is_enabled() and btn.is_displayed()
                location = btn.location
                size = btn.size
                
                print(f"   Texte: '{text}'")
                print(f"   Tag: {tag}")
                print(f"   Visible: {visible}")
                print(f"   Enabled: {enabled}")
                print(f"   Clickable: {clickable}")
                print(f"   Position: {location}")
                print(f"   Taille: {size}")
                
                if not clickable:
                    print("   ⚠️ Bouton non cliquable - ignoré")
                    continue
                
                # Scroller vers l'élément
                print("   📍 Scroll vers l'élément...")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                time.sleep(2)
                
                # Vérifier si toujours visible après scroll
                if not btn.is_displayed():
                    print("   ⚠️ Élément plus visible après scroll")
                    continue
                
                # Surligner l'élément pour debug visuel
                driver.execute_script("arguments[0].style.border='3px solid red';", btn)
                time.sleep(1)
                
                # Test 1: Clic normal
                print("   🖱️ Test 1: Clic normal...")
                try:
                    btn.click()
                    print("   ✅ Clic normal réussi!")
                    time.sleep(3)
                    
                    # Vérifier si ça a marché (sites de vote apparaissent)
                    vote_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Votez maintenant')]")
                    if vote_elements:
                        print(f"   🎉 SUCCÈS! Sites de vote détectés: {len(vote_elements)}")
                        break
                    else:
                        print("   ⚠️ Pas de sites de vote après clic normal")
                        
                except Exception as e:
                    print(f"   ❌ Clic normal échoué: {e}")
                
                # Test 2: Clic JavaScript
                print("   🖱️ Test 2: Clic JavaScript...")
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    print("   ✅ Clic JavaScript réussi!")
                    time.sleep(3)
                    
                    # Vérifier résultat
                    vote_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Votez maintenant')]")
                    if vote_elements:
                        print(f"   🎉 SUCCÈS! Sites de vote détectés: {len(vote_elements)}")
                        break
                    else:
                        print("   ⚠️ Pas de sites de vote après clic JS")
                        
                except Exception as e:
                    print(f"   ❌ Clic JavaScript échoué: {e}")
                
                # Test 3: Simuler submit du form parent
                print("   🖱️ Test 3: Submit du formulaire parent...")
                try:
                    form = btn.find_element(By.XPATH, "./ancestor::form[1]")
                    if form:
                        driver.execute_script("arguments[0].submit();", form)
                        print("   ✅ Submit formulaire réussi!")
                        time.sleep(3)
                        
                        vote_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Votez maintenant')]")
                        if vote_elements:
                            print(f"   🎉 SUCCÈS! Sites de vote détectés: {len(vote_elements)}")
                            break
                        else:
                            print("   ⚠️ Pas de sites de vote après submit form")
                    else:
                        print("   ⚠️ Pas de formulaire parent trouvé")
                        
                except Exception as e:
                    print(f"   ❌ Submit formulaire échoué: {e}")
                
            except Exception as e:
                print(f"   ❌ Erreur générale bouton #{i+1}: {e}")
                continue
        
        print("\n🔍 4. VÉRIFICATION FINALE DE LA PAGE:")
        
        # Chercher les sites de vote
        vote_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Votez maintenant') or contains(text(), 'Vote')]")
        print(f"   Éléments 'Vote' trouvés: {len(vote_elements)}")
        
        for i, elem in enumerate(vote_elements):
            text = elem.text.strip()[:50]
            href = elem.get_attribute('href')
            print(f"      {i+1}. '{text}' -> {href}")
        
        # Laisser la page ouverte pour inspection
        print("\n⏸️ Page laissée ouverte pour inspection manuelle...")
        print("Vérifiez si les sites de vote sont visibles dans le navigateur.")
        input("Appuyez sur Entrée pour fermer...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_envoyer_button()