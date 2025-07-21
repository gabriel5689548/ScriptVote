#!/usr/bin/env python3
"""
Extraire les vraies URLs de vote depuis oneblock.fr après avoir cliqué sur ENVOYER
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def extract_real_vote_urls():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🌐 1. Accès à oneblock.fr/vote...")
        driver.get("https://oneblock.fr/vote")
        time.sleep(5)
        
        print("✏️ 2. Remplissage du pseudo...")
        pseudo_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
        pseudo_field.clear()
        pseudo_field.send_keys("zCapsLock")
        time.sleep(2)
        
        print("🔘 3. Recherche et clic sur ENVOYER...")
        
        # Chercher le bouton ENVOYER avec plusieurs méthodes
        envoyer_btn = None
        
        # Méthode 1: XPath direct
        xpath_selectors = [
            "//button[contains(text(), 'ENVOYER')]",
            "//button[contains(text(), 'Envoyer')]", 
            "//input[@value='ENVOYER']",
            "//input[@value='Envoyer']"
        ]
        
        for xpath in xpath_selectors:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        envoyer_btn = elem
                        print(f"   Bouton trouvé: '{elem.text.strip()}'")
                        break
                if envoyer_btn:
                    break
            except:
                continue
        
        # Méthode 2: Parcourir tous les boutons
        if not envoyer_btn:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                text = btn.text.strip().lower()
                if 'envoyer' in text and btn.is_displayed() and btn.is_enabled():
                    envoyer_btn = btn
                    print(f"   Bouton trouvé via scan: '{btn.text.strip()}'")
                    break
        
        if not envoyer_btn:
            print("❌ Bouton ENVOYER non trouvé!")
            return
        
        # Cliquer sur le bouton
        try:
            envoyer_btn.click()
            print("✅ Clic normal réussi")
        except Exception as e:
            if "click intercepted" in str(e):
                print("⚠️ Clic intercepté, utilisation de JavaScript...")
                driver.execute_script("arguments[0].click();", envoyer_btn)
                print("✅ Clic JavaScript réussi")
            else:
                print(f"❌ Erreur clic: {e}")
                return
        
        time.sleep(5)
        print("✅ Clic ENVOYER effectué")
        
        print("\n🔍 4. EXTRACTION DES VRAIES URLs DE VOTE:")
        
        # Chercher TOUS les liens après le clic
        all_links = driver.find_elements(By.TAG_NAME, "a")
        print(f"   Total liens trouvés: {len(all_links)}")
        
        vote_urls = []
        
        for i, link in enumerate(all_links):
            href = link.get_attribute('href')
            text = link.text.strip()
            visible = link.is_displayed()
            
            if href and visible:
                # Filtrer les liens externes (pas oneblock.fr)
                if 'oneblock.fr' not in href and 'javascript:' not in href and href.startswith('http'):
                    print(f"\n   Lien externe #{len(vote_urls)+1}:")
                    print(f"      Texte: '{text}'")
                    print(f"      URL: {href}")
                    print(f"      Visible: {visible}")
                    
                    # Vérifier si c'est un lien de vote
                    if any(keyword in text.lower() for keyword in ['vote', 'votez']):
                        print(f"      🎯 LIEN DE VOTE IDENTIFIÉ!")
                        vote_urls.append({
                            'text': text,
                            'url': href,
                            'element': link
                        })
        
        print(f"\n📊 RÉSUMÉ:")
        print(f"   Liens de vote trouvés: {len(vote_urls)}")
        
        # Tester chaque URL de vote
        for i, vote_info in enumerate(vote_urls):
            print(f"\n🧪 Test URL de vote #{i+1}: {vote_info['text']}")
            print(f"   URL: {vote_info['url']}")
            
            try:
                # Ouvrir dans un nouvel onglet pour tester
                driver.execute_script("window.open(arguments[0], '_blank');", vote_info['url'])
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(5)
                
                current_url = driver.current_url
                title = driver.title
                
                print(f"   URL finale: {current_url}")
                print(f"   Titre: {title}")
                
                # Vérifier MTCaptcha
                page_source = driver.page_source
                if 'MTPublic-' in page_source:
                    import re
                    sitekey_match = re.search(r'MTPublic-[a-zA-Z0-9]+', page_source)
                    if sitekey_match:
                        print(f"   ✅ SITEKEY TROUVÉE: {sitekey_match.group(0)}")
                
                # Vérifier champs username
                username_fields = driver.find_elements(By.CSS_SELECTOR, "input[name='username'], input[name='pseudo'], input[placeholder*='pseudo' i]")
                print(f"   Champs username: {len(username_fields)}")
                
                # Vérifier formulaires de vote
                vote_forms = driver.find_elements(By.TAG_NAME, "form")
                vote_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'vote') or contains(text(), 'Vote')] | //input[@type='submit']")
                print(f"   Formulaires: {len(vote_forms)}")
                print(f"   Boutons vote: {len(vote_buttons)}")
                
                # Si on trouve MTCaptcha + username field, c'est probablement bon!
                if 'MTPublic-' in page_source and username_fields:
                    print(f"   🎉 BINGO! Cette URL semble être fonctionnelle pour le vote!")
                
                # Fermer cet onglet et revenir au principal
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
            except Exception as e:
                print(f"   ❌ Erreur test URL: {e}")
                # S'assurer qu'on est sur le bon onglet
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
        
        # Si on n'a pas trouvé de liens de vote, essayer de cliquer sur les boutons désactivés
        if not vote_urls:
            print(f"\n🔄 Aucun lien de vote trouvé, test des boutons désactivés...")
            
            site_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'SITE N°1') or contains(text(), 'SITE N°2')]")
            
            for i, site_btn in enumerate(site_buttons):
                try:
                    text = site_btn.text.strip()
                    print(f"\n   Test bouton site #{i+1}: '{text[:30]}...'")
                    
                    # Essayer de cliquer même si désactivé
                    driver.execute_script("arguments[0].click();", site_btn)
                    time.sleep(3)
                    
                    # Vérifier si on a été redirigé
                    current_url = driver.current_url
                    if 'oneblock.fr' not in current_url:
                        print(f"   ✅ Redirection réussie vers: {current_url}")
                        
                        # Analyser la page
                        if 'MTPublic-' in driver.page_source:
                            print(f"   🎉 Page avec MTCaptcha trouvée!")
                    else:
                        print(f"   ⚠️ Pas de redirection")
                        
                except Exception as e:
                    print(f"   ❌ Erreur clic bouton: {e}")
        
        print("\n⏸️ Page laissée ouverte pour inspection finale...")
        input("Appuyez sur Entrée pour fermer...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    extract_real_vote_urls()