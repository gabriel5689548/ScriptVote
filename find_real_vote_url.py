#!/usr/bin/env python3
"""
Chercher la vraie URL de vote sur serveur-prive.net
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def find_real_vote_url():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🔍 Recherche de la vraie URL de vote sur serveur-prive.net...")
        
        # Aller sur la page principale
        driver.get("https://serveur-prive.net/")
        time.sleep(5)
        
        print("🔍 Page principale chargée, recherche de 'oneblock'...")
        
        # Chercher tous les liens contenant "oneblock"
        oneblock_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'oneblock') or contains(text(), 'oneblock')]")
        
        print(f"   Liens 'oneblock' trouvés: {len(oneblock_links)}")
        
        for i, link in enumerate(oneblock_links):
            href = link.get_attribute('href')
            text = link.text.strip()
            print(f"   {i+1}. '{text}' -> {href}")
            
            # Si on trouve un lien prometeur, l'explorer
            if href and 'oneblock' in href.lower():
                print(f"\n🧪 Test du lien: {href}")
                
                try:
                    # Ouvrir dans un nouvel onglet
                    driver.execute_script("window.open(arguments[0], '_blank');", href)
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(3)
                    
                    current_url = driver.current_url
                    title = driver.title
                    
                    print(f"   URL finale: {current_url}")
                    print(f"   Titre: {title}")
                    
                    # Chercher MTCaptcha
                    page_source = driver.page_source
                    if 'MTPublic-' in page_source:
                        import re
                        sitekey_match = re.search(r'MTPublic-[a-zA-Z0-9]+', page_source)
                        if sitekey_match:
                            print(f"   ✅ SITEKEY TROUVÉE: {sitekey_match.group(0)}")
                    
                    # Chercher des champs de vote
                    username_fields = driver.find_elements(By.CSS_SELECTOR, "input[name='username'], input[name='pseudo'], input[placeholder*='pseudo' i]")
                    vote_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'vote') or contains(text(), 'Vote')] | //input[@type='submit']")
                    
                    print(f"   Champs username: {len(username_fields)}")
                    print(f"   Boutons vote: {len(vote_buttons)}")
                    
                    # Si on trouve des éléments de vote, c'est prometteur
                    if 'MTPublic-' in page_source and username_fields:
                        print(f"   🎉 BINGO! URL de vote fonctionnelle trouvée: {current_url}")
                        
                        # Fermer cet onglet et retourner au principal
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        return current_url
                    
                    # Fermer cet onglet
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                except Exception as e:
                    print(f"   ❌ Erreur test lien: {e}")
                    # S'assurer qu'on revient au bon onglet
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
        
        # Si pas trouvé via les liens, essayer de chercher dans le contenu de la page
        print(f"\n🔍 Recherche dans le contenu de la page...")
        
        # Chercher le texte "oneblock" dans la page
        page_text = driver.page_source.lower()
        if 'oneblock' in page_text:
            print("   Texte 'oneblock' trouvé dans la page")
            
            # Essayer de trouver des URLs dans le texte
            import re
            url_pattern = r'https?://[^\s<>"\']+oneblock[^\s<>"\']+'
            urls_found = re.findall(url_pattern, page_text, re.IGNORECASE)
            
            if urls_found:
                print(f"   URLs oneblock trouvées dans le texte: {len(urls_found)}")
                for url in set(urls_found):  # Éliminer les doublons
                    print(f"      {url}")
        
        # Essayer aussi une recherche sur la page
        try:
            search_box = driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[name='search'], input[placeholder*='search' i]")
            if search_box:
                print(f"\n🔍 Tentative de recherche 'oneblock' sur le site...")
                search_box.clear()
                search_box.send_keys("oneblock")
                
                # Chercher un bouton de recherche
                search_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'search') or contains(text(), 'Search')] | //input[@type='submit']")
                if search_buttons:
                    search_buttons[0].click()
                    time.sleep(3)
                    
                    # Analyser les résultats
                    result_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'oneblock')]")
                    print(f"   Résultats de recherche: {len(result_links)}")
                    
                    for i, link in enumerate(result_links[:5]):  # Limiter à 5 résultats
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        print(f"      {i+1}. '{text}' -> {href}")
                        
        except:
            print("   Pas de fonction de recherche trouvée")
        
        print(f"\n❌ Aucune URL de vote oneblock fonctionnelle trouvée")
        return None
        
    finally:
        print("\n⏸️ Navigateur laissé ouvert pour inspection...")
        input("Appuyez sur Entrée pour fermer...")
        driver.quit()

if __name__ == "__main__":
    real_url = find_real_vote_url()
    if real_url:
        print(f"\n✅ URL de vote trouvée: {real_url}")
    else:
        print(f"\n❌ Aucune URL de vote trouvée - il faut que l'utilisateur fournisse la bonne URL")