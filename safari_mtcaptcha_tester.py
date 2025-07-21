#!/usr/bin/env python3
"""
Safari MTCaptcha Testing Script
Version Safari qui conserve les données préremplies comme zCapsLock
"""

import os
import time
import logging
import argparse
import requests
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('safari_mtcaptcha_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SafariMTCaptchaTester:
    def __init__(self, api_key: str, timeout: int = 300):
        self.api_key = api_key
        self.timeout = timeout
        self.driver = None
        self.wait = None
        
    def setup_safari_driver(self):
        """Configure et initialise le driver Safari"""
        logger.info("Configuration du driver Safari...")
        
        try:
            # Activer le développeur Safari si nécessaire
            safari_options = SafariOptions()
            
            # Safari driver (pas d'options headless disponibles)
            self.driver = webdriver.Safari(options=safari_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("Driver Safari configuré avec succès")
            logger.info("💡 Safari conservera automatiquement 'zCapsLock' si déjà saisi")
            
        except Exception as e:
            logger.error(f"Erreur configuration Safari: {str(e)}")
            logger.info("💡 Astuce: Activez 'Développer > Autoriser l'automatisation' dans Safari")
            raise

    def get_mtcaptcha_sitekey(self, url: str) -> Optional[str]:
        """Récupère la clé sitekey du MTCaptcha"""
        logger.info(f"Accès à la page Safari: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # Vérifier si le pseudonyme est déjà prérempli
            self.check_pseudonyme_status()
            
            # Recherche de la sitekey JavaScript
            try:
                sitekey = self.driver.execute_script("""
                    if (typeof mtcaptchaConfig !== 'undefined' && mtcaptchaConfig.sitekey) {
                        return mtcaptchaConfig.sitekey;
                    }
                    return null;
                """)
                if sitekey:
                    logger.info(f"✅ Sitekey MTCaptcha trouvée: {sitekey}")
                    return sitekey
            except Exception as e:
                logger.debug(f"Erreur lecture config JS: {str(e)}")
            
            # Recherche dans le code source comme fallback
            try:
                page_source = self.driver.page_source
                import re
                
                patterns = [
                    r'sitekey\s*:\s*["\']([^"\']+)["\']',
                    r'MTPublic-[a-zA-Z0-9]+'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        sitekey = match.group(1) if len(match.groups()) > 0 else match.group(0)
                        logger.info(f"✅ Sitekey trouvée via regex: {sitekey}")
                        return sitekey
                        
            except Exception as e:
                logger.debug(f"Erreur recherche regex: {str(e)}")
                    
            logger.error("❌ Aucune sitekey MTCaptcha trouvée")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération: {str(e)}")
            return None

    def check_pseudonyme_status(self):
        """Vérifie si le pseudonyme est déjà prérempli et trouve le nom exact du champ"""
        try:
            # D'abord, inspectons tous les champs input sur la page
            logger.info("🔍 Recherche de tous les champs input...")
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            
            for i, input_elem in enumerate(all_inputs):
                name = input_elem.get_attribute('name')
                id_attr = input_elem.get_attribute('id')
                placeholder = input_elem.get_attribute('placeholder')
                input_type = input_elem.get_attribute('type')
                value = input_elem.get_attribute('value')
                
                logger.info(f"Input #{i}: name='{name}', id='{id_attr}', type='{input_type}', placeholder='{placeholder}', value='{value}'")
            
            # Maintenant cherchons spécifiquement le champ pseudonyme
            pseudonyme_selectors = [
                "input[name='pseudonyme']",
                "input[name='username']", 
                "input[name='pseudo']",
                "input[name='player']",
                "input[name='playername']",
                "input[id='pseudonyme']",
                "input[id='username']",
                "input[id='pseudo']",
                "input[placeholder*='pseudo' i]",
                "input[placeholder*='nom' i]",
                "input[type='text']"  # Fallback
            ]
            
            for selector in pseudonyme_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    current_value = element.get_attribute('value')
                    name = element.get_attribute('name')
                    id_attr = element.get_attribute('id')
                    
                    logger.info(f"🎯 Champ trouvé: {selector} (name='{name}', id='{id_attr}')")
                    
                    if current_value and current_value.strip():
                        logger.info(f"✅ Pseudonyme déjà prérempli: '{current_value}'")
                        return True
                    else:
                        logger.info("⚠️  Champ pseudonyme vide, remplissage avec zCapsLock...")
                        
                        # Essayer plusieurs méthodes pour remplir
                        try:
                            element.clear()
                            element.send_keys("zCapsLock")
                            
                            # Vérifier que ça a marché
                            new_value = element.get_attribute('value')
                            if new_value == "zCapsLock":
                                logger.info(f"✅ Pseudonyme 'zCapsLock' saisi avec succès dans {selector}")
                                return True
                            else:
                                logger.warning(f"⚠️  Valeur après saisie: '{new_value}' (attendu: 'zCapsLock')")
                                
                        except Exception as e:
                            logger.warning(f"⚠️  Erreur lors de la saisie dans {selector}: {e}")
                            continue
                            
                except NoSuchElementException:
                    continue
                    
            logger.warning("⚠️  Aucun champ pseudonyme trouvé ou accessible")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification pseudonyme: {str(e)}")
            return False

    def solve_mtcaptcha(self, sitekey: str, page_url: str) -> Optional[str]:
        """Résout le MTCaptcha via l'API 2Captcha"""
        logger.info("📤 Envoi de la demande à 2Captcha...")
        
        # Soumission du captcha
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': self.api_key,
            'method': 'mt_captcha',
            'sitekey': sitekey,
            'pageurl': page_url,
            'json': 1
        }
        
        try:
            response = requests.post(submit_url, data=submit_data, timeout=30)
            result = response.json()
            
            if result['status'] != 1:
                logger.error(f"❌ Erreur soumission: {result}")
                return None
                
            captcha_id = result['request']
            logger.info(f"📋 Captcha soumis avec ID: {captcha_id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur soumission: {str(e)}")
            return None

        # Récupération de la solution
        get_url = "http://2captcha.com/res.php"
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                time.sleep(10)
                
                get_data = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                
                response = requests.get(get_url, params=get_data, timeout=30)
                result = response.json()
                
                if result['status'] == 1:
                    logger.info("🎉 MTCaptcha résolu avec succès!")
                    return result['request']
                elif result['request'] == 'CAPCHA_NOT_READY':
                    logger.info("⏳ Résolution en cours...")
                    continue
                else:
                    logger.error(f"❌ Erreur résolution: {result}")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Erreur récupération: {str(e)}")
                continue
                
        logger.error("⏰ Timeout lors de la résolution")
        return None

    def inject_solution(self, solution: str) -> bool:
        """Injecte la solution MTCaptcha"""
        logger.info("💉 Injection de la solution...")
        
        try:
            # Chercher les champs de réponse MTCaptcha
            selectors = [
                "input[name='mtcaptcha-verifiedtoken']",
                "textarea[name='mtcaptcha-verifiedtoken']",
                "input[name='mt_token']",
                "textarea[name='mt_token']",
                "#mtcaptcha-verifiedtoken"
            ]
            
            injected = False
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.driver.execute_script(f"arguments[0].value = '{solution}';", element)
                    logger.info(f"✅ Solution injectée dans: {selector}")
                    injected = True
                    break
                except NoSuchElementException:
                    continue
            
            if not injected:
                # Fallback via API JavaScript
                script = f"""
                if (window.mtcaptcha) {{
                    window.mtcaptcha.setToken('{solution}');
                    console.log('MTCaptcha token set via API');
                }}
                """
                self.driver.execute_script(script)
                logger.info("✅ Solution injectée via API JavaScript")
                injected = True
                
            return injected
            
        except Exception as e:
            logger.error(f"❌ Erreur injection: {str(e)}")
            return False

    def submit_form(self) -> bool:
        """Soumet le formulaire"""
        logger.info("📨 Soumission du formulaire...")
        
        try:
            # D'abord inspectons tous les boutons et inputs
            logger.info("🔍 Recherche de tous les boutons et inputs submit...")
            
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
            
            for i, btn in enumerate(all_buttons):
                text = btn.text
                onclick = btn.get_attribute('onclick')
                id_attr = btn.get_attribute('id')
                class_attr = btn.get_attribute('class')
                logger.info(f"Button #{i}: text='{text}', id='{id_attr}', class='{class_attr}', onclick='{onclick}'")
                
            for i, inp in enumerate(all_inputs):
                value = inp.get_attribute('value')
                onclick = inp.get_attribute('onclick')
                id_attr = inp.get_attribute('id')
                name = inp.get_attribute('name')
                logger.info(f"Input #{i}: value='{value}', id='{id_attr}', name='{name}', onclick='{onclick}'")
            
            # Recherche spécifique du bouton de vote
            submit_selectors = [
                "#voteBtn",
                "button:contains('Je vote maintenant')",
                "button:contains('vote')",
                "input[value*='Je vote maintenant']",
                "input[value*='vote' i]",
                "button[onclick*='vote']",
                "input[onclick*='vote']",
                "*[onclick*='vote']",
                "input[type='submit']",
                "button[type='submit']"
            ]
            
            for selector in submit_selectors:
                try:
                    # Gérer les sélecteurs CSS spéciaux
                    if ":contains(" in selector:
                        # Pour les sélecteurs contains, utiliser XPath
                        text_to_find = selector.split("'")[1]
                        xpath = f"//button[contains(text(), '{text_to_find}')]"
                        submit_btn = self.driver.find_element(By.XPATH, xpath)
                    else:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Vérifier que l'élément est visible et cliquable
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        text = submit_btn.text or submit_btn.get_attribute('value')
                        logger.info(f"🎯 Bouton trouvé: '{text}' via {selector}")
                        
                        # Scroller vers l'élément
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                        time.sleep(2)
                        
                        # Tentative de clic
                        try:
                            submit_btn.click()
                            logger.info(f"✅ Clic réussi sur: '{text}' via {selector}")
                            return True
                        except Exception as click_error:
                            logger.warning(f"⚠️  Clic normal échoué: {click_error}")
                            # Fallback JavaScript
                            try:
                                self.driver.execute_script("arguments[0].click();", submit_btn)
                                logger.info(f"✅ Clic JS réussi sur: '{text}' via {selector}")
                                return True
                            except Exception as js_error:
                                logger.warning(f"⚠️  Clic JS échoué: {js_error}")
                                continue
                    else:
                        logger.warning(f"⚠️  Élément non cliquable: {selector}")
                        
                except NoSuchElementException:
                    continue
                except Exception as e:
                    logger.warning(f"⚠️  Erreur avec {selector}: {e}")
                    continue
                    
            # Fallback final avec JavaScript
            logger.info("🔄 Tentative de soumission JavaScript fallback...")
            success = self.driver.execute_script("""
                // Chercher le bouton "Je vote maintenant"
                var buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"]');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var text = btn.textContent || btn.value || '';
                    if (text.toLowerCase().includes('vote') || text.toLowerCase().includes('voter')) {
                        console.log('Bouton trouvé via JS:', text);
                        btn.click();
                        return true;
                    }
                }
                
                // Fallback: bouton avec ID voteBtn
                if (document.getElementById('voteBtn')) {
                    document.getElementById('voteBtn').click();
                    return true;
                }
                
                // Dernier recours: soumettre le premier formulaire
                if (document.forms.length > 0) {
                    document.forms[0].submit();
                    return true;
                }
                
                return false;
            """)
            
            if success:
                logger.info("✅ Soumission JavaScript fallback réussie")
                return True
            else:
                logger.error("❌ Aucune méthode de soumission n'a fonctionné")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erreur soumission: {str(e)}")
            return False

    def check_result(self) -> str:
        """Vérifie le résultat de la soumission"""
        logger.info("🔍 Vérification du résultat...")
        
        try:
            time.sleep(5)
            
            page_text = self.driver.page_source.lower()
            current_url = self.driver.current_url
            
            # Indicateurs de succès
            success_indicators = [
                "success", "thank you", "merci", "completed", "submitted", "voté"
            ]
            
            for indicator in success_indicators:
                if indicator in page_text:
                    return f"✅ SUCCÈS - Indicateur: '{indicator}'"
                    
            # Vérifier redirection
            if "success" in current_url or "thank" in current_url:
                return "✅ SUCCÈS - Redirection détectée"
                
            # Vérifier erreurs
            error_indicators = [
                "error", "failed", "invalid", "incorrect", "erreur", "échec"
            ]
            
            for indicator in error_indicators:
                if indicator in page_text:
                    return f"❌ ÉCHEC - Erreur: '{indicator}'"
                    
            return "⚠️ INCERTAIN - Résultat non déterminé"
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {str(e)}")
            return f"❌ ERREUR - {str(e)}"

    def run_test(self, url: str) -> bool:
        """Exécute le test complet avec Safari"""
        try:
            self.setup_safari_driver()
            
            # Étape 1: Récupérer la sitekey
            sitekey = self.get_mtcaptcha_sitekey(url)
            if not sitekey:
                return False
                
            # Étape 2: Résoudre le captcha
            solution = self.solve_mtcaptcha(sitekey, url)
            if not solution:
                return False
                
            # Étape 3: Injecter la solution
            if not self.inject_solution(solution):
                return False
                
            # Étape 4: Soumettre le formulaire
            if not self.submit_form():
                return False
                
            # Étape 5: Vérifier le résultat
            result = self.check_result()
            logger.info(f"🏁 Résultat final: {result}")
            
            return "SUCCÈS" in result
            
        except Exception as e:
            logger.error(f"❌ Erreur générale: {str(e)}")
            return False
            
        finally:
            if self.driver:
                logger.info("🚪 Fermeture de Safari")
                self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Testeur MTCaptcha pour Safari')
    parser.add_argument('--url', default='https://serveur-prive.net/minecraft/oneblockbyrivrs/vote',
                       help='URL de vote')
    
    args = parser.parse_args()
    
    # Charger la configuration
    load_dotenv()
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    
    if not api_key:
        logger.error("❌ Clé API 2Captcha manquante dans .env")
        return
        
    logger.info("🦁 === DÉMARRAGE DU TEST SAFARI MTCAPTCHA ===")
    logger.info(f"🎯 URL cible: {args.url}")
    
    tester = SafariMTCaptchaTester(api_key)
    success = tester.run_test(args.url)
    
    if success:
        logger.info("🎉 === TEST SAFARI TERMINÉ AVEC SUCCÈS ===")
    else:
        logger.info("💥 === TEST SAFARI ÉCHOUÉ ===")

if __name__ == "__main__":
    main()