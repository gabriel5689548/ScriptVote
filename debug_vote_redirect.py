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

def debug_vote_redirect():
    """Debug pour voir exactement ce qui se passe lors du clic sur Votez maintenant"""
    
    # Configuration Chrome avec logging des requêtes
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")
    
    # Activer le logging des requêtes réseau
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL', 'browser': 'ALL'})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("=== DEBUG REDIRECTION VOTE ===")
        
        # Activer l'interception des requêtes réseau
        driver.execute_cdp_cmd('Network.enable', {})
        
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
        username_input.send_keys("TestUser123")
        
        envoyer_button = None
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                envoyer_button = btn
                break
        
        if envoyer_button:
            driver.execute_script("arguments[0].click();", envoyer_button)
            logger.info("✅ ENVOYER cliqué")
            time.sleep(5)
        
        # Trouver le bouton "Votez maintenant"
        logger.info("\n🔍 RECHERCHE DU BOUTON VOTEZ MAINTENANT:")
        vote_buttons = []
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        
        for btn in all_buttons:
            text = btn.text.strip()
            if "Votez maintenant" in text and "SITE" in text and btn.is_displayed():
                vote_buttons.append(btn)
                logger.info(f"   Bouton trouvé: '{text}'")
        
        if not vote_buttons:
            logger.error("❌ Aucun bouton 'Votez maintenant' trouvé")
            return
        
        vote_button = vote_buttons[0]
        
        # Analyser les attributs du bouton
        logger.info(f"\n🔍 ANALYSE DU BOUTON:")
        logger.info(f"   Texte: '{vote_button.text}'")
        logger.info(f"   Tag: {vote_button.tag_name}")
        logger.info(f"   Classes: {vote_button.get_attribute('class')}")
        logger.info(f"   onClick: {vote_button.get_attribute('onclick')}")
        logger.info(f"   Data attributes:")
        
        # Vérifier tous les attributs data-*
        driver.execute_script("""
            var elem = arguments[0];
            var attrs = elem.attributes;
            for (var i = 0; i < attrs.length; i++) {
                if (attrs[i].name.startsWith('data-')) {
                    console.log('   ' + attrs[i].name + ': ' + attrs[i].value);
                }
            }
        """, vote_button)
        
        # Analyser le HTML du bouton
        html = vote_button.get_attribute('outerHTML')
        logger.info(f"   HTML: {html[:200]}...")
        
        # Chercher des liens cachés ou des URLs dans les attributs
        potential_urls = []
        all_attrs = driver.execute_script("""
            var elem = arguments[0];
            var attrs = {};
            for (var i = 0; i < elem.attributes.length; i++) {
                attrs[elem.attributes[i].name] = elem.attributes[i].value;
            }
            return attrs;
        """, vote_button)
        
        logger.info(f"   Tous les attributs: {all_attrs}")
        
        # Vérifier s'il y a des URLs dans les attributs
        for attr_name, attr_value in all_attrs.items():
            if attr_value and ('http' in str(attr_value) or 'serveur-prive' in str(attr_value)):
                potential_urls.append((attr_name, attr_value))
                logger.info(f"   🎯 URL potentielle trouvée: {attr_name}='{attr_value}'")
        
        # Analyser le JavaScript/événements attachés
        logger.info(f"\n🔍 ANALYSE DES ÉVÉNEMENTS:")
        
        # Vérifier les event listeners
        try:
            listeners = driver.execute_script("""
                var elem = arguments[0];
                return getEventListeners ? getEventListeners(elem) : 'getEventListeners not available';
            """, vote_button)
            logger.info(f"   Event listeners: {listeners}")
        except Exception as e:
            logger.debug(f"Erreur event listeners: {e}")
        
        # Tester le clic et capturer toutes les requêtes
        logger.info(f"\n🖱️ TEST DE CLIC AVEC CAPTURE RÉSEAU:")
        
        url_before = driver.current_url
        logger.info(f"   URL avant clic: {url_before}")
        
        # Vider les logs réseau
        driver.get_log('performance')
        
        # Cliquer sur le bouton
        logger.info("   Clic sur le bouton...")
        vote_button.click()
        
        # Capturer les requêtes pendant 10 secondes
        for wait_time in range(1, 11):
            time.sleep(1)
            current_url = driver.current_url
            
            # Récupérer les logs de performance (requêtes réseau)
            logs = driver.get_log('performance')
            new_requests = []
            
            for log in logs:
                try:
                    message = log['message']
                    if 'Network.request' in message or 'Network.response' in message:
                        import json
                        log_data = json.loads(message)
                        if 'params' in log_data and 'request' in log_data['params']:
                            url = log_data['params']['request']['url']
                            method = log_data['params']['request']['method']
                            new_requests.append(f"{method} {url}")
                except Exception:
                    continue
            
            if new_requests:
                logger.info(f"   Nouvelles requêtes (t={wait_time}s):")
                for req in new_requests[-5:]:  # Dernières 5 requêtes
                    logger.info(f"      {req}")
            
            if current_url != url_before:
                logger.info(f"   🎉 REDIRECTION DÉTECTÉE après {wait_time}s!")
                logger.info(f"   🎯 Nouvelle URL: {current_url}")
                
                # Vérifier si le pseudonyme est prérempli
                time.sleep(2)
                try:
                    username_fields = driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[id*='username'], input[placeholder*='pseudo']")
                    for field in username_fields:
                        if field.is_displayed():
                            value = field.get_attribute('value')
                            placeholder = field.get_attribute('placeholder')
                            logger.info(f"   📝 Champ username: value='{value}', placeholder='{placeholder}'")
                            if value and value.strip():
                                logger.info(f"   ✅ PSEUDONYME PRÉREMPLI: '{value}'")
                                return True
                except Exception as e:
                    logger.debug(f"Erreur vérification pseudonyme: {e}")
                
                break
            
            logger.info(f"   Attente... {wait_time}s (URL: {current_url})")
        
        logger.info(f"   URL finale: {driver.current_url}")
        
        if driver.current_url == url_before:
            logger.warning("   ⚠️ Aucune redirection détectée")
            
            # Vérifier si le bouton a changé
            try:
                new_text = vote_button.text.strip()
                logger.info(f"   Nouveau texte du bouton: '{new_text}'")
            except Exception:
                pass
        
        input("\n🔍 Appuyez sur Entrée pour terminer...")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_vote_redirect()