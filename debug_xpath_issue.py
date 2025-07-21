#!/usr/bin/env python3

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_xpath_issue():
    """Debug spécifique pour comprendre pourquoi les XPath ne fonctionnent pas"""
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("=== DEBUG XPATH ISSUE ===")
        
        # Setup oneblock.fr
        driver.get("https://oneblock.fr/vote")
        time.sleep(3)
        
        # Saisir pseudo et cliquer ENVOYER
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
        )
        username_input.clear()
        username_input.send_keys("TestUser123")
        
        envoyer_button = None
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                envoyer_button = btn
                break
        
        if envoyer_button:
            driver.execute_script("arguments[0].click();", envoyer_button)
            time.sleep(5)
        
        # Test différents XPath pour SITE N°1
        logger.info("\n🔍 TEST DIFFÉRENTS XPATH POUR 'SITE N°1':")
        
        xpath_variants = [
            "//*[contains(text(), 'SITE N°1')]",
            "//*[contains(text(), 'SITE N°')]",
            "//*[contains(text(), 'SITE')]",
            "//button[contains(text(), 'SITE N°1')]",
            "//button[contains(text(), 'SITE N°')]",
            "//button[contains(text(), 'Votez maintenant')]",
            "//*[text()[contains(., 'SITE N°1')]]",
            "//*[normalize-space(text())='SITE N°1']",
            "//button[contains(normalize-space(.), 'SITE N°1')]"
        ]
        
        for xpath in xpath_variants:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                logger.info(f"   '{xpath}' -> {len(elements)} éléments")
                
                for i, elem in enumerate(elements[:2]):
                    text = elem.text.strip().replace('\n', ' ')
                    tag = elem.tag_name
                    logger.info(f"      {i+1}. [{tag}] '{text}'")
                    
            except Exception as e:
                logger.error(f"   Erreur XPath '{xpath}': {e}")
        
        # Analyser la structure HTML des boutons vote
        logger.info("\n🔍 ANALYSE STRUCTURE HTML DES BOUTONS VOTE:")
        
        vote_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Votez maintenant')]")
        
        for i, btn in enumerate(vote_buttons):
            logger.info(f"\n   Bouton {i+1}:")
            logger.info(f"      innerHTML: {btn.get_attribute('innerHTML')[:200]}...")
            logger.info(f"      outerHTML: {btn.get_attribute('outerHTML')[:300]}...")
            logger.info(f"      text: '{btn.text}'")
            logger.info(f"      classes: {btn.get_attribute('class')}")
            
            # Chercher les éléments enfants
            children = btn.find_elements(By.XPATH, ".//*")
            logger.info(f"      Enfants: {len(children)}")
            
            for j, child in enumerate(children[:5]):
                child_text = child.text.strip()
                child_tag = child.tag_name
                logger.info(f"         {j+1}. [{child_tag}] '{child_text}'")
        
        # Test de différentes méthodes de clic
        logger.info("\n🔍 TEST DIFFÉRENTES MÉTHODES DE CLIC:")
        
        if vote_buttons:
            first_btn = vote_buttons[0]
            
            # Méthode 1: JavaScript click
            logger.info("   1. Test JavaScript click...")
            try:
                url_before = driver.current_url
                logger.info(f"      URL avant: {url_before}")
                
                driver.execute_script("arguments[0].click();", first_btn)
                time.sleep(3)
                
                url_after = driver.current_url
                logger.info(f"      URL après: {url_after}")
                
                if url_before != url_after:
                    logger.info("      ✅ JavaScript click a marché!")
                    return True
                else:
                    logger.warning("      ⚠️ Pas de redirection avec JavaScript")
                    
                    # Revenir à la page vote
                    driver.get("https://oneblock.fr/vote")
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"      ❌ Erreur JavaScript click: {e}")
            
            # Méthode 2: Click normal
            logger.info("   2. Test click normal...")
            try:
                # Refaire le setup
                username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']")
                username_input.clear()
                username_input.send_keys("TestUser123")
                
                envoyer_button = None
                for btn in driver.find_elements(By.TAG_NAME, "button"):
                    if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                        envoyer_button = btn
                        break
                
                if envoyer_button:
                    driver.execute_script("arguments[0].click();", envoyer_button)
                    time.sleep(5)
                
                vote_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Votez maintenant')]")
                if vote_buttons:
                    first_btn = vote_buttons[0]
                    
                    url_before = driver.current_url
                    logger.info(f"      URL avant: {url_before}")
                    
                    first_btn.click()
                    time.sleep(3)
                    
                    url_after = driver.current_url
                    logger.info(f"      URL après: {url_after}")
                    
                    if url_before != url_after:
                        logger.info("      ✅ Click normal a marché!")
                    else:
                        logger.warning("      ⚠️ Pas de redirection avec click normal")
                        
            except Exception as e:
                logger.error(f"      ❌ Erreur click normal: {e}")
        
        input("\n🔍 Appuyez sur Entrée pour terminer...")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_xpath_issue()