#!/usr/bin/env python3
"""
Debug de la page oneblock.fr/vote APRÈS avoir cliqué sur ENVOYER
Pour voir la structure des liens de vote
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def debug_after_envoyer():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🌐 1. Accès à oneblock.fr/vote...")
        driver.get("https://oneblock.fr/vote")
        time.sleep(3)
        
        print("✏️ 2. Remplissage du pseudo...")
        pseudo_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
        pseudo_field.clear()
        pseudo_field.send_keys("zCapsLock")
        time.sleep(2)
        
        print("🔘 3. Recherche et clic sur ENVOYER...")
        
        # Attendre que le bouton apparaisse
        time.sleep(2)
        
        # Chercher le bouton ENVOYER
        envoyer_btn = None
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
                
        if not envoyer_btn:
            print("❌ Bouton ENVOYER non trouvé!")
            return
            
        envoyer_btn.click()
        print("✅ Clic sur ENVOYER effectué")
        time.sleep(5)
        
        print("\n🔍 4. ANALYSE APRÈS CLIC ENVOYER:")
        
        # Chercher tous les éléments contenant "SITE"
        site_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'SITE')]")
        print(f"\n📍 Éléments contenant 'SITE': {len(site_elements)}")
        for i, elem in enumerate(site_elements):
            text = elem.text.strip()
            tag = elem.tag_name
            classes = elem.get_attribute('class')
            print(f"   {i+1}. [{tag}] '{text[:80]}...' classes: {classes}")
        
        # Chercher spécifiquement SITE N°1
        site1_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'SITE N°1')]")
        print(f"\n🎯 Éléments 'SITE N°1': {len(site1_elements)}")
        
        for i, site1 in enumerate(site1_elements):
            print(f"\n   SITE N°1 #{i+1}:")
            print(f"      Texte: '{site1.text}'")
            print(f"      Tag: {site1.tag_name}")
            print(f"      Classes: {site1.get_attribute('class')}")
            
            # Chercher le parent et analyser sa structure
            try:
                # Essayer différents niveaux de parents
                for level in range(1, 4):
                    try:
                        parent = site1.find_element(By.XPATH, f"./ancestor::*[{level}]")
                        parent_tag = parent.tag_name
                        parent_classes = parent.get_attribute('class')
                        parent_href = parent.get_attribute('href')
                        parent_onclick = parent.get_attribute('onclick')
                        
                        print(f"      Parent niveau {level}: [{parent_tag}] classes: {parent_classes}")
                        if parent_href:
                            print(f"         href: {parent_href}")
                        if parent_onclick:
                            print(f"         onclick: {parent_onclick}")
                            
                        # Chercher des liens dans ce parent
                        links_in_parent = parent.find_elements(By.TAG_NAME, "a")
                        if links_in_parent:
                            print(f"         Liens dans parent: {len(links_in_parent)}")
                            for j, link in enumerate(links_in_parent):
                                href = link.get_attribute('href')
                                text = link.text.strip()
                                print(f"            Lien {j+1}: '{text}' -> {href}")
                                
                    except:
                        break
                        
            except Exception as e:
                print(f"      Erreur analyse parent: {e}")
        
        # Chercher tous les liens contenant "vote"
        vote_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'vote') or contains(text(), 'Vote') or contains(text(), 'vote')]")
        print(f"\n🗳️ Tous les liens de vote: {len(vote_links)}")
        for i, link in enumerate(vote_links):
            href = link.get_attribute('href')
            text = link.text.strip()
            visible = link.is_displayed()
            print(f"   {i+1}. '{text}' -> {href} (visible: {visible})")
        
        # Chercher spécifiquement "Votez maintenant"
        votez_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Votez maintenant')]")
        print(f"\n🎯 Éléments 'Votez maintenant': {len(votez_elements)}")
        for i, elem in enumerate(votez_elements):
            text = elem.text.strip()
            tag = elem.tag_name
            href = elem.get_attribute('href')
            onclick = elem.get_attribute('onclick')
            visible = elem.is_displayed()
            classes = elem.get_attribute('class')
            
            print(f"   {i+1}. [{tag}] '{text}' (visible: {visible})")
            print(f"      href: {href}")
            print(f"      onclick: {onclick}")
            print(f"      classes: {classes}")
        
        # Vérifier s'il faut d'abord s'authentifier
        auth_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Connectez-vous') or contains(text(), 'connexion') or contains(text(), 'login')]")
        if auth_elements:
            print(f"\n🔐 Éléments d'authentification trouvés: {len(auth_elements)}")
            for i, elem in enumerate(auth_elements):
                text = elem.text.strip()
                print(f"   {i+1}. '{text}'")
        
        print("\n⏸️ Page laissée ouverte pour inspection manuelle...")
        input("Appuyez sur Entrée pour fermer...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_after_envoyer()