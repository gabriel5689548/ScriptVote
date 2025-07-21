#!/usr/bin/env python3

import time
import logging
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MTCaptchaVoter:
    def __init__(self, headless=False, timeout=120):
        self.timeout = timeout
        self.api_key = "94f39af4acdb68c2215fc8558e3ba1ab"  # 2Captcha API key
        self.username = "zCapsLock"
        
        # Configuration Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        logger.info("Configuration du driver Selenium...")
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Driver Selenium configuré avec succès")
    
    def vote_oneblock_site1(self, base_url):
        """Vote pour le SITE N°1 sur oneblock.fr avec la logique corrigée"""
        
        try:
            logger.info("🎯 Démarrage du processus de vote pour: " + base_url)
            logger.info("🌐 Étape 1: Accès à https://oneblock.fr/vote")
            
            # Étape 1: Aller sur oneblock.fr/vote
            self.driver.get("https://oneblock.fr/vote")
            time.sleep(3)
            
            # Étape 2: Remplir le pseudonyme
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
                )
                username_input.clear()
                username_input.send_keys(self.username)
                logger.info(f"✅ Pseudonyme '{self.username}' saisi dans oneblock.fr (placeholder: '{username_input.get_attribute('placeholder')}')")
            except Exception as e:
                logger.warning(f"⚠️ Erreur remplissage pseudo oneblock.fr: {str(e)}")
            
            # Étape 3: Cliquer sur ENVOYER
            envoyer_button = None
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                    envoyer_button = btn
                    logger.info(f"✅ Bouton 'Envoyer' identifié: '{btn.text.strip()}'")
                    break
            
            if envoyer_button:
                logger.info("🔘 Clic sur bouton: 'ENVOYER'")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", envoyer_button)
                time.sleep(1)
                envoyer_button.click()
                logger.info("✅ Clic normal sur 'ENVOYER' réussi")
                time.sleep(5)
            
            # Étape 4: Chercher et cliquer sur le bouton SITE N°1
            logger.info("🔍 Recherche et clic direct sur bouton SITE N°1...")
            
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            site1_button = None
            
            for btn in all_buttons:
                text = btn.text.strip()
                if "SITE N°1" in text and "Votez maintenant" in text and btn.is_displayed():
                    site1_button = btn
                    logger.info(f"🎯 Bouton SITE N°1 trouvé: '{text}'")
                    break
            
            if site1_button:
                # Cliquer sur le bouton
                logger.info("🖱️ Clic sur bouton SITE N°1...")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", site1_button)
                time.sleep(2)
                site1_button.click()
                logger.info("✅ Clic sur SITE N°1 effectué")
                
                # Attendre et vérifier si le vote est enregistré
                logger.info("⏳ Vérification du résultat du vote...")
                for wait_time in range(1, 11):
                    time.sleep(1)
                    try:
                        button_text = site1_button.text.strip()
                        if "min" in button_text and "s" in button_text:
                            logger.info(f"🎉 VOTE RÉUSSI! Cooldown détecté: '{button_text}'")
                            return True
                        elif "Veuillez patienter" in button_text:
                            logger.info(f"⏳ Vote en cours... '{button_text}'")
                        else:
                            logger.info(f"📊 État bouton: '{button_text}'")
                    except Exception:
                        pass
                    
                    # Vérifier l'URL au cas où il y aurait une redirection
                    current_url = self.driver.current_url
                    if 'oneblock.fr' not in current_url:
                        logger.info(f"🎯 Redirection détectée vers: {current_url}")
                        # Continuer le processus de vote sur serveur-prive.net
                        return self.continue_vote_on_serveur_prive()
                
                logger.warning("⚠️ Pas de cooldown visible après 10s, continuons vers serveur-prive.net")
            else:
                logger.warning("⚠️ Bouton SITE N°1 'Votez maintenant' non trouvé")
            
            # Fallback: Navigation directe
            logger.warning("⚠️ Fallback: navigation directe vers serveur-prive.net")
            self.driver.get(base_url)
            time.sleep(3)
            return self.continue_vote_on_serveur_prive()
            
        except Exception as e:
            logger.error(f"❌ Erreur dans vote_oneblock_site1: {str(e)}")
            return False
    
    def continue_vote_on_serveur_prive(self):
        """Continue le processus de vote sur serveur-prive.net"""
        
        try:
            # Vérifier si on est sur serveur-prive.net
            current_url = self.driver.current_url
            if 'serveur-prive.net' not in current_url:
                logger.error("❌ Pas sur serveur-prive.net")
                return False
            
            logger.info("🌐 Sur serveur-prive.net, recherche du MTCaptcha...")
            
            # Chercher la sitekey MTCaptcha
            sitekey = None
            try:
                # Chercher dans les scripts
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                for script in scripts:
                    script_text = script.get_attribute('innerHTML') or ''
                    if 'MTPublic-' in script_text:
                        import re
                        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', script_text)
                        if matches:
                            sitekey = matches[0]
                            logger.info(f"Sitekey MTCaptcha trouvée dans JS config: {sitekey}")
                            break
                
                if not sitekey:
                    # Chercher dans les attributs data
                    captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey], [data-site-key]")
                    for elem in captcha_elements:
                        potential_key = elem.get_attribute('data-sitekey') or elem.get_attribute('data-site-key')
                        if potential_key and 'MTPublic-' in potential_key:
                            sitekey = potential_key
                            logger.info(f"Sitekey MTCaptcha trouvée dans attribut: {sitekey}")
                            break
                
                if not sitekey:
                    logger.error("❌ Sitekey MTCaptcha non trouvée")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erreur recherche sitekey: {str(e)}")
                return False
            
            # Remplir le pseudonyme si nécessaire
            logger.info("Vérification si pseudonyme doit être rempli...")
            try:
                username_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[id*='username'], input[placeholder*='pseudo']")
                for field in username_fields:
                    if field.is_displayed():
                        current_value = field.get_attribute('value')
                        if not current_value or current_value.strip() == '':
                            field.clear()
                            field.send_keys(self.username)
                            logger.info(f"Pseudonyme '{self.username}' saisi dans: {field.get_attribute('name') or field.get_attribute('id')}")
                        break
                else:
                    logger.info("Aucun champ pseudonyme trouvé ou accessible")
            except Exception as e:
                logger.warning(f"⚠️ Erreur avec champ username: {e}")
                try:
                    # Essayer avec JavaScript
                    self.driver.execute_script(f"document.querySelector('input[name*=\"username\"], input[id*=\"username\"]').value = '{self.username}';")
                    logger.info(f"✅ Pseudonyme '{self.username}' saisi via JavaScript")
                except Exception as e2:
                    logger.warning(f"⚠️ Erreur JavaScript username: {e2}")
            
            # Résoudre le MTCaptcha avec 2Captcha
            logger.info("Envoi de la demande de résolution à 2Captcha...")
            try:
                page_url = self.driver.current_url
                submit_data = {
                    'key': self.api_key,
                    'method': 'mtcaptcha',
                    'sitekey': sitekey,
                    'pageurl': page_url,
                    'json': 1
                }
                
                response = requests.post('http://2captcha.com/in.php', data=submit_data, timeout=30)
                result = response.json()
                
                if result['status'] != 1:
                    logger.error(f"❌ Erreur soumission 2Captcha: {result}")
                    return False
                
                captcha_id = result['request']
                logger.info(f"Captcha soumis avec l'ID: {captcha_id}")
                
                # Attendre la résolution
                for attempt in range(30):
                    time.sleep(10)
                    
                    check_response = requests.get(f'http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}&json=1', timeout=30)
                    check_result = check_response.json()
                    
                    if check_result['status'] == 1:
                        solution = check_result['request']
                        logger.info("MTCaptcha résolu avec succès!")
                        break
                    elif check_result['error'] == 'CAPCHA_NOT_READY':
                        logger.info("Captcha en cours de résolution...")
                        continue
                    else:
                        logger.error(f"❌ Erreur résolution captcha: {check_result}")
                        return False
                else:
                    logger.error("❌ Timeout résolution captcha")
                    return False
                
                # Injecter la solution
                logger.info("Injection de la solution dans la page...")
                
                # Injecter dans le champ MTCaptcha
                try:
                    self.driver.execute_script(f"document.querySelector('input[name=\"mtcaptcha-verifiedtoken\"]').value = '{solution}';")
                    logger.info("Solution injectée dans: input[name='mtcaptcha-verifiedtoken']")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur injection solution: {e}")
                
                # Soumettre le formulaire
                logger.info("Soumission du formulaire...")
                
                # Chercher et cliquer sur le bouton de vote
                vote_selectors = [
                    "#voteBtn",
                    "input[type='submit']",
                    "button[type='submit']",
                    "button:contains('Vote')",
                    "*[onclick*='vote']"
                ]
                
                form_submitted = False
                for selector in vote_selectors:
                    try:
                        if 'contains' in selector:
                            elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), 'Vote')] | //button[contains(text(), 'vote')]")
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for element in elements:
                            if element.is_displayed():
                                try:
                                    element.click()
                                    logger.info(f"Formulaire soumis via clic: {selector}")
                                    form_submitted = True
                                    break
                                except:
                                    try:
                                        self.driver.execute_script("arguments[0].click();", element)
                                        logger.info(f"Formulaire soumis via JavaScript: {selector}")
                                        form_submitted = True
                                        break
                                    except:
                                        continue
                        if form_submitted:
                            break
                    except:
                        continue
                
                if not form_submitted:
                    logger.warning("⚠️ Aucun bouton de soumission trouvé, tentative JavaScript")
                    try:
                        self.driver.execute_script("document.forms[0].submit();")
                        logger.info("Formulaire soumis via JavaScript générique")
                        form_submitted = True
                    except Exception as e:
                        logger.error(f"❌ Erreur soumission formulaire: {e}")
                        return False
                
                # Vérifier le résultat
                logger.info("Vérification du résultat...")
                time.sleep(5)
                
                page_source = self.driver.page_source.lower()
                current_url = self.driver.current_url
                
                # Messages de succès
                success_patterns = [
                    "succès", "success", "vote validé", "merci", "thank you",
                    "votre vote a été", "vote enregistré", "classement"
                ]
                
                # Messages d'erreur  
                error_patterns = [
                    "erreur", "error", "déjà voté", "already voted", "cooldown",
                    "prochain vote", "next vote", "minutes", "heures"
                ]
                
                # Chercher les messages dans le HTML visible
                visible_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                
                for pattern in success_patterns:
                    if pattern in visible_text:
                        success_msg = [line.strip() for line in visible_text.split('\n') if pattern in line][0]
                        logger.info(f"✅ Message de succès trouvé: '{success_msg}'")
                        return True
                
                for pattern in error_patterns:
                    if pattern in visible_text:
                        error_msg = [line.strip() for line in visible_text.split('\n') if pattern in line][0]
                        logger.info(f"❌ Message d'erreur trouvé: '{error_msg}'")
                        return False
                
                # Si pas de message clair, considérer comme succès si on est toujours sur la bonne page
                if 'serveur-prive.net' in current_url:
                    logger.info("✅ Probablement réussi (pas de message d'erreur)")
                    return True
                else:
                    logger.warning(f"⚠️ Résultat incertain, URL: {current_url}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erreur traitement MTCaptcha: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur générale: {str(e)}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("Driver fermé")

def main():
    parser = argparse.ArgumentParser(description='Script de vote automatique MTCaptcha corrigé')
    parser.add_argument('--url', required=True, help='URL de vote sur serveur-prive.net')
    parser.add_argument('--headless', action='store_true', help='Mode headless')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout en secondes')
    
    args = parser.parse_args()
    
    logger.info("=== DÉMARRAGE DU TEST MTCAPTCHA CORRIGÉ ===")
    logger.info(f"URL cible: {args.url}")
    logger.info(f"Mode headless: {args.headless}")
    
    voter = None
    try:
        voter = MTCaptchaVoter(headless=args.headless, timeout=args.timeout)
        
        success = voter.vote_oneblock_site1(args.url)
        
        if success:
            logger.info("Résultat final: ✅ SUCCÈS")
            logger.info("=== TEST TERMINÉ AVEC SUCCÈS ===")
        else:
            logger.info("Résultat final: ❌ ÉCHEC")
            logger.info("=== TEST ÉCHOUÉ ===")
            
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {str(e)}")
        logger.info("=== TEST ÉCHOUÉ ===")
    finally:
        if voter:
            voter.close()

if __name__ == "__main__":
    main()