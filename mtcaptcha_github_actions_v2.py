#!/usr/bin/env python3

import time
import logging
import argparse
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
import cloudscraper

# Alternative avec undetected-chromedriver si disponible
try:
    import undetected_chromedriver as uc
    HAS_UNDETECTED = True
except ImportError:
    HAS_UNDETECTED = False
    logging.warning("undetected-chromedriver non disponible, utilisation de selenium standard")

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MTCaptchaVoterV2:
    def __init__(self, headless=True, timeout=120, use_undetected=False):
        self.timeout = timeout
        self.screenshot_count = 0
        self.api_key = os.getenv('api_key') or os.getenv('TWOCAPTCHA_API_KEY')
        self.username = os.getenv('username', 'zCapsLock')
        
        if not self.api_key:
            raise ValueError("❌ API key non trouvée dans .env !")
        
        logger.info("🔧 Configuration du driver Selenium V2...")
        
        if use_undetected and HAS_UNDETECTED:
            logger.info("🚀 Utilisation de undetected-chromedriver")
            # Configuration avec undetected-chromedriver
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            if headless:
                options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            
            try:
                self.driver = uc.Chrome(options=options, version_main=None)
                logger.info("✅ Undetected ChromeDriver configuré avec succès")
            except Exception as e:
                logger.warning(f"⚠️ Erreur avec undetected-chromedriver: {e}")
                logger.info("🔄 Fallback vers Selenium standard")
                self._setup_standard_driver(headless)
        else:
            self._setup_standard_driver(headless)
    
    def _setup_standard_driver(self, headless):
        """Configuration du driver Selenium standard"""
        chrome_options = Options()
        chrome_options.add_argument("--headless") if headless else None
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✅ Driver Selenium standard configuré")
    
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
    
    def handle_cloudflare_smart(self):
        """Gestion intelligente de Cloudflare avec plusieurs stratégies"""
        logger.info("🛡️ Détection et gestion de Cloudflare...")
        
        # Stratégie 1: Attendre que Cloudflare se résolve
        for i in range(10):
            page_source = self.driver.page_source
            if not any(indicator in page_source for indicator in ["Cloudflare", "_cf_chl_opt", "Just a moment"]):
                logger.info("✅ Page chargée sans Cloudflare")
                return True
            
            logger.info(f"⏳ Cloudflare détecté, attente {i+1}/10...")
            time.sleep(3)
            
            # Stratégie 2: Essayer de cliquer sur des éléments Cloudflare
            try:
                # Chercher le checkbox Cloudflare
                cf_checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                if cf_checkbox.is_displayed():
                    cf_checkbox.click()
                    logger.info("✅ Checkbox Cloudflare cliqué")
                    time.sleep(5)
            except:
                pass
        
        # Stratégie 3: Utiliser cloudscraper comme fallback
        logger.info("🔄 Tentative avec cloudscraper...")
        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(self.driver.current_url)
            if response.status_code == 200 and "Cloudflare" not in response.text:
                logger.info("✅ Cloudflare contourné avec cloudscraper")
                # Transférer les cookies
                for cookie in scraper.cookies:
                    try:
                        self.driver.add_cookie({
                            'name': cookie.name,
                            'value': cookie.value,
                            'domain': cookie.domain,
                            'path': cookie.path or '/'
                        })
                    except:
                        pass
                self.driver.refresh()
                return True
        except Exception as e:
            logger.warning(f"⚠️ Erreur cloudscraper: {e}")
        
        self.save_screenshot("cloudflare_blocked")
        return False
    
    def vote_with_fallback(self):
        """Vote avec gestion des sites alternatifs"""
        # Essayer d'abord le Site N°1
        if self.vote_oneblock_site1():
            return True
        
        logger.info("🔄 Site N°1 échoué, tentative sur d'autres sites...")
        
        # Chercher d'autres boutons de vote
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            vote_buttons = []
            
            for btn in all_buttons:
                text = btn.text.strip()
                if "SITE N°" in text and "Votez maintenant" in text and btn.is_displayed():
                    vote_buttons.append((btn, text))
            
            logger.info(f"📊 {len(vote_buttons)} sites de vote trouvés")
            
            # Essayer chaque site
            for btn, text in vote_buttons:
                logger.info(f"🎯 Tentative sur: {text}")
                try:
                    btn.click()
                    time.sleep(3)
                    
                    # Gérer le nouvel onglet ou la page actuelle
                    if len(self.driver.window_handles) > 1:
                        original_tab = self.driver.current_window_handle
                        new_tab = [h for h in self.driver.window_handles if h != original_tab][0]
                        self.driver.switch_to.window(new_tab)
                        
                        if self.handle_cloudflare_smart():
                            if self.continue_vote_on_any_page():
                                logger.info(f"🎉 Vote réussi sur {text}!")
                                return True
                        
                        self.driver.close()
                        self.driver.switch_to.window(original_tab)
                    else:
                        if self.handle_cloudflare_smart():
                            if self.continue_vote_on_any_page():
                                logger.info(f"🎉 Vote réussi sur {text}!")
                                return True
                except Exception as e:
                    logger.warning(f"⚠️ Erreur sur {text}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Erreur fallback: {e}")
        
        return False
    
    def vote_oneblock_site1(self):
        """Vote pour le SITE N°1 sur oneblock.fr"""
        try:
            logger.info("🎯 Démarrage du processus de vote sur oneblock.fr")
            
            # Aller sur oneblock.fr/vote
            self.driver.get("https://oneblock.fr/vote")
            time.sleep(3)
            
            # Remplir le pseudonyme
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
                )
                username_input.clear()
                username_input.send_keys(self.username)
                logger.info(f"✅ Pseudonyme '{self.username}' saisi")
            except Exception as e:
                logger.warning(f"⚠️ Erreur pseudonyme: {e}")
            
            # Cliquer sur ENVOYER
            envoyer_button = None
            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                    envoyer_button = btn
                    break
            
            if envoyer_button:
                envoyer_button.click()
                logger.info("✅ Clic sur ENVOYER")
                time.sleep(5)
            
            # Chercher le bouton SITE N°1
            site1_button = None
            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                text = btn.text.strip()
                if "SITE N°1" in text and btn.is_displayed():
                    site1_button = btn
                    logger.info(f"🎯 Bouton trouvé: '{text}'")
                    break
            
            if not site1_button:
                logger.warning("⚠️ Bouton SITE N°1 non trouvé")
                self.save_screenshot("site1_non_trouve")
                return False
            
            # Cliquer et gérer le nouvel onglet
            initial_tabs = len(self.driver.window_handles)
            site1_button.click()
            logger.info("✅ Clic sur SITE N°1")
            
            # Attendre nouvel onglet ou changement de page
            time.sleep(3)
            
            if len(self.driver.window_handles) > initial_tabs:
                # Nouvel onglet ouvert
                original_tab = self.driver.current_window_handle
                new_tab = [h for h in self.driver.window_handles if h != original_tab][0]
                self.driver.switch_to.window(new_tab)
                logger.info(f"🔄 Basculé vers: {self.driver.current_url}")
                
                # Gérer Cloudflare et voter
                if self.handle_cloudflare_smart():
                    result = self.continue_vote_on_any_page()
                    self.driver.close()
                    self.driver.switch_to.window(original_tab)
                    return result
                else:
                    self.driver.close()
                    self.driver.switch_to.window(original_tab)
                    return False
            else:
                # Pas de nouvel onglet, vérifier la page actuelle
                if "serveur-prive.net" in self.driver.current_url:
                    if self.handle_cloudflare_smart():
                        return self.continue_vote_on_any_page()
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur vote_oneblock_site1: {e}")
            self.save_screenshot("erreur_vote")
            return False
    
    def continue_vote_on_any_page(self):
        """Continue le processus de vote sur la page actuelle"""
        try:
            logger.info(f"📍 Traitement de: {self.driver.current_url}")
            
            # Chercher la sitekey MTCaptcha
            sitekey = self.find_mtcaptcha_sitekey()
            if not sitekey:
                logger.error("❌ Sitekey MTCaptcha non trouvée")
                self.save_screenshot("sitekey_non_trouvee")
                return False
            
            logger.info(f"✅ Sitekey trouvée: {sitekey}")
            
            # Remplir le pseudonyme si nécessaire
            self.fill_username_if_needed()
            
            # Résoudre le captcha
            solution = self.solve_mtcaptcha(sitekey)
            if not solution:
                return False
            
            # Injecter la solution
            self.inject_captcha_solution(solution)
            
            # Soumettre le formulaire
            if self.submit_vote_form():
                logger.info("🎉 Vote soumis avec succès!")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur continue_vote: {e}")
            self.save_screenshot("erreur_continue_vote")
            return False
    
    def find_mtcaptcha_sitekey(self):
        """Trouve la sitekey MTCaptcha dans la page"""
        # Chercher dans les scripts
        for script in self.driver.find_elements(By.TAG_NAME, "script"):
            script_text = script.get_attribute('innerHTML') or ''
            if 'MTPublic-' in script_text:
                import re
                matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', script_text)
                if matches:
                    return matches[0]
        
        # Chercher dans les attributs
        for elem in self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey], [data-site-key]"):
            key = elem.get_attribute('data-sitekey') or elem.get_attribute('data-site-key')
            if key and 'MTPublic-' in key:
                return key
        
        # Chercher dans le HTML
        import re
        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', self.driver.page_source)
        if matches:
            return matches[0]
        
        return None
    
    def fill_username_if_needed(self):
        """Remplit le champ username si nécessaire"""
        try:
            for field in self.driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[id*='username'], input[placeholder*='pseudo']"):
                if field.is_displayed() and not field.get_attribute('value'):
                    field.clear()
                    field.send_keys(self.username)
                    logger.info(f"✅ Pseudonyme '{self.username}' saisi")
                    break
        except:
            pass
    
    def solve_mtcaptcha(self, sitekey):
        """Résout le captcha avec 2Captcha"""
        logger.info("📤 Envoi à 2Captcha...")
        
        try:
            response = requests.post('http://2captcha.com/in.php', data={
                'key': self.api_key,
                'method': 'mt_captcha',
                'sitekey': sitekey,
                'pageurl': self.driver.current_url,
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
        for selector in ["#voteBtn", "input[type='submit']", "button[type='submit']"]:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        elem.click()
                        logger.info(f"✅ Formulaire soumis via: {selector}")
                        time.sleep(5)
                        
                        # Vérifier le résultat
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        if any(word in page_text for word in ["succès", "merci", "thank", "vote validé", "classement"]):
                            return True
                        elif any(word in page_text for word in ["erreur", "déjà voté", "cooldown"]):
                            logger.warning("⚠️ Vote déjà effectué ou en cooldown")
                            return False
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
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Driver fermé")

def main():
    parser = argparse.ArgumentParser(description='Script de vote MTCaptcha V2')
    parser.add_argument('--headless', action='store_true', default=True)
    parser.add_argument('--use-undetected', action='store_true', help='Utiliser undetected-chromedriver')
    parser.add_argument('--timeout', type=int, default=120)
    
    args = parser.parse_args()
    
    logger.info("=== 🚀 DÉMARRAGE DU VOTE AUTOMATIQUE V2 ===")
    
    voter = None
    try:
        voter = MTCaptchaVoterV2(
            headless=args.headless,
            timeout=args.timeout,
            use_undetected=args.use_undetected
        )
        
        # Essayer avec fallback sur plusieurs sites
        success = voter.vote_with_fallback()
        
        if success:
            logger.info("🎉 VOTE RÉUSSI!")
            exit(0)
        else:
            logger.info("❌ VOTE ÉCHOUÉ")
            exit(1)
            
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {e}")
        exit(1)
    finally:
        if voter:
            voter.close()

if __name__ == "__main__":
    main()