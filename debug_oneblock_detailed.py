#!/usr/bin/env python3
"""
Analyse détaillée de la structure des sections de vote
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def debug_detailed():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get("https://oneblock.fr/vote")
        time.sleep(3)
        
        # Remplir pseudo
        pseudo_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
        pseudo_field.send_keys("zCapsLock")
        time.sleep(2)
        
        # Chercher SITE N°1 spécifiquement
        site1_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'SITE N°1')]")
        
        for i, site1 in enumerate(site1_elements):
            print(f"\n🎯 SITE N°1 #{i+1}:")
            print(f"   Texte: '{site1.text}'")
            print(f"   Tag: {site1.tag_name}")
            
            # Chercher le parent container
            try:
                parent = site1.find_element(By.XPATH, "./ancestor::div[contains(@class, 'vote') or contains(@class, 'site') or contains(@class, 'card')][1]")
                print(f"   Parent div class: {parent.get_attribute('class')}")
                
                # Chercher tous les éléments cliquables dans ce parent
                clickables = parent.find_elements(By.XPATH, ".//a | .//button | .//*[@onclick]")
                print(f"   Éléments cliquables dans le parent: {len(clickables)}")
                
                for j, clickable in enumerate(clickables):
                    text = clickable.text.strip()
                    href = clickable.get_attribute('href')
                    onclick = clickable.get_attribute('onclick')
                    tag = clickable.tag_name
                    print(f"      {j+1}. [{tag}] '{text}' -> href: {href}, onclick: {onclick}")
                    
            except Exception as e:
                print(f"   Erreur parent: {e}")
                
        # Essayer de cliquer manuellement
        print("\n🖱️ Tentative de clic automatique...")
        try:
            # Scroller et chercher des boutons vote
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            # Chercher tous les éléments avec "vote" dans différents attributs
            vote_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'vote') or contains(@id, 'vote') or contains(text(), 'Votez')]")
            
            for elem in vote_elements:
                if elem.is_displayed():
                    print(f"   Élément vote visible: '{elem.text}' class: {elem.get_attribute('class')}")
                    
        except Exception as e:
            print(f"Erreur clic: {e}")
                
    finally:
        print("\nNavigateur laissé ouvert pour inspection manuelle...")
        time.sleep(30)  # Laisser 30 secondes pour voir
        driver.quit()

if __name__ == "__main__":
    debug_detailed()