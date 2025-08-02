#!/usr/bin/env python3

import time
import logging
import argparse
import os
import random
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests
import cloudscraper
import undetected_chromedriver as uc

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudflareBypasser:
    def __init__(self, headless=True, timeout=120):
        self.timeout = timeout
        self.screenshot_count = 0
        self.api_key = os.getenv('api_key') or os.getenv('TWOCAPTCHA_API_KEY')
        self.username = os.getenv('username', 'zCapsLock')
        
        if not self.api_key:
            raise ValueError("❌ API key non trouvée dans .env !")
        
        logger.info("🔧 Configuration du driver optimisé pour Cloudflare...")
        
        # Méthode 1: Essayer avec undetected-chromedriver d'abord
        try:
            self.setup_undetected_driver(headless)
            logger.info("✅ Undetected ChromeDriver configuré")
        except Exception as e:
            logger.warning(f"⚠️ UC échoué: {e}, fallback vers Selenium standard")
            self.setup_standard_driver(headless)
    
    def setup_undetected_driver(self, headless):
        """Configure undetected-chromedriver pour GitHub Actions"""
        options = uc.ChromeOptions()
        
        # Options spécifiques pour GitHub Actions
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        if headless:
            # Utiliser le nouveau mode headless moins détectable
            options.add_argument("--headless=chrome")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Options pour éviter la détection
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Créer le driver avec la version spécifique pour GitHub Actions
        self.driver = uc.Chrome(
            options=options,
            version_main=None,  # Auto-détection de la version
            driver_executable_path='/usr/local/bin/chromedriver'
        )
        
        # Attendre que le driver soit prêt
        time.sleep(3)
    
    def setup_standard_driver(self, headless):
        """Configuration Selenium standard comme fallback"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        if headless:
            chrome_options.add_argument("--headless")
        
        # Anti-détection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent réaliste
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Masquer les propriétés webdriver
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
    
    def save_screenshot(self, name):
        """Sauvegarde un screenshot"""
        try:
            self.screenshot_count += 1
            filename = f"{name}_{self.screenshot_count}_{int(time.time())}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"📸 Screenshot: {filename}")
            return filename
        except:
            return None
    
    def handle_cloudflare_challenge(self):
        """Gère le challenge Cloudflare de manière intelligente"""
        logger.info("🛡️ Gestion du challenge Cloudflare...")
        
        max_wait = 120  # 2 minutes max
        start_time = time.time()
        challenge_detected = False
        
        while time.time() - start_time < max_wait:
            try:
                # Attendre un peu avant de vérifier
                time.sleep(random.uniform(3, 5))
                
                page_source = self.driver.page_source
                current_url = self.driver.current_url
                
                # Détecter Cloudflare
                cf_indicators = [
                    "Checking your browser",
                    "Just a moment",
                    "cf-browser-verification",
                    "challenges.cloudflare.com",
                    "_cf_chl_opt"
                ]
                
                if any(indicator in page_source for indicator in cf_indicators):
                    if not challenge_detected:
                        logger.info("🔍 Challenge Cloudflare détecté")
                        challenge_detected = True
                        self.save_screenshot("cloudflare_challenge")
                    
                    # Vérifier si c'est un challenge interactif
                    if "challenge-platform" in page_source:
                        logger.info("🎯 Challenge interactif détecté")
                        self.handle_interactive_challenge()
                    
                    logger.info(f"⏳ Attente résolution... {int(time.time() - start_time)}s")
                    
                    # Comportement humain
                    self.simulate_human_behavior()
                    
                else:
                    if challenge_detected:
                        logger.info("✅ Challenge Cloudflare résolu!")
                        time.sleep(random.uniform(2, 3))
                    return True
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur pendant l'attente: {e}")
        
        # Si toujours bloqué, essayer avec cloudscraper
        return self.try_cloudscraper_bypass()
    
    def handle_interactive_challenge(self):
        """Gère les challenges interactifs (checkbox, etc.)"""
        try:
            # Chercher les iframes de challenge
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "challenge" in src or "hcaptcha" in src or "turnstile" in src:
                    logger.info("📦 Iframe de challenge trouvé")
                    
                    # Attendre que l'iframe soit chargé
                    time.sleep(2)
                    
                    # Basculer vers l'iframe
                    self.driver.switch_to.frame(iframe)
                    
                    # Chercher et cliquer sur la checkbox
                    try:
                        checkbox = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='checkbox'], div[role='checkbox']"))
                        )
                        time.sleep(random.uniform(1, 2))
                        checkbox.click()
                        logger.info("✅ Checkbox cliquée")
                    except:
                        logger.info("❌ Pas de checkbox trouvée")
                    
                    # Revenir au contexte principal
                    self.driver.switch_to.default_content()
                    break
                    
        except Exception as e:
            logger.warning(f"⚠️ Erreur challenge interactif: {e}")
    
    def simulate_human_behavior(self):
        """Simule un comportement humain"""
        try:
            # Mouvements de souris aléatoires
            self.driver.execute_script("""
                const event = new MouseEvent('mousemove', {
                    bubbles: true,
                    cancelable: true,
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
            
            # Scroll aléatoire
            scroll = random.randint(50, 200)
            self.driver.execute_script(f"window.scrollBy(0, {scroll});")
            time.sleep(random.uniform(0.5, 1))
            self.driver.execute_script(f"window.scrollBy(0, -{scroll//2});")
            
        except:
            pass
    
    def try_cloudscraper_bypass(self):
        """Essaie de contourner avec cloudscraper"""
        logger.info("🔄 Tentative avec cloudscraper...")
        
        try:
            # Créer un scraper avec configuration avancée
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'linux',
                    'desktop': True
                },
                delay=10
            )
            
            # Copier les cookies de Selenium vers cloudscraper
            for cookie in self.driver.get_cookies():
                scraper.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
            
            # Faire la requête
            response = scraper.get(self.driver.current_url)
            
            if response.status_code == 200 and "Cloudflare" not in response.text:
                logger.info("✅ Cloudscraper a réussi!")
                
                # Transférer les cookies vers Selenium
                self.driver.delete_all_cookies()
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
                time.sleep(3)
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Cloudscraper échoué: {e}")
        
        return False
    
    def vote_oneblock_site1(self):
        """Processus de vote principal"""
        try:
            logger.info("🎯 Démarrage du vote sur oneblock.fr")
            
            # Aller sur oneblock.fr/vote
            self.driver.get("https://oneblock.fr/vote")
            
            # Gérer Cloudflare si nécessaire
            if not self.handle_cloudflare_challenge():
                logger.error("❌ Impossible de passer Cloudflare sur oneblock.fr")
                return False
            
            # Attendre et remplir le pseudo
            time.sleep(random.uniform(3, 5))
            
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username']"))
                )
                username_input.clear()
                username_input.send_keys(self.username)
                logger.info(f"✅ Pseudo '{self.username}' saisi")
            except:
                logger.warning("⚠️ Champ pseudo non trouvé")
            
            # Chercher et cliquer sur ENVOYER
            time.sleep(random.uniform(1, 2))
            
            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                    btn.click()
                    logger.info("✅ Clic sur ENVOYER")
                    time.sleep(5)
                    break
            
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
            
            # Cliquer sur SITE N°1
            initial_tabs = len(self.driver.window_handles)
            site1_button.click()
            logger.info("✅ Clic sur SITE N°1")
            
            # Gérer le nouvel onglet
            time.sleep(3)
            
            if len(self.driver.window_handles) > initial_tabs:
                # Nouvel onglet ouvert
                original_tab = self.driver.current_window_handle
                new_tab = [h for h in self.driver.window_handles if h != original_tab][0]
                self.driver.switch_to.window(new_tab)
                logger.info(f"🔄 Nouvel onglet: {self.driver.current_url}")
                
                # Gérer Cloudflare sur le site de vote
                if self.handle_cloudflare_challenge():
                    result = self.continue_vote_on_page()
                    self.driver.close()
                    self.driver.switch_to.window(original_tab)
                    return result
                else:
                    self.driver.close()
                    self.driver.switch_to.window(original_tab)
                    return False
            else:
                # Pas de nouvel onglet
                current_url = self.driver.current_url
                if "serveur-prive.net" in current_url:
                    if self.handle_cloudflare_challenge():
                        return self.continue_vote_on_page()
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur vote: {e}")
            self.save_screenshot("erreur_vote")
            return False
    
    def continue_vote_on_page(self):
        """Continue le vote sur la page actuelle"""
        try:
            logger.info(f"📍 Page de vote: {self.driver.current_url}")
            
            # Chercher la sitekey MTCaptcha
            sitekey = self.find_mtcaptcha_sitekey()
            if not sitekey:
                logger.error("❌ Sitekey non trouvée")
                return False
            
            # Remplir le pseudo si nécessaire
            self.fill_username_if_needed()
            
            # Résoudre le captcha
            solution = self.solve_mtcaptcha(sitekey)
            if not solution:
                return False
            
            # Injecter et soumettre
            self.inject_captcha_solution(solution)
            return self.submit_vote_form()
            
        except Exception as e:
            logger.error(f"❌ Erreur continue_vote: {e}")
            return False
    
    def find_mtcaptcha_sitekey(self):
        """Trouve la sitekey MTCaptcha"""
        # Chercher dans les scripts
        for script in self.driver.find_elements(By.TAG_NAME, "script"):
            text = script.get_attribute('innerHTML') or ''
            if 'MTPublic-' in text:
                import re
                matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', text)
                if matches:
                    return matches[0]
        
        # Chercher dans le HTML
        import re
        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', self.driver.page_source)
        if matches:
            return matches[0]
        
        return None
    
    def fill_username_if_needed(self):
        """Remplit le username si nécessaire"""
        try:
            for field in self.driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[placeholder*='pseudo']"):
                if field.is_displayed() and not field.get_attribute('value'):
                    field.clear()
                    field.send_keys(self.username)
                    logger.info(f"✅ Username '{self.username}' saisi")
                    break
        except:
            pass
    
    def solve_mtcaptcha(self, sitekey):
        """Résout le MTCaptcha avec 2Captcha"""
        try:
            response = requests.post('http://2captcha.com/in.php', data={
                'key': self.api_key,
                'method': 'mt_captcha',
                'sitekey': sitekey,
                'pageurl': self.driver.current_url,
                'json': 1
            })
            
            result = response.json()
            if result.get('status') != 1:
                logger.error(f"❌ Erreur 2Captcha: {result.get('request')}")
                return None
            
            captcha_id = result['request']
            logger.info(f"🎯 Captcha ID: {captcha_id}")
            
            # Attendre la résolution
            for i in range(30):
                time.sleep(10)
                check = requests.get(f'http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}&json=1')
                check_result = check.json()
                
                if check_result.get('status') == 1:
                    logger.info("🎉 Captcha résolu!")
                    return check_result.get('request')
                elif check_result.get('error') != 'CAPCHA_NOT_READY':
                    logger.error(f"❌ Erreur: {check_result.get('error')}")
                    return None
                
                logger.info(f"⏳ Résolution... {i+1}/30")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur 2Captcha: {e}")
            return None
    
    def inject_captcha_solution(self, solution):
        """Injecte la solution du captcha"""
        try:
            self.driver.execute_script(f"document.querySelector('input[name=\"mtcaptcha-verifiedtoken\"]').value = '{solution}';")
            logger.info("✅ Solution injectée")
        except:
            pass
    
    def submit_vote_form(self):
        """Soumet le formulaire de vote"""
        time.sleep(1)
        
        # Chercher le bouton de vote
        for selector in ["#voteBtn", "input[type='submit']", "button[type='submit']"]:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        elem.click()
                        logger.info(f"✅ Vote soumis via: {selector}")
                        time.sleep(5)
                        
                        # Vérifier le résultat
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        if any(word in page_text for word in ["succès", "merci", "vote validé"]):
                            return True
                        elif any(word in page_text for word in ["erreur", "déjà voté"]):
                            logger.warning("⚠️ Vote déjà effectué")
                            return False
            except:
                continue
        
        # JavaScript en dernier recours
        try:
            self.driver.execute_script("document.forms[0].submit();")
            logger.info("✅ Formulaire soumis via JS")
            time.sleep(5)
            return True
        except:
            pass
        
        return False
    
    def close(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            logger.info("🔒 Driver fermé")

def main():
    parser = argparse.ArgumentParser(description='Script optimisé pour contourner Cloudflare')
    parser.add_argument('--headless', action='store_true', default=True)
    parser.add_argument('--timeout', type=int, default=120)
    
    args = parser.parse_args()
    
    logger.info("=== 🚀 DÉMARRAGE DU VOTE CLOUDFLARE BYPASS ===")
    
    voter = None
    try:
        voter = CloudflareBypasser(
            headless=args.headless,
            timeout=args.timeout
        )
        
        success = voter.vote_oneblock_site1()
        
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