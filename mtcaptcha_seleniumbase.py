#!/usr/bin/env python3

import time
import logging
import argparse
import os
from dotenv import load_dotenv
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import cloudscraper

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MTCaptchaVoterSeleniumBase:
    def __init__(self, headless=True, timeout=120):
        self.timeout = timeout
        self.screenshot_count = 0
        self.api_key = os.getenv('api_key') or os.getenv('TWOCAPTCHA_API_KEY')
        self.username = os.getenv('username', 'zCapsLock')
        
        if not self.api_key:
            raise ValueError("❌ API key non trouvée dans .env !")
        
        logger.info("🔧 Configuration de SeleniumBase UC Mode...")
        
        try:
            # Configuration SeleniumBase avec UC Mode pour contourner Cloudflare
            self.driver = Driver(
                browser="chrome",
                uc=True,  # Active UndetectedChromeDriver mode
                headless=headless,
                undetectable=True,
                chromium_arg="--disable-blink-features=AutomationControlled",
                agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                page_load_strategy="normal",
                uc_cdp=True,  # Utilise Chrome DevTools Protocol pour contourner les détections
                no_sandbox=True
            )
            
            # Attendre un peu pour que le driver se stabilise
            time.sleep(2)
            
            logger.info("✅ SeleniumBase UC Mode configuré avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration SeleniumBase: {e}")
            raise
    
    def save_screenshot(self, name):
        """Sauvegarde un screenshot avec un nom unique"""
        try:
            self.screenshot_count += 1
            filename = f"{name}_{self.screenshot_count}_{int(time.time())}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"📸 Screenshot sauvegardé: {filename}")
            return filename
        except Exception as e:
            logger.warning(f"⚠️ Impossible de sauvegarder le screenshot: {e}")
            return None
    
    def handle_cloudflare_turnstile(self):
        """Gère spécifiquement Cloudflare Turnstile"""
        logger.info("🛡️ Vérification de Cloudflare Turnstile...")
        
        try:
            # Attendre que la page se charge complètement
            time.sleep(5)
            
            # Chercher l'iframe Turnstile
            turnstile_selectors = [
                "iframe[src*='challenges.cloudflare.com']",
                "iframe[title*='Cloudflare']",
                "#turnstile-wrapper iframe",
                ".cf-turnstile iframe"
            ]
            
            for selector in turnstile_selectors:
                try:
                    iframe = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if iframe.is_displayed():
                        logger.info("🎯 Iframe Turnstile détecté")
                        
                        # Basculer vers l'iframe
                        self.driver.switch_to.frame(iframe)
                        
                        # Chercher et cliquer sur la checkbox
                        checkbox_selectors = [
                            "input[type='checkbox']",
                            "#challenge-stage input",
                            ".cb-i"
                        ]
                        
                        for cb_selector in checkbox_selectors:
                            try:
                                checkbox = self.driver.find_element(By.CSS_SELECTOR, cb_selector)
                                if checkbox.is_displayed() and not checkbox.is_selected():
                                    checkbox.click()
                                    logger.info("✅ Checkbox Turnstile cliquée")
                                    time.sleep(3)
                                    break
                            except:
                                continue
                        
                        # Revenir au contexte principal
                        self.driver.switch_to.default_content()
                        
                        # Attendre que le challenge se résolve
                        time.sleep(5)
                        break
                        
                except Exception as e:
                    logger.debug(f"Pas de Turnstile avec {selector}: {e}")
                    continue
            
            # Vérifier si on est toujours sur Cloudflare après l'attente
            page_source = self.driver.page_source
            if "Cloudflare" in page_source and ("Just a moment" in page_source or "Checking your browser" in page_source):
                logger.info("⏳ Cloudflare toujours actif, attente supplémentaire...")
                time.sleep(10)
            else:
                logger.info("✅ Cloudflare passé ou non détecté")
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur gestion Turnstile: {e}")
    
    def wait_for_cloudflare(self, max_wait=60):
        """Attend que Cloudflare se résolve avec UC Mode"""
        logger.info("⏳ Attente de résolution Cloudflare avec UC Mode...")
        
        start_time = time.time()
        cloudflare_detected = False
        
        while time.time() - start_time < max_wait:
            try:
                page_source = self.driver.page_source
                current_url = self.driver.current_url
                
                # Indicateurs Cloudflare
                cloudflare_indicators = [
                    "Cloudflare",
                    "_cf_chl_opt", 
                    "Just a moment",
                    "Checking your browser",
                    "cf-browser-verification",
                    "challenges.cloudflare.com"
                ]
                
                if any(indicator in page_source for indicator in cloudflare_indicators):
                    if not cloudflare_detected:
                        logger.info("🛡️ Challenge Cloudflare détecté")
                        cloudflare_detected = True
                        self.save_screenshot("cloudflare_challenge")
                    
                    # Essayer de gérer Turnstile
                    self.handle_cloudflare_turnstile()
                    
                    logger.info(f"⏳ Attente Cloudflare... {int(time.time() - start_time)}s/{max_wait}s")
                    time.sleep(3)
                else:
                    if cloudflare_detected:
                        logger.info("✅ Cloudflare résolu!")
                    else:
                        logger.info("✅ Pas de Cloudflare détecté")
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur pendant l'attente: {e}")
                time.sleep(2)
        
        logger.error(f"❌ Timeout après {max_wait}s d'attente Cloudflare")
        self.save_screenshot("cloudflare_timeout")
        return False
    
    def vote_oneblock_site1(self):
        """Vote pour le SITE N°1 sur oneblock.fr avec SeleniumBase"""
        
        try:
            logger.info("🎯 Démarrage du processus de vote sur oneblock.fr")
            logger.info("🌐 Étape 1: Accès à https://oneblock.fr/vote")
            
            # Aller sur oneblock.fr/vote
            self.driver.get("https://oneblock.fr/vote")
            
            # Attendre un peu plus pour que UC Mode se stabilise
            time.sleep(5)
            
            # Remplir le pseudonyme
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
                )
                username_input.clear()
                username_input.send_keys(self.username)
                logger.info(f"✅ Pseudonyme '{self.username}' saisi dans oneblock.fr")
            except Exception as e:
                logger.warning(f"⚠️ Erreur remplissage pseudo oneblock.fr: {str(e)}")
            
            # Cliquer sur ENVOYER
            envoyer_button = None
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                    envoyer_button = btn
                    logger.info("✅ Bouton 'Envoyer' identifié")
                    break
            
            if envoyer_button:
                logger.info("🔘 Clic sur bouton: 'ENVOYER'")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", envoyer_button)
                time.sleep(1)
                envoyer_button.click()
                logger.info("✅ Clic normal sur 'ENVOYER' réussi")
                time.sleep(5)
            
            # Chercher et cliquer sur le bouton SITE N°1
            logger.info("🔍 Recherche et clic direct sur bouton SITE N°1...")
            
            # Attendre un peu plus
            time.sleep(3)
            
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            site1_button = None
            
            logger.info(f"📊 Nombre de boutons trouvés: {len(all_buttons)}")
            
            for i, btn in enumerate(all_buttons):
                try:
                    text = btn.text.strip()
                    is_displayed = btn.is_displayed()
                    logger.info(f"🔍 Bouton {i+1}: '{text}' (visible: {is_displayed})")
                    
                    if "SITE N°1" in text and btn.is_displayed():
                        site1_button = btn
                        logger.info("🎯 Bouton SITE N°1 trouvé")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Erreur lecture bouton {i+1}: {e}")
            
            if site1_button:
                # Mémoriser le nombre d'onglets avant le clic
                initial_tabs = len(self.driver.window_handles)
                original_tab = self.driver.current_window_handle
                logger.info(f"📊 Onglets avant clic: {initial_tabs}")
                
                # Cliquer sur le bouton
                logger.info("🖱️ Clic sur bouton SITE N°1...")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", site1_button)
                time.sleep(2)
                site1_button.click()
                logger.info("✅ Clic sur SITE N°1 effectué")
                
                # Attendre et détecter l'ouverture d'un nouvel onglet
                logger.info("🔍 Détection de nouveaux onglets...")
                new_tab_opened = False
                
                for wait_time in range(1, 11):
                    time.sleep(1)
                    current_tabs = len(self.driver.window_handles)
                    logger.info(f"📊 Onglets actuels: {current_tabs}")
                    
                    if current_tabs > initial_tabs:
                        logger.info("🎯 Nouvel onglet détecté!")
                        new_tab_opened = True
                        
                        # Basculer vers le nouvel onglet
                        for handle in self.driver.window_handles:
                            if handle != original_tab:
                                self.driver.switch_to.window(handle)
                                logger.info(f"🔄 Basculé vers nouvel onglet: {self.driver.current_url}")
                                
                                # Attendre que Cloudflare se résolve avec UC Mode
                                if self.wait_for_cloudflare(max_wait=60):
                                    # Continuer le vote
                                    vote_result = self.continue_vote_on_any_page()
                                    
                                    # Fermer l'onglet et revenir
                                    self.driver.close()
                                    self.driver.switch_to.window(original_tab)
                                    logger.info("🔄 Retour à l'onglet oneblock.fr")
                                    
                                    return vote_result
                                else:
                                    # Cloudflare non résolu
                                    self.driver.close()
                                    self.driver.switch_to.window(original_tab)
                                    logger.error("❌ Impossible de passer Cloudflare")
                                    return False
                        break
                
                if not new_tab_opened:
                    logger.warning("⚠️ Aucun nouvel onglet détecté après 10s")
                    # Essayer sur la page actuelle
                    current_url = self.driver.current_url
                    if "serveur-prive.net" in current_url or "vote" in current_url:
                        logger.info("🔄 Tentative de vote sur la page actuelle...")
                        if self.wait_for_cloudflare(max_wait=60):
                            return self.continue_vote_on_any_page()
            else:
                logger.warning("⚠️ Bouton SITE N°1 non trouvé")
                self.save_screenshot("bouton_site1_non_trouve")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur dans vote_oneblock_site1: {str(e)}")
            self.save_screenshot("erreur_vote_oneblock")
            return False
    
    def continue_vote_on_any_page(self):
        """Continue le processus de vote sur la page actuelle"""
        
        try:
            current_url = self.driver.current_url
            logger.info(f"📍 Page de vote: {current_url}")
            
            # Chercher la sitekey MTCaptcha
            sitekey = None
            try:
                # Chercher dans les scripts
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                logger.info(f"📊 Scripts trouvés: {len(scripts)}")
                
                for script in scripts:
                    script_text = script.get_attribute('innerHTML') or ''
                    if 'MTPublic-' in script_text:
                        import re
                        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', script_text)
                        if matches:
                            sitekey = matches[0]
                            logger.info(f"✅ Sitekey trouvée: {sitekey}")
                            break
                
                if not sitekey:
                    # Chercher dans les attributs
                    elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey], [data-site-key]")
                    for elem in elements:
                        key = elem.get_attribute('data-sitekey') or elem.get_attribute('data-site-key')
                        if key and 'MTPublic-' in key:
                            sitekey = key
                            logger.info(f"✅ Sitekey trouvée dans attribut: {sitekey}")
                            break
                
                if not sitekey:
                    # Chercher dans le HTML
                    import re
                    matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', self.driver.page_source)
                    if matches:
                        sitekey = matches[0]
                        logger.info(f"✅ Sitekey trouvée dans HTML: {sitekey}")
                
                if not sitekey:
                    logger.error("❌ Sitekey MTCaptcha non trouvée")
                    self.save_screenshot("sitekey_non_trouvee")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erreur recherche sitekey: {e}")
                return False
            
            # Remplir le pseudonyme si nécessaire
            self.fill_username_if_needed()
            
            # Résoudre le MTCaptcha
            logger.info("📤 Résolution du MTCaptcha...")
            solution = self.solve_mtcaptcha(sitekey, current_url)
            
            if not solution:
                return False
            
            # Injecter la solution
            self.inject_captcha_solution(solution)
            
            # Soumettre le formulaire
            return self.submit_vote_form()
            
        except Exception as e:
            logger.error(f"❌ Erreur continue_vote: {e}")
            self.save_screenshot("erreur_continue_vote")
            return False
    
    def fill_username_if_needed(self):
        """Remplit le champ username si nécessaire"""
        try:
            fields = self.driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[id*='username'], input[placeholder*='pseudo']")
            for field in fields:
                if field.is_displayed():
                    current_value = field.get_attribute('value')
                    if not current_value or current_value.strip() == '':
                        field.clear()
                        field.send_keys(self.username)
                        logger.info(f"✅ Pseudonyme '{self.username}' saisi")
                        break
        except Exception as e:
            logger.warning(f"⚠️ Erreur remplissage username: {e}")
    
    def solve_mtcaptcha(self, sitekey, pageurl):
        """Résout le MTCaptcha avec 2Captcha"""
        try:
            # Envoyer à 2Captcha
            response = requests.post('http://2captcha.com/in.php', data={
                'key': self.api_key,
                'method': 'mt_captcha',
                'sitekey': sitekey,
                'pageurl': pageurl,
                'json': 1
            }, timeout=30)
            
            result = response.json()
            if result.get('status') != 1:
                logger.error(f"❌ Erreur 2Captcha: {result.get('request')}")
                return None
            
            captcha_id = result['request']
            logger.info(f"🎯 Captcha ID: {captcha_id}")
            
            # Attendre la résolution
            for i in range(30):
                time.sleep(10)
                check_response = requests.get(
                    f'http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}&json=1',
                    timeout=30
                )
                check_result = check_response.json()
                
                if check_result.get('status') == 1:
                    logger.info("🎉 Captcha résolu!")
                    return check_result.get('request')
                elif check_result.get('error') != 'CAPCHA_NOT_READY':
                    logger.error(f"❌ Erreur: {check_result.get('error')}")
                    return None
                
                logger.info(f"⏳ Résolution en cours... {i+1}/30")
            
            logger.error("❌ Timeout résolution captcha")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur 2Captcha: {e}")
            return None
    
    def inject_captcha_solution(self, solution):
        """Injecte la solution du captcha"""
        try:
            self.driver.execute_script(f"document.querySelector('input[name=\"mtcaptcha-verifiedtoken\"]').value = '{solution}';")
            logger.info("✅ Solution injectée")
        except Exception as e:
            logger.warning(f"⚠️ Erreur injection: {e}")
    
    def submit_vote_form(self):
        """Soumet le formulaire de vote"""
        # Chercher le bouton de soumission
        vote_selectors = [
            "#voteBtn",
            "input[type='submit']",
            "button[type='submit']",
            "button:contains('Vote')",
            "*[onclick*='vote']"
        ]
        
        for selector in vote_selectors:
            try:
                if 'contains' in selector:
                    elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Vote')] | //button[contains(text(), 'vote')]")
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed():
                        try:
                            element.click()
                            logger.info(f"✅ Formulaire soumis via: {selector}")
                            time.sleep(5)
                            
                            # Vérifier le résultat
                            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                            if any(word in page_text for word in ["succès", "merci", "thank", "vote validé"]):
                                return True
                            elif any(word in page_text for word in ["erreur", "déjà voté", "cooldown"]):
                                logger.warning("⚠️ Vote déjà effectué ou en cooldown")
                                return False
                        except:
                            continue
            except:
                continue
        
        # Essayer avec JavaScript
        try:
            self.driver.execute_script("document.forms[0].submit();")
            logger.info("✅ Formulaire soumis via JavaScript")
            time.sleep(5)
            return True
        except:
            pass
        
        logger.warning("⚠️ Impossible de soumettre le formulaire")
        return False
    
    def close(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            logger.info("🔒 Driver fermé")

def main():
    parser = argparse.ArgumentParser(description='Script de vote MTCaptcha avec SeleniumBase')
    parser.add_argument('--headless', action='store_true', default=True)
    parser.add_argument('--timeout', type=int, default=120)
    
    args = parser.parse_args()
    
    logger.info("=== 🚀 DÉMARRAGE DU VOTE AUTOMATIQUE SELENIUMBASE ===")
    logger.info(f"Mode headless: {args.headless}")
    
    voter = None
    try:
        voter = MTCaptchaVoterSeleniumBase(
            headless=args.headless,
            timeout=args.timeout
        )
        
        success = voter.vote_oneblock_site1()
        
        if success:
            logger.info("🎉 Résultat final: ✅ SUCCÈS")
            logger.info("=== ✅ VOTE TERMINÉ AVEC SUCCÈS ===")
            exit(0)
        else:
            logger.info("❌ Résultat final: ❌ ÉCHEC")
            logger.info("=== ❌ VOTE ÉCHOUÉ ===")
            exit(1)
            
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {str(e)}")
        logger.info("=== ❌ VOTE ÉCHOUÉ ===")
        exit(1)
    finally:
        if voter:
            voter.close()

if __name__ == "__main__":
    main()