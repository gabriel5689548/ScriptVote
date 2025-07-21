#!/usr/bin/env python3

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_button_click():
    """Test pour forcer le clic sur le vrai bouton SITE N°1 et attendre la redirection"""
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("=== TEST CLIC RÉEL SUR BOUTON SITE N°1 ===")
        
        # Setup oneblock.fr
        logger.info("🌐 Accès à https://oneblock.fr/vote")
        driver.get("https://oneblock.fr/vote")
        time.sleep(3)
        
        # Saisir pseudo et cliquer ENVOYER
        logger.info("📝 Setup du vote...")
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
        )
        username_input.clear()
        username_input.send_keys("TestUser456")
        
        # Cliquer ENVOYER
        envoyer_button = None
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                envoyer_button = btn
                break
        
        if envoyer_button:
            driver.execute_script("arguments[0].click();", envoyer_button)
            logger.info("✅ ENVOYER cliqué")
            time.sleep(5)
        
        # Trouver le bouton SITE N°1 spécifiquement
        logger.info("🔍 Recherche du bouton SITE N°1...")
        site1_button = None
        
        # Chercher tous les boutons
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in all_buttons:
            text = btn.text.strip()
            if "SITE N°1" in text and "Votez maintenant" in text and btn.is_displayed():
                site1_button = btn
                logger.info(f"🎯 Bouton SITE N°1 trouvé: '{text}'")
                break
        
        if not site1_button:
            logger.error("❌ Bouton SITE N°1 non trouvé")
            return
        
        # Analyser l'état avant clic
        logger.info("\n📊 ÉTAT AVANT CLIC:")
        button_text_before = site1_button.text.strip()
        button_classes_before = site1_button.get_attribute('class')
        url_before = driver.current_url
        
        logger.info(f"   Texte bouton: '{button_text_before}'")
        logger.info(f"   Classes bouton: {button_classes_before}")
        logger.info(f"   URL: {url_before}")
        
        # Cliquer et surveiller INTENSIVEMENT
        logger.info("\n🖱️ CLIC SUR SITE N°1 ET SURVEILLANCE:")
        
        # Scroller vers le bouton
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", site1_button)
        time.sleep(2)
        
        # CLIC
        site1_button.click()
        logger.info("✅ Clic effectué sur SITE N°1")
        
        # Surveiller pendant 30 secondes
        for wait_time in range(1, 31):
            time.sleep(1)
            
            # Vérifier URL
            current_url = driver.current_url
            if current_url != url_before:
                logger.info(f"🎉 REDIRECTION DÉTECTÉE après {wait_time}s!")
                logger.info(f"   Nouvelle URL: {current_url}")
                
                # Vérifier si c'est le bon site
                if 'serveur-prive.net' in current_url:
                    logger.info("🎯 SUCCÈS: Redirection vers serveur-prive.net!")
                    
                    # Vérifier si le pseudo est prérempli
                    time.sleep(3)
                    try:
                        username_fields = driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[id*='username'], input[placeholder*='pseudo']")
                        for field in username_fields:
                            if field.is_displayed():
                                value = field.get_attribute('value')
                                placeholder = field.get_attribute('placeholder')
                                if value and value.strip():
                                    logger.info(f"✅ PSEUDONYME PRÉREMPLI: '{value}'")
                                    return True
                                else:
                                    logger.info(f"📝 Champ username vide: value='{value}', placeholder='{placeholder}'")
                    except Exception as e:
                        logger.debug(f"Erreur vérification pseudonyme: {e}")
                        
                break
            
            # Vérifier changement de texte du bouton
            try:
                new_button_text = site1_button.text.strip()
                if new_button_text != button_text_before:
                    logger.info(f"🔄 Texte bouton changé (t={wait_time}s): '{new_button_text}'")
                    button_text_before = new_button_text
            except Exception:
                # Le bouton n'existe peut-être plus
                logger.info(f"⚠️ Bouton non accessible (t={wait_time}s) - possible redirection")
            
            if wait_time % 5 == 0:
                logger.info(f"   ⏳ Attente {wait_time}s... URL: {current_url}")
        
        # État final
        final_url = driver.current_url
        logger.info(f"\n📊 ÉTAT FINAL:")
        logger.info(f"   URL finale: {final_url}")
        
        if final_url == url_before:
            logger.warning("❌ Aucune redirection après 30s")
            
            # Vérifier l'état du bouton
            try:
                final_button_text = site1_button.text.strip()
                logger.info(f"   Texte final du bouton: '{final_button_text}'")
            except:
                logger.info("   Bouton non accessible")
        else:
            logger.info("✅ Redirection a eu lieu")
        
        input("\n🔍 Vérifiez manuellement oneblock.fr/vote pour voir l'état des boutons, puis appuyez sur Entrée...")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_real_button_click()