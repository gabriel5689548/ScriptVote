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

def debug_dynamic_content():
    """Debug pour comprendre si le contenu est dans iframe ou généré dynamiquement"""
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("=== DEBUG CONTENU DYNAMIQUE ===")
        
        # Setup oneblock.fr
        driver.get("https://oneblock.fr/vote")
        time.sleep(3)
        
        # 1. Vérifier les iframes
        logger.info("\n1️⃣ RECHERCHE D'IFRAMES:")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        logger.info(f"   Nombre d'iframes trouvées: {len(iframes)}")
        
        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute('src')
            id_attr = iframe.get_attribute('id')
            name = iframe.get_attribute('name')
            logger.info(f"   Iframe {i+1}: id='{id_attr}', name='{name}', src='{src}'")
        
        # 2. Vérifier shadow DOM
        logger.info("\n2️⃣ RECHERCHE DE SHADOW DOM:")
        try:
            shadow_hosts = driver.execute_script("""
                var hosts = [];
                function findShadowHosts(element) {
                    if (element.shadowRoot) {
                        hosts.push(element.tagName + (element.id ? '#' + element.id : '') + (element.className ? '.' + element.className.split(' ').join('.') : ''));
                    }
                    for (var child of element.children) {
                        findShadowHosts(child);
                    }
                }
                findShadowHosts(document.body);
                return hosts;
            """)
            logger.info(f"   Shadow DOM hosts trouvés: {shadow_hosts}")
        except Exception as e:
            logger.debug(f"Erreur shadow DOM: {e}")
        
        # 3. Attendre le chargement et refaire le setup
        logger.info("\n3️⃣ SETUP ONEBLOCK AVEC ATTENTE:")
        
        # Saisir pseudo
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
        )
        username_input.clear()
        username_input.send_keys("TestUser123")
        logger.info("   ✅ Pseudo saisi")
        
        # Attendre que les boutons soient chargés AVANT de cliquer ENVOYER
        logger.info("   ⏳ Attente du chargement des boutons...")
        time.sleep(3)
        
        # Compter les boutons AVANT ENVOYER
        buttons_before = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"   Boutons AVANT ENVOYER: {len(buttons_before)}")
        
        for i, btn in enumerate(buttons_before):
            text = btn.text.strip()[:50]
            is_displayed = btn.is_displayed()
            logger.info(f"      {i+1}. '{text}' - Visible: {is_displayed}")
        
        # Cliquer ENVOYER
        envoyer_button = None
        for btn in buttons_before:
            if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                envoyer_button = btn
                break
        
        if envoyer_button:
            logger.info("   🔘 Clic sur ENVOYER...")
            driver.execute_script("arguments[0].click();", envoyer_button)
            
            # Attendre explicitement le changement
            for wait_time in [1, 3, 5, 10]:
                time.sleep(wait_time - (wait_time - 1) if wait_time > 1 else wait_time)
                
                logger.info(f"   📊 État après {wait_time}s:")
                
                # Compter tous les boutons
                buttons_after = driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"      Total boutons: {len(buttons_after)}")
                
                # Chercher spécifiquement les boutons avec "Votez" ou "SITE"
                vote_related = []
                for btn in buttons_after:
                    text = btn.text.strip()
                    if any(keyword in text for keyword in ['Votez', 'SITE', 'maintenant']):
                        vote_related.append((btn, text))
                        logger.info(f"      🎯 Bouton vote: '{text}' - Visible: {btn.is_displayed()}")
                
                # Test XPath à ce moment
                xpath_results = []
                test_xpaths = [
                    "//button[contains(text(), 'Votez')]",
                    "//button[contains(text(), 'SITE')]",
                    "//*[contains(text(), 'maintenant')]"
                ]
                
                for xpath in test_xpaths:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        xpath_results.append((xpath, len(elements)))
                        logger.info(f"      XPath '{xpath}': {len(elements)} éléments")
                    except Exception as e:
                        logger.debug(f"Erreur XPath {xpath}: {e}")
                
                # Si on trouve des boutons, essayer de cliquer
                if vote_related:
                    logger.info(f"      ✅ {len(vote_related)} boutons de vote trouvés!")
                    
                    # Test de clic sur le premier
                    first_vote_btn, first_text = vote_related[0]
                    logger.info(f"      🖱️ Test de clic sur: '{first_text}'")
                    
                    try:
                        url_before = driver.current_url
                        
                        # Essayer clic normal d'abord
                        first_vote_btn.click()
                        time.sleep(2)
                        
                        url_after = driver.current_url
                        logger.info(f"      URL avant: {url_before}")
                        logger.info(f"      URL après: {url_after}")
                        
                        if url_before != url_after:
                            logger.info("      🎉 SUCCÈS! Le clic a redirigé!")
                            logger.info(f"      🎯 Nouvelle URL: {url_after}")
                            return True
                        else:
                            logger.warning("      ⚠️ Pas de redirection")
                            
                    except Exception as e:
                        logger.error(f"      ❌ Erreur clic: {e}")
                        
                        # Essayer JavaScript
                        try:
                            logger.info("      🔄 Essai avec JavaScript...")
                            driver.execute_script("arguments[0].click();", first_vote_btn)
                            time.sleep(2)
                            
                            url_js = driver.current_url
                            if url_js != url_before:
                                logger.info("      🎉 SUCCÈS avec JavaScript!")
                                logger.info(f"      🎯 Nouvelle URL: {url_js}")
                                return True
                            else:
                                logger.warning("      ⚠️ Pas de redirection avec JavaScript non plus")
                                
                        except Exception as e2:
                            logger.error(f"      ❌ Erreur JavaScript: {e2}")
        
        logger.info("\n4️⃣ INSPECTION FINALE:")
        
        # Dump du HTML final
        try:
            page_source_length = len(driver.page_source)
            logger.info(f"   Taille du HTML: {page_source_length} caractères")
            
            # Chercher "Votez maintenant" dans le source
            if "Votez maintenant" in driver.page_source:
                logger.info("   ✅ 'Votez maintenant' trouvé dans le source HTML")
            else:
                logger.warning("   ⚠️ 'Votez maintenant' NON trouvé dans le source HTML")
                
            if "SITE N°1" in driver.page_source:
                logger.info("   ✅ 'SITE N°1' trouvé dans le source HTML")
            else:
                logger.warning("   ⚠️ 'SITE N°1' NON trouvé dans le source HTML")
                
        except Exception as e:
            logger.error(f"Erreur inspection HTML: {e}")
        
        input("\n🔍 Appuyez sur Entrée pour terminer...")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_dynamic_content()