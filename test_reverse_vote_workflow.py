#!/usr/bin/env python3
"""
Test du workflow inversé selon l'idée de l'utilisateur :
1. D'abord voter sur https://serveur-prive.net/minecraft/oneblockbyrivrs/vote
2. Puis aller sur oneblock.fr pour voir si ça détecte qu'on a déjà voté
"""

import os
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReverseWorkflowTester:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.driver = None
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def solve_mtcaptcha(self, sitekey: str, page_url: str):
        """Résout le MTCaptcha via l'API 2Captcha"""
        logger.info("Envoi de la demande de résolution à 2Captcha...")
        
        # Étape 1: Soumission
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
                logger.error(f"Erreur soumission: {result}")
                return None
                
            captcha_id = result['request']
            logger.info(f"Captcha soumis avec l'ID: {captcha_id}")
            
        except Exception as e:
            logger.error(f"Erreur soumission: {str(e)}")
            return None

        # Étape 2: Récupération de la solution
        get_url = "http://2captcha.com/res.php"
        start_time = time.time()
        
        while time.time() - start_time < 300:  # 5 minutes max
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
                    logger.info("MTCaptcha résolu avec succès!")
                    return result['request']
                elif result['request'] == 'CAPCHA_NOT_READY':
                    logger.info("Captcha en cours de résolution...")
                    continue
                else:
                    logger.error(f"Erreur résolution: {result}")
                    return None
                    
            except Exception as e:
                logger.error(f"Erreur récupération: {str(e)}")
                continue
                
        logger.error("Timeout résolution captcha")
        return None
    
    def test_reverse_workflow(self):
        """Test du workflow inversé"""
        try:
            self.setup_driver()
            
            logger.info("🧪 === TEST WORKFLOW INVERSÉ ===")
            
            # ÉTAPE 1: Voter directement sur le site
            vote_url = "https://serveur-prive.net/minecraft/oneblockbyrivrs/vote"
            logger.info(f"🌐 Étape 1: Vote direct sur {vote_url}")
            
            self.driver.get(vote_url)
            time.sleep(5)
            
            current_url = self.driver.current_url
            logger.info(f"URL atteinte: {current_url}")
            
            # Chercher la sitekey MTCaptcha
            page_source = self.driver.page_source
            sitekey = None
            
            if 'MTPublic-' in page_source:
                import re
                sitekey_match = re.search(r'MTPublic-[a-zA-Z0-9]+', page_source)
                if sitekey_match:
                    sitekey = sitekey_match.group(0)
                    logger.info(f"✅ Sitekey trouvée: {sitekey}")
            
            # Chercher et remplir le champ username
            username_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[name='username'], input[name='pseudo'], input[placeholder*='pseudo' i]")
            
            if username_fields:
                for field in username_fields:
                    if field.is_displayed() and field.is_enabled():
                        field.clear()
                        field.send_keys("zCapsLock")
                        logger.info("✅ Pseudonyme 'zCapsLock' saisi")
                        break
            else:
                logger.warning("⚠️ Aucun champ username trouvé")
            
            # Résoudre le captcha si trouvé
            if sitekey:
                solution = self.solve_mtcaptcha(sitekey, vote_url)
                
                if solution:
                    # Injecter la solution
                    logger.info("Injection de la solution...")
                    
                    # Chercher les champs de réponse MTCaptcha
                    selectors = [
                        "input[name='mtcaptcha-verifiedtoken']",
                        "textarea[name='mtcaptcha-verifiedtoken']",
                        "input[name='mt_token']",
                        "#mtcaptcha-verifiedtoken"
                    ]
                    
                    injected = False
                    for selector in selectors:
                        try:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            self.driver.execute_script(f"arguments[0].value = '{solution}';", element)
                            logger.info(f"Solution injectée dans: {selector}")
                            injected = True
                            break
                        except:
                            continue
                    
                    if not injected:
                        # Tentative via JavaScript MTCaptcha API
                        script = f"""
                        if (window.mtcaptcha) {{
                            window.mtcaptcha.setToken('{solution}');
                        }}
                        """
                        self.driver.execute_script(script)
                        logger.info("Solution injectée via API MTCaptcha")
                    
                    # Soumettre le formulaire
                    logger.info("Soumission du formulaire de vote...")
                    
                    submit_selectors = [
                        "input[type='submit']",
                        "button[type='submit']",
                        "#voteBtn",
                        "button:contains('vote')"
                    ]
                    
                    submitted = False
                    for selector in submit_selectors:
                        try:
                            if selector.startswith('#') or selector.startswith('.'):
                                submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            else:
                                submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                            submit_btn.click()
                            logger.info(f"✅ Formulaire soumis via: {selector}")
                            submitted = True
                            break
                        except:
                            continue
                    
                    if not submitted:
                        # Fallback JavaScript
                        self.driver.execute_script("""
                            if (document.forms.length > 0) {
                                document.forms[0].submit();
                            }
                        """)
                        logger.info("✅ Formulaire soumis via JavaScript")
                    
                    # Attendre le résultat
                    time.sleep(5)
                    
                    # Vérifier le résultat du vote
                    final_page = self.driver.page_source.lower()
                    if any(word in final_page for word in ['success', 'succès', 'thank', 'merci', 'voté']):
                        logger.info("🎉 VOTE RÉUSSI!")
                    elif any(word in final_page for word in ['error', 'erreur', 'failed', 'cooldown']):
                        logger.warning("⚠️ Erreur ou cooldown détecté")
                    else:
                        logger.info("🤷 Résultat du vote incertain")
                
            else:
                logger.error("❌ Pas de sitekey MTCaptcha trouvée")
                return False
            
            # ÉTAPE 2: Tester la détection sur oneblock.fr
            logger.info("\n🌐 Étape 2: Test détection sur oneblock.fr")
            
            self.driver.get("https://oneblock.fr/vote")
            time.sleep(5)
            
            # Remplir le pseudo
            try:
                pseudo_field = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='pseudo' i]")
                pseudo_field.clear()
                pseudo_field.send_keys("zCapsLock")
                logger.info("✅ Pseudo saisi sur oneblock.fr")
                time.sleep(2)
            except:
                logger.warning("⚠️ Erreur saisie pseudo oneblock.fr")
            
            # Cliquer sur ENVOYER
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                envoyer_btn = None
                
                for btn in all_buttons:
                    if 'envoyer' in btn.text.strip().lower() and btn.is_displayed() and btn.is_enabled():
                        envoyer_btn = btn
                        break
                
                if envoyer_btn:
                    try:
                        envoyer_btn.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", envoyer_btn)
                    
                    logger.info("✅ Clic ENVOYER réussi")
                    time.sleep(5)
                    
                    # ANALYSER LES SITES APRÈS ENVOYER
                    logger.info("\n🔍 Analyse des sites de vote:")
                    
                    site_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'SITE N°')]")
                    
                    for i, site_btn in enumerate(site_buttons):
                        text = site_btn.text.strip()
                        classes = site_btn.get_attribute('class') or ''
                        is_disabled = 'grayscale' in classes or 'cursor-not-allowed' in classes
                        
                        logger.info(f"   Site #{i+1}: '{text[:50]}...'")
                        logger.info(f"      Désactivé: {is_disabled}")
                        
                        # VÉRIFIER LES MESSAGES DE STATUT
                        if any(keyword in text.lower() for keyword in ['voté', 'voted', 'cooldown', 'attendre', 'wait']):
                            logger.info(f"   🎉 DÉTECTION DE VOTE PRÉCÉDENT!")
                        elif 'connectez-vous' in text.lower():
                            logger.info(f"   🔐 Connexion requise")
                        elif not is_disabled:
                            logger.info(f"   ✅ Site disponible")
                        else:
                            logger.info(f"   ⚠️ Site désactivé")
                
            except Exception as e:
                logger.error(f"❌ Erreur oneblock.fr: {e}")
            
            logger.info("\n✅ Test du workflow inversé terminé!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur générale: {e}")
            return False
            
        finally:
            if self.driver:
                input("\nAppuyez sur Entrée pour fermer le navigateur...")
                self.driver.quit()

def main():
    load_dotenv()
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    
    if not api_key:
        logger.error("Clé API 2Captcha manquante!")
        return
    
    tester = ReverseWorkflowTester(api_key)
    tester.test_reverse_workflow()

if __name__ == "__main__":
    main()