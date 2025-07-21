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

def debug_vote_links():
    """Debug pour analyser en détail les liens de vote sur oneblock.fr"""
    
    # Configuration Chrome
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("=== DEBUT DU DEBUG VOTE LINKS ===")
        
        # Étape 1: Aller sur oneblock.fr/vote
        logger.info("🌐 Accès à https://oneblock.fr/vote")
        driver.get("https://oneblock.fr/vote")
        time.sleep(3)
        
        # Étape 2: Saisir le pseudonyme
        logger.info("📝 Saisie du pseudonyme...")
        try:
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
            )
            username_input.clear()
            username_input.send_keys("zCapsLock")
            logger.info("✅ Pseudonyme saisi")
        except Exception as e:
            logger.error(f"❌ Erreur saisie pseudonyme: {e}")
            return
            
        # Étape 3: Analyser TOUS les boutons disponibles
        logger.info("\n🔍 ANALYSE DE TOUS LES BOUTONS DISPONIBLES:")
        all_buttons = driver.find_elements(By.XPATH, "//button | //input[@type='submit'] | //input[@type='button'] | //*[@onclick]")
        
        for i, btn in enumerate(all_buttons):
            try:
                text = btn.text.strip()
                value = btn.get_attribute('value')
                onclick = btn.get_attribute('onclick')
                btn_type = btn.get_attribute('type')
                tag = btn.tag_name
                is_displayed = btn.is_displayed()
                
                logger.info(f"   Bouton {i+1}: [{tag}] text='{text}' value='{value}' type='{btn_type}' onclick='{onclick}' visible={is_displayed}")
            except Exception as e:
                logger.debug(f"Erreur bouton {i+1}: {e}")
        
        # Étape 4: Cliquer sur ENVOYER directement (on sait qu'il existe)
        logger.info("\n🔘 Clic sur bouton ENVOYER...")
        try:
            # Trouver le bouton parmi ceux analysés
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            envoyer_button = None
            
            for btn in all_buttons:
                if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                    envoyer_button = btn
                    break
            
            if envoyer_button:
                # Scroller vers le bouton et cliquer avec JavaScript
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", envoyer_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", envoyer_button)
                logger.info("✅ Clic sur ENVOYER réussi (JavaScript)")
                time.sleep(3)  # Attendre l'activation des boutons
            else:
                logger.error("❌ Bouton ENVOYER non trouvé")
                return
        except Exception as e:
            logger.error(f"❌ Erreur clic ENVOYER: {e}")
            return
        
        # Attendre que les sites de vote apparaissent
        logger.info("\n⏳ Attente de l'activation des boutons de vote...")
        time.sleep(5)
        
        # NOUVEAU: Analyser les boutons APRÈS clic sur ENVOYER
        logger.info("\n🔍 ÉTAT DES BOUTONS APRÈS CLIC SUR ENVOYER:")
        
        vote_buttons_after = driver.find_elements(By.XPATH, "//button[contains(text(), 'SITE N°')]")
        for i, btn in enumerate(vote_buttons_after):
            try:
                text = btn.text.strip()
                classes = btn.get_attribute('class')
                is_enabled = 'cursor-not-allowed' not in classes
                is_grayscale = 'grayscale' in classes
                
                logger.info(f"   Bouton {i+1}: '{text}' - Activé: {is_enabled}, Grisé: {is_grayscale}")
                logger.info(f"      Classes: {classes}")
                
                if is_enabled and not is_grayscale:
                    logger.info(f"      ⭐ BOUTON ACTIVÉ TROUVÉ!")
                    
            except Exception as e:
                logger.debug(f"Erreur bouton vote {i+1}: {e}")
        
        # Étape 4: ANALYSE DÉTAILLÉE DES SITES DE VOTE
        logger.info("\n" + "="*50)
        logger.info("🔍 ANALYSE DÉTAILLÉE DES SITES DE VOTE")
        logger.info("="*50)
        
        # Analyser tous les éléments potentiels
        vote_containers = [
            "div[class*='vote']",
            "div[class*='site']", 
            "div[class*='server']",
            ".vote-site",
            ".site-vote",
            "[data-site]",
            "div:has(a[href*='serveur-prive'])",
            "div:has(button:contains('Votez'))",
            "div:has(*:contains('SITE N°1'))"
        ]
        
        all_vote_elements = []
        
        for container_selector in vote_containers:
            try:
                if ':has' in container_selector or 'contains' in container_selector:
                    # Utiliser XPath pour des sélecteurs complexes
                    if 'SITE N°1' in container_selector:
                        xpath = "//div[contains(., 'SITE N°1') or contains(., 'Site n°1') or contains(., 'site 1')]"
                    elif 'Votez' in container_selector:
                        xpath = "//div[.//button[contains(text(), 'Votez')] or .//a[contains(text(), 'Votez')]]"
                    elif 'serveur-prive' in container_selector:
                        xpath = "//div[.//a[contains(@href, 'serveur-prive')]]"
                    else:
                        continue
                    
                    containers = driver.find_elements(By.XPATH, xpath)
                else:
                    containers = driver.find_elements(By.CSS_SELECTOR, container_selector)
                
                logger.info(f"\n📦 Conteneurs trouvés avec '{container_selector}': {len(containers)}")
                
                for i, container in enumerate(containers):
                    try:
                        text_content = container.text.strip()[:200] + "..." if len(container.text.strip()) > 200 else container.text.strip()
                        logger.info(f"   Conteneur {i+1}: '{text_content}'")
                        
                        # Analyser tous les liens et boutons dans ce conteneur
                        clickables = container.find_elements(By.XPATH, ".//a | .//button | .//*[@onclick]")
                        
                        for j, clickable in enumerate(clickables):
                            href = clickable.get_attribute('href')
                            onclick = clickable.get_attribute('onclick')
                            text = clickable.text.strip()
                            tag = clickable.tag_name
                            class_attr = clickable.get_attribute('class')
                            
                            if text or href or onclick:
                                logger.info(f"      🔗 [{tag}] '{text}' -> href: {href}, onclick: {onclick}, class: {class_attr}")
                                
                                # Identifier le site n°1 spécifiquement
                                if any(keyword in text.lower() for keyword in ['votez maintenant', 'voter', 'vote']) or \
                                   (href and 'serveur-prive.net' in href):
                                    all_vote_elements.append({
                                        'element': clickable,
                                        'text': text,
                                        'href': href,
                                        'onclick': onclick,
                                        'tag': tag,
                                        'class': class_attr,
                                        'container_text': text_content
                                    })
                                    logger.info(f"         ⭐ CANDIDAT VOTE DÉTECTÉ!")
                    
                    except Exception as e:
                        logger.debug(f"Erreur analyse conteneur {i+1}: {e}")
                        
            except Exception as e:
                logger.debug(f"Erreur sélecteur '{container_selector}': {e}")
        
        # Résumé des candidats
        logger.info(f"\n🎯 RÉSUMÉ: {len(all_vote_elements)} candidats de vote trouvés")
        for i, vote_elem in enumerate(all_vote_elements):
            logger.info(f"   Candidat {i+1}: [{vote_elem['tag']}] '{vote_elem['text']}' -> {vote_elem['href']}")
        
        # Test de clic sur le premier candidat valide
        if all_vote_elements:
            logger.info(f"\n🖱️ TEST DE CLIC sur le premier candidat...")
            try:
                first_candidate = all_vote_elements[0]['element']
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", first_candidate)
                time.sleep(2)
                
                # Capturer l'URL avant le clic
                url_before = driver.current_url
                logger.info(f"URL avant clic: {url_before}")
                
                first_candidate.click()
                time.sleep(3)
                
                url_after = driver.current_url
                logger.info(f"URL après clic: {url_after}")
                
                if url_before != url_after:
                    logger.info("✅ SUCCÈS: Le clic a changé l'URL!")
                else:
                    logger.warning("⚠️ Le clic n'a pas changé l'URL")
                    
            except Exception as e:
                logger.error(f"❌ Erreur test clic: {e}")
        
        # Garde la fenêtre ouverte pour inspection manuelle
        input("\n🔍 Appuyez sur Entrée après inspection manuelle de la page...")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    
    finally:
        driver.quit()
        logger.info("🏁 Debug terminé")

if __name__ == "__main__":
    debug_vote_links()