#!/usr/bin/env python3

import time
import logging
import argparse
import os
import re
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MTCaptchaVoterUndetected:
    def __init__(self, headless=True, timeout=120):
        self.timeout = timeout
        self.api_key = os.getenv('api_key') or os.getenv('TWOCAPTCHA_API_KEY')
        self.username = os.getenv('username', 'zCapsLock')
        
        # Configuration proxy
        self.proxy_host = os.getenv('PROXY_HOST')
        self.proxy_port = os.getenv('PROXY_PORT')
        self.proxy_user = os.getenv('PROXY_USER')
        self.proxy_pass = os.getenv('PROXY_PASS')
        
        if not self.api_key:
            raise ValueError("❌ API key non trouvée dans .env !")
        
        logger.info("🔧 Configuration undetected-chromedriver...")
        
        # Options Chrome
        chrome_options = uc.ChromeOptions()
        
        # Configuration de base
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-gpu")
        
        # Taille de fenêtre
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # User agent réaliste
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        
        # Configuration proxy si disponible
        if self.proxy_host and self.proxy_port:
            if self.proxy_user and self.proxy_pass:
                proxy_string = f"{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}"
            else:
                proxy_string = f"{self.proxy_host}:{self.proxy_port}"
            chrome_options.add_argument(f'--proxy-server=http://{proxy_string}')
            logger.info(f"🌐 Proxy configuré: {self.proxy_host}:{self.proxy_port}")
        
        # Mode headless - ATTENTION: moins efficace contre Cloudflare
        if headless:
            chrome_options.add_argument("--headless=new")
            logger.warning("⚠️ Mode headless activé - détection Cloudflare plus probable")
        
        try:
            # Utiliser Chrome version 126 ou moins si possible
            self.driver = uc.Chrome(
                options=chrome_options,
                version_main=126,  # Version recommandée pour bypass
                use_subprocess=True,  # Aide à éviter la détection
            )
            logger.info("✅ Driver undetected-chromedriver configuré")
            
            # Patch supplémentaire pour éviter la détection
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration driver: {e}")
            raise
    
    def wait_for_cloudflare(self, max_wait=30):
        """Attendre que Cloudflare nous laisse passer"""
        logger.info("⏳ Vérification Cloudflare...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                title = self.driver.title.lower()
                body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                
                # Vérifier si on est toujours sur Cloudflare
                cf_indicators = [
                    "just a moment",
                    "checking your browser",
                    "verifying you are human",
                    "please wait",
                    "cf-browser-verification"
                ]
                
                if not any(indicator in title or indicator in body_text for indicator in cf_indicators):
                    logger.info("✅ Cloudflare passé!")
                    return True
                
                # Chercher et cliquer sur un éventuel checkbox
                try:
                    cf_checkbox = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='challenges.cloudflare.com']")
                    if cf_checkbox:
                        logger.info("🖱️ Checkbox Cloudflare détecté")
                        # Ne pas cliquer automatiquement en mode headless
                        if not "--headless" in self.driver.options.arguments:
                            self.driver.switch_to.frame(cf_checkbox)
                            checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                            checkbox.click()
                            self.driver.switch_to.default_content()
                            logger.info("✅ Checkbox cliqué")
                except:
                    pass
                
                logger.info(f"⏳ Cloudflare en cours... ({int(time.time() - start_time)}/{max_wait}s)")
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur vérification Cloudflare: {e}")
                time.sleep(2)
        
        logger.error("❌ Timeout Cloudflare")
        return False
    
    def vote_oneblock_site1(self):
        """Vote pour le SITE N°1 sur oneblock.fr"""
        
        try:
            logger.info("🎯 Démarrage du vote sur oneblock.fr")
            
            # Charger la page
            self.driver.get("https://oneblock.fr/vote")
            time.sleep(3)
            
            # Remplir le pseudo
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
                )
                username_input.clear()
                username_input.send_keys(self.username)
                logger.info(f"✅ Pseudonyme '{self.username}' saisi")
            except Exception as e:
                logger.warning(f"⚠️ Erreur saisie pseudo: {e}")
            
            # Cliquer sur ENVOYER
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                        btn.click()
                        logger.info("✅ Clic sur ENVOYER")
                        time.sleep(3)
                        break
            except Exception as e:
                logger.warning(f"⚠️ Erreur clic ENVOYER: {e}")
            
            # Chercher et cliquer sur SITE N°1
            logger.info("🔍 Recherche du bouton SITE N°1...")
            
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            site1_button = None
            
            for btn in buttons:
                text = btn.text.strip()
                if "SITE N°1" in text and "Votez maintenant" in text and btn.is_displayed():
                    site1_button = btn
                    break
            
            if site1_button:
                # Mémoriser les onglets
                initial_tabs = len(self.driver.window_handles)
                original_tab = self.driver.current_window_handle
                
                # Cliquer
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", site1_button)
                time.sleep(1)
                site1_button.click()
                logger.info("✅ Clic sur SITE N°1")
                
                # Attendre nouvel onglet
                time.sleep(5)
                
                # Vérifier nouvel onglet
                if len(self.driver.window_handles) > initial_tabs:
                    for handle in self.driver.window_handles:
                        if handle != original_tab:
                            self.driver.switch_to.window(handle)
                            logger.info(f"🔄 Nouvel onglet: {self.driver.current_url}")
                            
                            # Continuer le vote
                            result = self.continue_vote_on_serveur_prive()
                            
                            # Fermer et revenir
                            self.driver.close()
                            self.driver.switch_to.window(original_tab)
                            
                            return result
                
                # Vérifier si on est sur serveur-prive
                if "serveur-prive.net" in self.driver.current_url:
                    return self.continue_vote_on_serveur_prive()
            
            logger.error("❌ Bouton SITE N°1 non trouvé")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur vote_oneblock: {e}")
            return False
    
    def continue_vote_on_serveur_prive(self):
        """Continue le vote sur serveur-prive.net"""
        
        try:
            current_url = self.driver.current_url
            logger.info(f"📍 Page de vote: {current_url}")
            
            # Gérer Cloudflare
            if not self.wait_for_cloudflare():
                # Screenshot si échec
                try:
                    os.makedirs("screenshots", exist_ok=True)
                    screenshot_path = f"screenshots/cf_block_undetected_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"📸 Screenshot: {screenshot_path}")
                except:
                    pass
                return False
            
            # Attendre chargement complet
            time.sleep(3)
            
            # Chercher MTCaptcha sitekey
            logger.info("🔍 Recherche MTCaptcha sitekey...")
            sitekey = None
            
            # Méthode 1: Scripts
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                try:
                    script_text = script.get_attribute('innerHTML') or ''
                    if 'MTPublic-' in script_text:
                        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', script_text)
                        if matches:
                            sitekey = matches[0]
                            logger.info(f"✅ Sitekey trouvée: {sitekey}")
                            break
                except:
                    continue
            
            # Méthode 2: Attributs
            if not sitekey:
                elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey], [data-site-key]")
                for elem in elements:
                    key = elem.get_attribute('data-sitekey') or elem.get_attribute('data-site-key')
                    if key and 'MTPublic-' in key:
                        sitekey = key
                        logger.info(f"✅ Sitekey dans attribut: {sitekey}")
                        break
            
            # Méthode 3: Page source
            if not sitekey:
                page_source = self.driver.page_source
                matches = re.findall(r'(MTPublic-[a-zA-Z0-9]+)', page_source)
                if matches:
                    sitekey = matches[0]
                    logger.info(f"✅ Sitekey dans source: {sitekey}")
            
            if not sitekey:
                logger.error("❌ Sitekey non trouvée")
                return False
            
            # Remplir username
            try:
                username_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[id*='username'], input[placeholder*='pseudo']")
                for field in username_fields:
                    if field.is_displayed():
                        field.clear()
                        field.send_keys(self.username)
                        logger.info("✅ Username rempli")
                        break
            except:
                pass
            
            # Résoudre avec 2Captcha
            logger.info("📤 Envoi à 2Captcha...")
            
            submit_data = {
                'key': self.api_key,
                'method': 'mt_captcha',
                'sitekey': sitekey,
                'pageurl': current_url,
                'json': 1
            }
            
            response = requests.post('http://2captcha.com/in.php', data=submit_data, timeout=30)
            result = response.json()
            
            if result['status'] != 1:
                logger.error(f"❌ Erreur 2Captcha: {result}")
                return False
            
            captcha_id = result['request']
            logger.info(f"🎯 Captcha ID: {captcha_id}")
            
            # Attendre résolution
            for attempt in range(30):
                time.sleep(10)
                
                check_response = requests.get(
                    f'http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}&json=1',
                    timeout=30
                )
                check_result = check_response.json()
                
                if check_result['status'] == 1:
                    solution = check_result['request']
                    logger.info("🎉 Captcha résolu!")
                    break
                elif 'error' in check_result and check_result['error'] != 'CAPCHA_NOT_READY':
                    logger.error(f"❌ Erreur: {check_result}")
                    return False
                else:
                    logger.info(f"⏳ Attente... ({attempt+1}/30)")
            else:
                logger.error("❌ Timeout résolution")
                return False
            
            # Injecter solution
            logger.info("💉 Injection solution...")
            
            self.driver.execute_script(f"""
                var input = document.querySelector('input[name="mtcaptcha-verifiedtoken"]');
                if (!input) {{
                    input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'mtcaptcha-verifiedtoken';
                    document.forms[0].appendChild(input);
                }}
                input.value = '{solution}';
            """)
            
            # Soumettre
            logger.info("📤 Soumission...")
            
            # Chercher bouton submit
            submit_selectors = [
                "#voteBtn",
                "input[type='submit']",
                "button[type='submit']",
                "button:contains('Vote')"
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            elem.click()
                            logger.info(f"✅ Clic sur: {selector}")
                            submitted = True
                            break
                    if submitted:
                        break
                except:
                    continue
            
            if not submitted:
                self.driver.execute_script("document.forms[0].submit();")
                logger.info("✅ Submit via JS")
            
            # Vérifier résultat
            time.sleep(5)
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            success_keywords = ["succès", "success", "merci", "thank you", "vote validé"]
            error_keywords = ["erreur", "error", "déjà voté", "already voted"]
            
            for keyword in success_keywords:
                if keyword in page_text:
                    logger.info(f"🎉 Vote réussi! ('{keyword}' trouvé)")
                    return True
            
            for keyword in error_keywords:
                if keyword in page_text:
                    logger.warning(f"❌ Vote échoué: '{keyword}'")
                    return False
            
            logger.info("✅ Vote probablement réussi")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur serveur-prive: {e}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Driver fermé")

def main():
    parser = argparse.ArgumentParser(description='Vote avec undetected-chromedriver')
    parser.add_argument('--headless', action='store_true', default=True, help='Mode headless')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout')
    
    args = parser.parse_args()
    
    logger.info("=== 🚀 DÉMARRAGE VOTE UNDETECTED-CHROMEDRIVER ===")
    logger.info(f"Mode headless: {args.headless}")
    
    voter = None
    try:
        voter = MTCaptchaVoterUndetected(headless=args.headless, timeout=args.timeout)
        
        success = voter.vote_oneblock_site1()
        
        if success:
            logger.info("🎉 SUCCÈS")
            exit(0)
        else:
            logger.info("❌ ÉCHEC")
            exit(1)
            
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {e}")
        exit(1)
    finally:
        if voter:
            voter.close()

if __name__ == "__main__":
    main()