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

def debug_oneblock_detailed():
    """Debug détaillé de oneblock.fr pour identifier EXACTEMENT où est le lien de vote"""
    
    # Configuration Chrome
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("=== DEBUG DÉTAILLÉ ONEBLOCK.FR ===")
        
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
            username_input.send_keys("TestUser123")
            logger.info("✅ Pseudonyme saisi")
        except Exception as e:
            logger.error(f"❌ Erreur saisie pseudonyme: {e}")
            return
            
        # Étape 3: Cliquer sur ENVOYER
        logger.info("🔘 Recherche et clic sur ENVOYER...")
        try:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            envoyer_button = None
            
            for btn in all_buttons:
                if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                    envoyer_button = btn
                    break
            
            if envoyer_button:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", envoyer_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", envoyer_button)
                logger.info("✅ Clic sur ENVOYER réussi")
                time.sleep(5)  # Attendre l'activation
            else:
                logger.error("❌ Bouton ENVOYER non trouvé")
                return
        except Exception as e:
            logger.error(f"❌ Erreur clic ENVOYER: {e}")
            return
        
        # Étape 4: ANALYSE COMPLÈTE DE LA PAGE APRÈS ENVOYER
        logger.info("\n" + "="*60)
        logger.info("🔍 ANALYSE COMPLÈTE APRÈS CLIC SUR ENVOYER")
        logger.info("="*60)
        
        # 1. Analyser TOUS les boutons présents
        logger.info("\n1️⃣ ANALYSE DE TOUS LES BOUTONS:")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        vote_buttons = []
        
        for i, btn in enumerate(all_buttons):
            try:
                text = btn.text.strip()
                classes = btn.get_attribute('class')
                is_displayed = btn.is_displayed()
                
                if 'SITE N°' in text or 'Votez' in text:
                    logger.info(f"   🎯 Bouton {i+1} [CANDIDAT]: '{text}' - Visible: {is_displayed}")
                    logger.info(f"      Classes: {classes}")
                    
                    if is_displayed and 'Votez maintenant' in text:
                        vote_buttons.append(btn)
                        logger.info(f"      ⭐ BOUTON DE VOTE ACTIF!")
                else:
                    logger.info(f"   Bouton {i+1}: '{text[:30]}...' - Visible: {is_displayed}")
            except Exception as e:
                logger.debug(f"Erreur bouton {i+1}: {e}")
        
        # 2. Analyser TOUS les liens présents
        logger.info(f"\n2️⃣ ANALYSE DE TOUS LES LIENS:")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        vote_links = []
        
        for i, link in enumerate(all_links):
            try:
                text = link.text.strip()
                href = link.get_attribute('href')
                is_displayed = link.is_displayed()
                
                if href and ('serveur-prive' in href or 'vote' in href.lower()):
                    logger.info(f"   🎯 Lien {i+1} [CANDIDAT]: '{text}' -> {href}")
                    logger.info(f"      Visible: {is_displayed}")
                    
                    if is_displayed:
                        vote_links.append(link)
                        logger.info(f"      ⭐ LIEN DE VOTE ACTIF!")
                elif text and ('vote' in text.lower() or 'maintenant' in text.lower()):
                    logger.info(f"   Lien {i+1}: '{text}' -> {href} - Visible: {is_displayed}")
                else:
                    logger.info(f"   Lien {i+1}: '{text[:20]}...' -> {href[:30] if href else 'None'}...")
            except Exception as e:
                logger.debug(f"Erreur lien {i+1}: {e}")
        
        # 3. Test des sélecteurs utilisés par mtcaptcha_tester.py
        logger.info(f"\n3️⃣ TEST DES SÉLECTEURS DU SCRIPT PRINCIPAL:")
        
        test_selectors = [
            ("SITE N°1 XPath", "//*[contains(text(), 'SITE N°1')]"),
            ("Votez maintenant XPath", "//*[contains(text(), 'Votez maintenant')]"),
            ("Liens avec href", "//a[@href]"),
            ("Boutons vote CSS", "button:contains('Votez')"),
            ("Divs avec vote", "//div[contains(text(), 'vote')]")
        ]
        
        for name, selector in test_selectors:
            try:
                if selector.startswith("//") or selector.startswith("//*"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    # CSS selector
                    continue  # Skip CSS contains pour l'instant
                
                logger.info(f"   {name}: {len(elements)} éléments trouvés")
                
                for j, elem in enumerate(elements[:3]):  # Limiter à 3 premiers
                    text = elem.text.strip()[:50]
                    tag = elem.tag_name
                    is_displayed = elem.is_displayed()
                    logger.info(f"      {j+1}. [{tag}] '{text}' - Visible: {is_displayed}")
                    
            except Exception as e:
                logger.debug(f"Erreur sélecteur {name}: {e}")
        
        # 4. Test de clic sur le premier bouton de vote trouvé
        if vote_buttons:
            logger.info(f"\n4️⃣ TEST DE CLIC SUR LE PREMIER BOUTON DE VOTE:")
            try:
                first_vote_btn = vote_buttons[0]
                text = first_vote_btn.text.strip()
                logger.info(f"   Bouton sélectionné: '{text}'")
                
                # Capturer URL avant
                url_before = driver.current_url
                logger.info(f"   URL avant clic: {url_before}")
                
                # Cliquer
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", first_vote_btn)
                time.sleep(2)
                driver.execute_script("arguments[0].click();", first_vote_btn)
                logger.info("   ✅ Clic effectué")
                
                time.sleep(5)
                
                # Capturer URL après
                url_after = driver.current_url
                logger.info(f"   URL après clic: {url_after}")
                
                if url_before != url_after:
                    logger.info("   🎉 SUCCÈS: Le clic a changé l'URL!")
                    if 'serveur-prive.net' in url_after:
                        logger.info("   🎯 Redirection vers serveur-prive.net détectée!")
                else:
                    logger.warning("   ⚠️ Pas de changement d'URL")
                    
            except Exception as e:
                logger.error(f"   ❌ Erreur test clic: {e}")
        
        elif vote_links:
            logger.info(f"\n4️⃣ TEST DE CLIC SUR LE PREMIER LIEN DE VOTE:")
            try:
                first_vote_link = vote_links[0]
                href = first_vote_link.get_attribute('href')
                text = first_vote_link.text.strip()
                logger.info(f"   Lien sélectionné: '{text}' -> {href}")
                
                first_vote_link.click()
                logger.info("   ✅ Clic effectué")
                time.sleep(3)
                
                logger.info(f"   URL finale: {driver.current_url}")
                
            except Exception as e:
                logger.error(f"   ❌ Erreur test clic lien: {e}")
        
        else:
            logger.warning("❌ Aucun bouton ou lien de vote trouvé!")
        
        # Garder ouvert pour inspection
        logger.info(f"\n🔍 RÉSUMÉ:")
        logger.info(f"   - Boutons de vote trouvés: {len(vote_buttons)}")
        logger.info(f"   - Liens de vote trouvés: {len(vote_links)}")
        
        input("\n🔍 Appuyez sur Entrée après inspection manuelle...")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    
    finally:
        driver.quit()
        logger.info("🏁 Debug terminé")

if __name__ == "__main__":
    debug_oneblock_detailed()