#!/usr/bin/env python3
"""
Test du workflow inversé : 
1. Résoudre le captcha sur le site de vote direct
2. Aller sur oneblock.fr pour voir si ça détecte qu'on a voté
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_reverse_workflow(vote_url: str):
    """
    Test du workflow inversé
    """
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("🧪 === TEST DU WORKFLOW INVERSÉ ===")
        logger.info(f"URL de vote: {vote_url}")
        
        # ÉTAPE 1: Aller directement sur le site de vote
        logger.info("🌐 Étape 1: Accès direct au site de vote")
        driver.get(vote_url)
        time.sleep(5)
        
        current_url = driver.current_url
        title = driver.title
        logger.info(f"URL atteinte: {current_url}")
        logger.info(f"Titre: {title}")
        
        # Vérifier si on a bien une page de vote
        page_source = driver.page_source
        
        # Chercher MTCaptcha
        if 'MTPublic-' in page_source:
            import re
            sitekey_match = re.search(r'MTPublic-[a-zA-Z0-9]+', page_source)
            if sitekey_match:
                sitekey = sitekey_match.group(0)
                logger.info(f"✅ MTCaptcha sitekey trouvée: {sitekey}")
                
                # Chercher champs username
                username_fields = driver.find_elements(By.CSS_SELECTOR, "input[name='username'], input[name='pseudo'], input[placeholder*='pseudo' i]")
                if username_fields:
                    logger.info(f"✅ {len(username_fields)} champ(s) username trouvé(s)")
                    
                    # Remplir le champ avec zCapsLock
                    for field in username_fields:
                        if field.is_displayed() and field.is_enabled():
                            field.clear()
                            field.send_keys("zCapsLock")
                            logger.info("✅ Pseudonyme 'zCapsLock' saisi")
                            break
                    
                    # ICI ON DEVRAIT RÉSOUDRE LE CAPTCHA ET VOTER
                    logger.info("📋 À ce stade, on résoudrait normalement le MTCaptcha...")
                    logger.info("📋 Puis on soumettrait le vote...")
                    
                    # Simuler un délai de vote (pour le test)
                    time.sleep(3)
                    
                else:
                    logger.warning("⚠️ Aucun champ username trouvé")
            else:
                logger.warning("⚠️ Sitekey MTCaptcha non trouvée")
        else:
            logger.warning("⚠️ Pas de MTCaptcha détecté sur cette page")
        
        # ÉTAPE 2: Aller sur oneblock.fr pour tester la détection
        logger.info("\n🌐 Étape 2: Test détection sur oneblock.fr")
        driver.get("https://oneblock.fr/vote")
        time.sleep(5)
        
        # Remplir le pseudo sur oneblock.fr
        try:
            pseudo_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
            pseudo_field.clear()
            pseudo_field.send_keys("zCapsLock")
            logger.info("✅ Pseudo saisi sur oneblock.fr")
            time.sleep(2)
        except:
            logger.warning("⚠️ Erreur saisie pseudo oneblock.fr")
        
        # Cliquer sur ENVOYER
        try:
            # Chercher le bouton ENVOYER
            envoyer_btn = None
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                if 'envoyer' in btn.text.strip().lower() and btn.is_displayed() and btn.is_enabled():
                    envoyer_btn = btn
                    break
            
            if envoyer_btn:
                try:
                    envoyer_btn.click()
                    logger.info("✅ Clic ENVOYER réussi")
                except:
                    # Si intercepté
                    driver.execute_script("arguments[0].click();", envoyer_btn)
                    logger.info("✅ Clic ENVOYER via JavaScript réussi")
                
                time.sleep(5)
                
                # ÉTAPE 3: Analyser les sites de vote après ENVOYER
                logger.info("\n🔍 Étape 3: Analyse des sites après ENVOYER")
                
                # Chercher les boutons SITE N°1 et N°2
                site_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'SITE N°')]")
                
                for i, site_btn in enumerate(site_buttons):
                    text = site_btn.text.strip()
                    classes = site_btn.get_attribute('class') or ''
                    is_disabled = 'grayscale' in classes or 'cursor-not-allowed' in classes
                    
                    logger.info(f"   Site #{i+1}: '{text[:30]}...'")
                    logger.info(f"      Classes: {classes}")
                    logger.info(f"      Désactivé: {is_disabled}")
                    
                    # Vérifier s'il y a un message de cooldown/déjà voté
                    if 'connectez-vous' not in text.lower():
                        if any(keyword in text.lower() for keyword in ['voté', 'voted', 'cooldown', 'attendre', 'wait']):
                            logger.info(f"   🎉 DÉTECTION POSSIBLE DE VOTE PRÉCÉDENT!")
                        elif not is_disabled:
                            logger.info(f"   ✅ Site disponible pour vote")
                        else:
                            logger.info(f"   ⚠️ Site désactivé")
                    else:
                        logger.info(f"   🔐 Connexion requise")
                
                # Chercher des messages d'alerte ou de statut
                alert_selectors = [".alert", ".message", ".notification", "[class*='alert']", "[class*='message']"]
                for selector in alert_selectors:
                    try:
                        alerts = driver.find_elements(By.CSS_SELECTOR, selector)
                        for alert in alerts:
                            if alert.is_displayed():
                                alert_text = alert.text.strip()
                                if alert_text:
                                    logger.info(f"   📢 Message: '{alert_text}'")
                    except:
                        continue
                        
            else:
                logger.warning("⚠️ Bouton ENVOYER non trouvé")
                
        except Exception as e:
            logger.error(f"❌ Erreur processus oneblock.fr: {e}")
        
        logger.info("\n⏸️ Test terminé - page laissée ouverte pour inspection")
        input("Appuyez sur Entrée pour fermer...")
        
    finally:
        driver.quit()

def main():
    # URLs de test à essayer
    test_urls = [
        "https://serveur-prive.net/oneblockbyrivrs/vote",  # URL originale (on sait qu'elle fait 404)
        "https://serveur-prive.net/",  # Page principale
        # Ajouter d'autres URLs si l'utilisateur en fournit
    ]
    
    logger.info("📋 URLs de test disponibles:")
    for i, url in enumerate(test_urls):
        logger.info(f"   {i+1}. {url}")
    
    logger.info("\n⚠️ IMPORTANT: Il faut une URL de vote qui fonctionne vraiment!")
    logger.info("⚠️ L'URL actuelle retourne 404 - besoin de la vraie URL")
    
    # Pour le moment, on va juste tester avec la première URL
    # même si on sait qu'elle ne fonctionne pas
    test_reverse_workflow(test_urls[0])

if __name__ == "__main__":
    main()