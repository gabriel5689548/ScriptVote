#!/usr/bin/env python3
"""
Script de debug pour analyser la structure de oneblock.fr/vote
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def debug_oneblock():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🌐 Accès à oneblock.fr/vote...")
        driver.get("https://oneblock.fr/vote")
        time.sleep(5)
        
        # Remplir le pseudo
        pseudo_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
        pseudo_field.clear()
        pseudo_field.send_keys("zCapsLock")
        print("✅ Pseudo 'zCapsLock' saisi")
        time.sleep(2)
        
        # Analyser la structure
        print("\n🔍 ANALYSE DE LA STRUCTURE:")
        
        # Chercher tous les éléments avec "site"
        site_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'site') or contains(text(), 'Site')]")
        print(f"\n📍 Éléments contenant 'site': {len(site_elements)}")
        for i, elem in enumerate(site_elements[:5]):
            print(f"   {i+1}. '{elem.text.strip()[:100]}'")
            
        # Chercher tous les liens et boutons
        all_links = driver.find_elements(By.TAG_NAME, "a")
        print(f"\n🔗 Tous les liens: {len(all_links)}")
        for i, link in enumerate(all_links[:10]):
            href = link.get_attribute('href')
            text = link.text.strip()
            if text and len(text) < 100:
                print(f"   {i+1}. '{text}' -> {href}")
                
        # Chercher spécifiquement "Votez maintenant"
        vote_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Votez') or contains(text(), 'Vote')]")
        print(f"\n🗳️ Éléments avec 'Vote': {len(vote_elements)}")
        for i, elem in enumerate(vote_elements):
            text = elem.text.strip()
            href = elem.get_attribute('href')
            onclick = elem.get_attribute('onclick')
            print(f"   {i+1}. '{text}' -> href: {href}, onclick: {onclick}")
            
        # Laisser la page ouverte pour inspection manuelle
        print("\n⏸️ Page ouverte pour inspection manuelle...")
        input("Appuyez sur Entrée pour continuer...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_oneblock()