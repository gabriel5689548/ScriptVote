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
from selenium_stealth import stealth
import undetected_chromedriver as uc
import requests
import cloudscraper

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MTCaptchaVoterStealth:
    def __init__(self, headless=True, timeout=120):
        self.timeout = timeout
        self.screenshot_count = 0
        self.api_key = os.getenv('api_key') or os.getenv('TWOCAPTCHA_API_KEY')
        self.username = os.getenv('username', 'zCapsLock')
        
        if not self.api_key:
            raise ValueError("❌ API key non trouvée dans .env !")
        
        logger.info("🔧 Configuration de Selenium avec Stealth Mode...")
        
        try:
            # Utiliser undetected-chromedriver avec selenium-stealth
            options = uc.ChromeOptions()
            
            # Options de base pour GitHub Actions
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            if headless:
                options.add_argument("--headless=new")  # Nouveau mode headless moins détectable
            
            # Options anti-détection supplémentaires
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            
            # Désactiver les extensions qui peuvent être détectées
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins-discovery")
            options.add_argument("--disable-default-apps")
            
            # Headers réalistes
            options.add_argument("--lang=fr-FR,fr;q=0.9,en;q=0.8")
            
            # User agents variés
            user_agents = [
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
            ]
            selected_ua = random.choice(user_agents)
            options.add_argument(f"--user-agent={selected_ua}")
            
            # Créer le driver avec undetected-chromedriver
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Appliquer selenium-stealth pour masquer encore plus les traces
            stealth(self.driver,
                languages=["fr-FR", "fr", "en-US", "en"],
                vendor="Google Inc.",
                platform="Linux",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                run_on_insecure_origins=True
            )
            
            # Ajouter des propriétés JavaScript pour éviter la détection
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    // Masquer webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Masquer les plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Masquer les langues
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['fr-FR', 'fr', 'en-US', 'en']
                    });
                    
                    // Permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // Chrome
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                """
            })
            
            logger.info("✅ Selenium Stealth configuré avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration driver: {e}")
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
    
    def simulate_human_behavior(self):
        """Simule un comportement humain aléatoire"""
        try:
            # Mouvements de souris aléatoires
            actions = webdriver.ActionChains(self.driver)
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                actions.move_by_offset(x, y)
                actions.pause(random.uniform(0.1, 0.3))
            actions.perform()
            
            # Scroll aléatoire
            scroll_amount = random.randint(100, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount//2});")
            
        except Exception as e:
            logger.debug(f"Comportement humain: {e}")
    
    def wait_for_cloudflare_smart(self, max_wait=90):
        """Attend intelligemment que Cloudflare se résolve"""
        logger.info("⏳ Gestion intelligente de Cloudflare...")
        
        start_time = time.time()
        cloudflare_detected = False
        
        # Attendre un peu avant de vérifier (laisser le temps à UC de faire son travail)
        time.sleep(random.uniform(3, 5))
        
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
                    "challenges.cloudflare.com",
                    "cf-chl-bypass"
                ]
                
                if any(indicator in page_source for indicator in cloudflare_indicators):
                    if not cloudflare_detected:
                        logger.info("🛡️ Challenge Cloudflare détecté")
                        cloudflare_detected = True
                        self.save_screenshot("cloudflare_challenge")
                    
                    # Simuler un comportement humain
                    self.simulate_human_behavior()
                    
                    # Chercher et cliquer sur une checkbox Turnstile si présente
                    try:
                        # Chercher l'iframe Turnstile
                        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                        for iframe in iframes:
                            src = iframe.get_attribute("src") or ""
                            if "challenges.cloudflare.com" in src:
                                logger.info("🎯 Iframe Turnstile trouvé")
                                self.driver.switch_to.frame(iframe)
                                
                                # Chercher la checkbox
                                try:
                                    checkbox = WebDriverWait(self.driver, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='checkbox']"))
                                    )
                                    if not checkbox.is_selected():
                                        # Clic humain avec délai aléatoire
                                        time.sleep(random.uniform(1, 2))
                                        checkbox.click()
                                        logger.info("✅ Checkbox Turnstile cliquée")
                                except:
                                    pass
                                
                                self.driver.switch_to.default_content()
                                break
                    except:
                        pass
                    
                    logger.info(f"⏳ Attente Cloudflare... {int(time.time() - start_time)}s/{max_wait}s")
                    time.sleep(random.uniform(2, 4))
                    
                else:
                    if cloudflare_detected:
                        logger.info("✅ Cloudflare résolu!")
                        # Attendre un peu plus pour s'assurer que tout est chargé
                        time.sleep(random.uniform(2, 3))
                    else:
                        logger.info("✅ Pas de Cloudflare détecté")
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur pendant l'attente: {e}")
                time.sleep(2)
        
        # Dernière tentative avec cloudscraper
        logger.info("🔄 Tentative finale avec cloudscraper...")
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
                time.sleep(3)
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Cloudscraper échoué: {e}")
        
        logger.error(f"❌ Timeout après {max_wait}s d'attente Cloudflare")
        self.save_screenshot("cloudflare_timeout")
        return False
    
    def vote_oneblock_site1(self):
        """Vote pour le SITE N°1 sur oneblock.fr avec comportement humain"""
        
        try:
            logger.info("🎯 Démarrage du processus de vote sur oneblock.fr")
            logger.info("🌐 Étape 1: Accès à https://oneblock.fr/vote")
            
            # Aller sur oneblock.fr/vote avec comportement humain
            self.driver.get("https://oneblock.fr/vote")
            
            # Attendre comme un humain
            time.sleep(random.uniform(3, 5))
            self.simulate_human_behavior()
            
            # Remplir le pseudonyme
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
                )
                
                # Clic humain sur le champ
                username_input.click()
                time.sleep(random.uniform(0.5, 1))
                
                # Effacer et taper comme un humain
                username_input.clear()
                for char in self.username:
                    username_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                    
                logger.info(f"✅ Pseudonyme '{self.username}' saisi")
            except Exception as e:
                logger.warning(f"⚠️ Erreur remplissage pseudo: {e}")
            
            # Chercher et cliquer sur ENVOYER
            time.sleep(random.uniform(1, 2))
            envoyer_button = None
            
            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                    envoyer_button = btn
                    break
            
            if envoyer_button:
                # Scroll vers le bouton
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", envoyer_button)
                time.sleep(random.uniform(1, 2))
                
                # Clic humain
                envoyer_button.click()
                logger.info("✅ Clic sur ENVOYER")
                time.sleep(random.uniform(4, 6))
            
            # Chercher le bouton SITE N°1
            self.simulate_human_behavior()
            
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
            original_tab = self.driver.current_window_handle
            
            # Scroll et clic humain
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", site1_button)
            time.sleep(random.uniform(1, 2))
            site1_button.click()
            logger.info("✅ Clic sur SITE N°1")
            
            # Gérer le nouvel onglet
            time.sleep(random.uniform(2, 3))
            
            if len(self.driver.window_handles) > initial_tabs:
                # Nouvel onglet
                new_tab = [h for h in self.driver.window_handles if h != original_tab][0]
                self.driver.switch_to.window(new_tab)
                logger.info(f"🔄 Nouvel onglet: {self.driver.current_url}")
                
                # Attendre résolution Cloudflare
                if self.wait_for_cloudflare_smart():
                    result = self.continue_vote_on_any_page()
                    self.driver.close()
                    self.driver.switch_to.window(original_tab)
                    return result
                else:
                    self.driver.close()
                    self.driver.switch_to.window(original_tab)
                    return False
            else:
                # Pas de nouvel onglet
                if "serveur-prive.net" in self.driver.current_url:
                    if self.wait_for_cloudflare_smart():
                        return self.continue_vote_on_any_page()
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur vote: {e}")
            self.save_screenshot("erreur_vote")
            return False
    
    def continue_vote_on_any_page(self):
        """Continue le vote avec résolution du captcha"""
        try:
            logger.info(f"📍 Page de vote: {self.driver.current_url}")
            
            # Comportement humain
            self.simulate_human_behavior()
            
            # Chercher la sitekey
            sitekey = self.find_mtcaptcha_sitekey()
            if not sitekey:
                logger.error("❌ Sitekey non trouvée")
                self.save_screenshot("sitekey_non_trouvee")
                return False
            
            # Remplir username si nécessaire
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
        
        # Chercher dans les attributs
        for elem in self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey]"):
            key = elem.get_attribute('data-sitekey')
            if key and 'MTPublic-' in key:
                return key
        
        # Chercher dans le HTML
        import re
        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', self.driver.page_source)
        if matches:
            return matches[0]
        
        return None
    
    def fill_username_if_needed(self):
        """Remplit le username avec comportement humain"""
        try:
            for field in self.driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[placeholder*='pseudo']"):
                if field.is_displayed() and not field.get_attribute('value'):
                    field.click()
                    time.sleep(random.uniform(0.5, 1))
                    field.clear()
                    
                    for char in self.username:
                        field.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))
                    
                    logger.info(f"✅ Username '{self.username}' saisi")
                    break
        except:
            pass
    
    def solve_mtcaptcha(self, sitekey):
        """Résout le MTCaptcha"""
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
            
            # Attendre résolution
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
        """Injecte la solution"""
        try:
            self.driver.execute_script(f"document.querySelector('input[name=\"mtcaptcha-verifiedtoken\"]').value = '{solution}';")
            logger.info("✅ Solution injectée")
        except:
            pass
    
    def submit_vote_form(self):
        """Soumet le formulaire avec comportement humain"""
        time.sleep(random.uniform(1, 2))
        
        # Chercher bouton de vote
        for selector in ["#voteBtn", "input[type='submit']", "button[type='submit']"]:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        # Scroll et clic humain
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                        time.sleep(random.uniform(1, 2))
                        elem.click()
                        logger.info(f"✅ Vote soumis via: {selector}")
                        
                        time.sleep(5)
                        
                        # Vérifier résultat
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
    parser = argparse.ArgumentParser(description='Script de vote avec Selenium Stealth')
    parser.add_argument('--headless', action='store_true', default=True)
    parser.add_argument('--timeout', type=int, default=120)
    
    args = parser.parse_args()
    
    logger.info("=== 🚀 DÉMARRAGE DU VOTE SELENIUM STEALTH ===")
    
    voter = None
    try:
        voter = MTCaptchaVoterStealth(
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