#!/usr/bin/env python3

import time
import logging
import argparse
import os
import sys
from dotenv import load_dotenv
from seleniumbase import SB
import requests
import re

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MTCaptchaVoterSeleniumBase:
    def __init__(self, headless=True, timeout=120):
        self.timeout = timeout
        self.api_key = os.getenv('api_key') or os.getenv('TWOCAPTCHA_API_KEY')
        self.username = os.getenv('username', 'zCapsLock')
        
        # Configuration proxy (optionnel)
        self.proxy_host = os.getenv('PROXY_HOST')
        self.proxy_port = os.getenv('PROXY_PORT')
        self.proxy_user = os.getenv('PROXY_USER')
        self.proxy_pass = os.getenv('PROXY_PASS')
        
        if not self.api_key:
            raise ValueError("❌ API key non trouvée dans .env ! Ajoutez: api_key=votre_clé ou TWOCAPTCHA_API_KEY=votre_clé")
        
        # Configuration SeleniumBase
        self.sb_options = {
            'uc': True,  # Mode UndetectedChromedriver
            'headless': headless,
            'disable_csp': True,  # Désactive Content Security Policy
            'disable_ws': True,   # Désactive WebSocket
            'page_load_strategy': 'eager',
            'block_images': False,  # Images nécessaires pour MTCaptcha
        }
        
        # Si on est sur Linux (GitHub Actions), utiliser xvfb
        if sys.platform.startswith('linux') and headless:
            self.sb_options['xvfb'] = True
            logger.info("🖥️ Mode xvfb activé pour Linux headless")
        
        # Configuration proxy si disponible
        if self.proxy_host and self.proxy_port:
            if self.proxy_user and self.proxy_pass:
                proxy_string = f"{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}"
            else:
                proxy_string = f"{self.proxy_host}:{self.proxy_port}"
            self.sb_options['proxy'] = proxy_string
            logger.info(f"🌐 Proxy configuré: {self.proxy_host}:{self.proxy_port}")
        
        logger.info("🔧 Configuration SeleniumBase avec UC mode...")
    
    def vote_oneblock_site1(self):
        """Vote pour le SITE N°1 sur oneblock.fr avec SeleniumBase UC mode"""
        
        try:
            with SB(**self.sb_options) as sb:
                logger.info("✅ Driver SeleniumBase UC configuré avec succès")
                
                logger.info("🎯 Démarrage du processus de vote sur oneblock.fr")
                logger.info("🌐 Étape 1: Accès à https://oneblock.fr/vote")
                
                # Utiliser uc_open_with_reconnect pour contourner la détection initiale
                sb.uc_open_with_reconnect("https://oneblock.fr/vote", reconnect_time=4)
                
                # Attendre que la page se charge
                sb.wait_for_element_visible("body", timeout=10)
                
                # Remplir le pseudonyme
                try:
                    # Chercher le champ username
                    username_selectors = [
                        "input[placeholder*='pseudo']",
                        "input[name*='username']", 
                        "input[id*='username']"
                    ]
                    
                    username_field = None
                    for selector in username_selectors:
                        if sb.is_element_present(selector):
                            username_field = selector
                            break
                    
                    if username_field:
                        sb.clear(username_field)
                        sb.type(username_field, self.username)
                        logger.info(f"✅ Pseudonyme '{self.username}' saisi")
                    else:
                        logger.warning("⚠️ Champ username non trouvé")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur remplissage pseudo: {str(e)}")
                
                # Cliquer sur ENVOYER
                try:
                    # Chercher le bouton ENVOYER
                    if sb.is_text_visible("ENVOYER"):
                        sb.click("button:contains('ENVOYER')")
                        logger.info("✅ Clic sur bouton 'ENVOYER'")
                        time.sleep(3)
                except Exception as e:
                    logger.warning(f"⚠️ Erreur clic ENVOYER: {str(e)}")
                
                # Chercher et cliquer sur SITE N°1
                logger.info("🔍 Recherche du bouton SITE N°1...")
                
                try:
                    # Attendre que les boutons de vote apparaissent
                    sb.wait_for_element_visible("button", timeout=10)
                    
                    # Chercher le bouton SITE N°1
                    site1_clicked = False
                    buttons = sb.find_elements("button")
                    
                    for button in buttons:
                        text = button.text.strip()
                        if "SITE N°1" in text and "Votez maintenant" in text:
                            # Mémoriser le nombre d'onglets
                            initial_tabs = len(sb.driver.window_handles)
                            current_handle = sb.driver.current_window_handle
                            
                            # Cliquer sur le bouton
                            sb.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                            time.sleep(1)
                            button.click()
                            logger.info("✅ Clic sur SITE N°1 effectué")
                            site1_clicked = True
                            
                            # Attendre l'ouverture d'un nouvel onglet
                            time.sleep(3)
                            
                            # Vérifier si un nouvel onglet s'est ouvert
                            if len(sb.driver.window_handles) > initial_tabs:
                                # Basculer vers le nouvel onglet
                                for handle in sb.driver.window_handles:
                                    if handle != current_handle:
                                        sb.switch_to_window(handle)
                                        logger.info(f"🔄 Basculé vers nouvel onglet: {sb.get_current_url()}")
                                        
                                        # Continuer le vote sur serveur-prive.net
                                        vote_success = self.continue_vote_on_serveur_prive(sb)
                                        
                                        # Fermer l'onglet et revenir
                                        sb.driver.close()
                                        sb.switch_to_window(current_handle)
                                        
                                        return vote_success
                            else:
                                # Vérifier si on est redirigé sur la même page
                                current_url = sb.get_current_url()
                                if "serveur-prive.net" in current_url:
                                    logger.info("📍 Redirection vers serveur-prive.net détectée")
                                    return self.continue_vote_on_serveur_prive(sb)
                            
                            break
                    
                    if not site1_clicked:
                        logger.error("❌ Bouton SITE N°1 non trouvé")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ Erreur lors du clic SITE N°1: {str(e)}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Erreur générale: {str(e)}")
            return False
    
    def continue_vote_on_serveur_prive(self, sb):
        """Continue le vote sur serveur-prive.net avec gestion Cloudflare"""
        
        try:
            current_url = sb.get_current_url()
            logger.info(f"📍 Page de vote: {current_url}")
            
            # Gérer Cloudflare avec UC mode
            logger.info("⏳ Gestion de Cloudflare avec UC mode...")
            
            # Attendre que Cloudflare se charge
            time.sleep(3)
            
            # Vérifier si on a un défi Cloudflare
            page_title = sb.get_title().lower()
            page_source = sb.get_page_source().lower()
            
            if "just a moment" in page_title or "checking your browser" in page_source:
                logger.info("🛡️ Défi Cloudflare détecté, utilisation de UC mode...")
                
                # Essayer uc_gui_click_captcha si un captcha est présent
                try:
                    if sb.is_element_present("iframe[src*='challenges.cloudflare.com']"):
                        logger.info("🖱️ Tentative de clic sur le captcha Cloudflare...")
                        sb.uc_gui_click_captcha()
                        time.sleep(5)
                except:
                    pass
                
                # Attendre que Cloudflare nous laisse passer
                max_wait = 30
                waited = 0
                while waited < max_wait:
                    current_title = sb.get_title().lower()
                    if "just a moment" not in current_title and "checking" not in current_title:
                        logger.info("✅ Cloudflare passé!")
                        break
                    
                    logger.info(f"⏳ Attente Cloudflare... {waited}/{max_wait}s")
                    time.sleep(2)
                    waited += 2
                
                # Recharger la page avec reconnexion si nécessaire
                if waited >= max_wait:
                    logger.warning("⚠️ Timeout Cloudflare, tentative de reconnexion...")
                    sb.uc_open_with_reconnect(current_url, reconnect_time=6)
                    time.sleep(3)
            
            # Vérifier qu'on est bien sur la page de vote
            current_url = sb.get_current_url()
            if "serveur-prive.net" not in current_url:
                logger.error(f"❌ Pas sur serveur-prive.net: {current_url}")
                return False
            
            logger.info("🔍 Recherche du MTCaptcha...")
            
            # Rechercher la sitekey MTCaptcha
            sitekey = None
            
            # Méthode 1: Dans les scripts
            scripts = sb.find_elements("script")
            for script in scripts:
                script_text = sb.driver.execute_script("return arguments[0].innerHTML;", script) or ''
                if 'MTPublic-' in script_text:
                    matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', script_text)
                    if matches:
                        sitekey = matches[0]
                        logger.info(f"✅ Sitekey trouvée dans script: {sitekey}")
                        break
            
            # Méthode 2: Dans les attributs
            if not sitekey:
                for selector in ["[data-sitekey]", "[data-site-key]"]:
                    if sb.is_element_present(selector):
                        elem = sb.find_element(selector)
                        sitekey = elem.get_attribute('data-sitekey') or elem.get_attribute('data-site-key')
                        if sitekey and 'MTPublic-' in sitekey:
                            logger.info(f"✅ Sitekey trouvée dans attribut: {sitekey}")
                            break
            
            # Méthode 3: Dans les iframes
            if not sitekey:
                iframes = sb.find_elements("iframe")
                for iframe in iframes:
                    src = iframe.get_attribute('src') or ''
                    if 'mtcaptcha' in src.lower():
                        matches = re.findall(r'k=([A-Za-z0-9\-]+)', src)
                        if matches:
                            sitekey = matches[0]
                            logger.info(f"✅ Sitekey trouvée dans iframe: {sitekey}")
                            break
            
            # Méthode 4: Dans la source complète
            if not sitekey:
                page_source = sb.get_page_source()
                # Pattern pour MTPublic-xxx ou UUID
                matches = re.findall(r'(MTPublic-[a-zA-Z0-9]+|[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', page_source)
                if matches:
                    for match in matches:
                        if 'MTPublic' in match or len(match) == 36:
                            sitekey = match
                            logger.info(f"✅ Sitekey trouvée dans source: {sitekey}")
                            break
            
            if not sitekey:
                logger.error("❌ Sitekey MTCaptcha non trouvée")
                # Sauvegarder un screenshot
                try:
                    os.makedirs("screenshots", exist_ok=True)
                    screenshot_path = f"screenshots/no_sitekey_{int(time.time())}.png"
                    sb.save_screenshot(screenshot_path)
                    logger.info(f"📸 Screenshot sauvegardé: {screenshot_path}")
                except:
                    pass
                return False
            
            # Remplir le username si nécessaire
            try:
                username_selectors = [
                    "input[name*='username']",
                    "input[id*='username']",
                    "input[placeholder*='pseudo']"
                ]
                
                for selector in username_selectors:
                    if sb.is_element_present(selector) and sb.is_element_visible(selector):
                        sb.clear(selector)
                        sb.type(selector, self.username)
                        logger.info(f"✅ Pseudonyme saisi: {self.username}")
                        break
            except Exception as e:
                logger.warning(f"⚠️ Erreur saisie username: {e}")
            
            # Résoudre le MTCaptcha avec 2Captcha
            logger.info("📤 Envoi à 2Captcha...")
            
            try:
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
                
                # Attendre la résolution
                for attempt in range(30):
                    time.sleep(10)
                    
                    check_response = requests.get(
                        f'http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}&json=1',
                        timeout=30
                    )
                    check_result = check_response.json()
                    
                    if check_result['status'] == 1:
                        solution = check_result['request']
                        logger.info("🎉 MTCaptcha résolu!")
                        break
                    elif 'error' in check_result and check_result['error'] != 'CAPCHA_NOT_READY':
                        logger.error(f"❌ Erreur: {check_result}")
                        return False
                    else:
                        logger.info(f"⏳ En attente... ({attempt+1}/30)")
                else:
                    logger.error("❌ Timeout résolution captcha")
                    return False
                
                # Injecter la solution
                logger.info("💉 Injection de la solution...")
                
                # Injecter le token
                sb.execute_script(f"""
                    var input = document.querySelector('input[name="mtcaptcha-verifiedtoken"]');
                    if (!input) {{
                        input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = 'mtcaptcha-verifiedtoken';
                        document.forms[0].appendChild(input);
                    }}
                    input.value = '{solution}';
                """)
                
                # Soumettre le formulaire
                logger.info("📤 Soumission du formulaire...")
                
                # Chercher le bouton de vote
                vote_selectors = [
                    "#voteBtn",
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:contains('Vote')",
                    "button:contains('Voter')"
                ]
                
                clicked = False
                for selector in vote_selectors:
                    try:
                        if sb.is_element_present(selector) and sb.is_element_visible(selector):
                            sb.click(selector)
                            logger.info(f"✅ Clic sur: {selector}")
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    # Essayer de soumettre le formulaire directement
                    sb.execute_script("document.forms[0].submit();")
                    logger.info("✅ Formulaire soumis via JS")
                
                # Attendre le résultat
                time.sleep(5)
                
                # Vérifier le succès
                page_text = sb.get_text("body").lower()
                
                success_keywords = ["succès", "success", "merci", "thank you", "vote validé", "vote enregistré"]
                error_keywords = ["erreur", "error", "déjà voté", "already voted", "cooldown"]
                
                for keyword in success_keywords:
                    if keyword in page_text:
                        logger.info(f"🎉 Vote réussi! ('{keyword}' trouvé)")
                        return True
                
                for keyword in error_keywords:
                    if keyword in page_text:
                        logger.warning(f"❌ Vote échoué: '{keyword}' trouvé")
                        return False
                
                # Si pas de message clair, considérer comme succès
                logger.info("✅ Vote probablement réussi")
                return True
                
            except Exception as e:
                logger.error(f"❌ Erreur résolution captcha: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur vote serveur-prive: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Script de vote avec SeleniumBase UC mode')
    parser.add_argument('--headless', action='store_true', default=True, help='Mode headless')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout en secondes')
    
    args = parser.parse_args()
    
    logger.info("=== 🚀 DÉMARRAGE DU VOTE AVEC SELENIUMBASE UC MODE ===")
    logger.info(f"Mode headless: {args.headless}")
    
    try:
        voter = MTCaptchaVoterSeleniumBase(headless=args.headless, timeout=args.timeout)
        
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

if __name__ == "__main__":
    main()