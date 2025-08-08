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
import json

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MTCaptchaVoterSeleniumBase:
    def __init__(self, headless=True, timeout=120):
        self.timeout = timeout
        self.api_key = os.getenv('TWOCAPTCHA_API_KEY') or os.getenv('api_key')
        self.username = os.getenv('username', 'zCapsLock')
        
        if not self.api_key:
            raise ValueError("❌ API key non trouvée dans .env ! Ajoutez: TWOCAPTCHA_API_KEY=votre_clé")
        
        # Configuration SeleniumBase
        if headless:
            # Configuration spéciale pour headless
            self.sb_options = {
                'uc': False,  # Désactiver UC en headless
                'headless2': True,  # Utiliser le nouveau mode headless de Chrome
                'disable_csp': True,
                'disable_ws': True,
                'page_load_strategy': 'normal',  # Mode normal en headless
                'block_images': False,
                'chromium_arg': '--disable-blink-features=AutomationControlled,--no-sandbox,--disable-dev-shm-usage',
            }
            
            # Sur Linux uniquement, utiliser xvfb
            if sys.platform.startswith('linux'):
                self.sb_options['xvfb'] = True
                logger.info("🖥️ Mode xvfb activé pour Linux headless")
        else:
            # Configuration normale avec UC
            self.sb_options = {
                'uc': True,
                'headless': False,
                'disable_csp': True,
                'disable_ws': True,
                'page_load_strategy': 'eager',
                'block_images': False,
            }
        
        logger.info("🔧 Configuration SeleniumBase avec UC mode...")
    
    def vote_oneblock_site1(self, url=None):
        """Vote pour le SITE N°1 sur oneblock.fr avec requête AJAX"""
        
        if not url:
            url = "https://oneblock.fr/vote"
        
        try:
            with SB(**self.sb_options) as sb:
                logger.info("✅ Driver SeleniumBase UC configuré")
                
                logger.info(f"🌐 Étape 1: Accès à {url}")
                # En headless ou sans UC, utiliser open normal
                if self.sb_options.get('headless2') or not self.sb_options.get('uc'):
                    sb.open(url)
                    time.sleep(3)  # Attendre le chargement
                else:
                    sb.uc_open_with_reconnect(url, reconnect_time=4)
                sb.wait_for_element_visible("body", timeout=10)
                
                # Gérer les cookies
                try:
                    if sb.is_element_visible("button:contains('J'accepte')"):
                        sb.click("button:contains('J'accepte')")
                        logger.info("✅ Cookies acceptés")
                        time.sleep(2)
                except:
                    pass
                
                # Remplir le pseudonyme
                username_selectors = [
                    "input[placeholder*='pseudo' i]",
                    "input[name*='username' i]", 
                    "input[type='text']"
                ]
                
                for selector in username_selectors:
                    if sb.is_element_present(selector):
                        sb.clear(selector)
                        sb.type(selector, self.username)
                        logger.info(f"✅ Pseudonyme '{self.username}' saisi")
                        break
                
                # Cliquer sur ENVOYER
                buttons = sb.find_elements("button")
                for btn in buttons:
                    if "ENVOYER" in btn.text.upper() and btn.is_displayed():
                        try:
                            # Essayer un clic normal d'abord
                            btn.click()
                            logger.info("✅ Clic sur bouton 'ENVOYER'")
                        except:
                            # Si ça échoue, utiliser JavaScript sans scroll
                            try:
                                sb.execute_script("arguments[0].click();", btn)
                                logger.info("✅ Clic sur bouton 'ENVOYER' (JS)")
                            except:
                                logger.warning("⚠️ Impossible de cliquer sur ENVOYER")
                        time.sleep(5)
                        break
                
                # Chercher et cliquer sur SITE N°1
                logger.info("🔍 Recherche du bouton SITE N°1...")
                time.sleep(3)
                
                site1_clicked = False
                buttons = sb.find_elements("button")
                
                for button in buttons:
                    text = button.text.strip()
                    if "SITE N°1" in text:
                        # Vérifier si on est en cooldown (format: "SITE N°1\n00h 00min 00s")
                        button_text_lower = text.lower()
                        # Détecter le format de temps comme "01h 18min 35s"
                        import re
                        time_pattern = r'\d+h\s*\d+min\s*\d+s'
                        if (re.search(time_pattern, text) or 
                            "cooldown" in button_text_lower or 
                            "attendre" in button_text_lower or 
                            "wait" in button_text_lower or 
                            "prochain" in button_text_lower):
                            logger.info(f"⏰ COOLDOWN DÉTECTÉ: {text.replace(chr(10), ' ')}")
                            logger.info("✅ Le vote précédent a bien fonctionné! Cooldown actif.")
                            return True  # Succès car cooldown = vote passé
                        
                        initial_tabs = len(sb.driver.window_handles)
                        current_handle = sb.driver.current_window_handle
                        
                        # Clic simple sans scroll en headless
                        try:
                            button.click()
                            logger.info("✅ Clic sur SITE N°1")
                        except:
                            try:
                                sb.driver.execute_script("arguments[0].click();", button)
                                logger.info("✅ Clic sur SITE N°1 (JS)")
                            except Exception as e:
                                logger.warning(f"⚠️ Erreur clic SITE N°1: {e}")
                        site1_clicked = True
                        
                        time.sleep(3)
                        
                        # Gérer le nouvel onglet ou redirection
                        if len(sb.driver.window_handles) > initial_tabs:
                            for handle in sb.driver.window_handles:
                                if handle != current_handle:
                                    sb.switch_to_window(handle)
                                    logger.info(f"🔄 Basculé vers nouvel onglet: {sb.get_current_url()}")
                                    vote_success = self.continue_vote_on_serveur_prive(sb)
                                    sb.driver.close()
                                    sb.switch_to_window(current_handle)
                                    return vote_success
                        else:
                            current_url = sb.get_current_url()
                            if "serveur-prive.net" in current_url:
                                logger.info("📍 Redirection vers serveur-prive.net")
                                return self.continue_vote_on_serveur_prive(sb)
                        break
                
                if not site1_clicked:
                    # Vérifier si c'est parce qu'on est en cooldown
                    page_text = sb.get_text("body").lower()
                    if "cooldown" in page_text or "attendre" in page_text or "déjà voté" in page_text:
                        logger.info("⏰ COOLDOWN DÉTECTÉ sur la page")
                        logger.info("✅ Le vote précédent a bien fonctionné! Cooldown actif.")
                        return True
                    
                    logger.error("❌ Bouton SITE N°1 non trouvé")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Erreur générale: {str(e)}")
            return False
    
    def continue_vote_on_serveur_prive(self, sb):
        """Continue le vote sur serveur-prive.net avec requête AJAX"""
        
        try:
            current_url = sb.get_current_url()
            logger.info(f"📍 Page de vote: {current_url}")
            
            # Gérer Cloudflare
            logger.info("⏳ Gestion de Cloudflare...")
            time.sleep(3)
            
            page_source = sb.get_page_source().lower()
            if "just a moment" in page_source or "checking your browser" in page_source:
                logger.info("🛡️ Défi Cloudflare détecté")
                
                try:
                    if sb.is_element_present("iframe[src*='challenges.cloudflare.com']"):
                        sb.uc_gui_click_captcha()
                        time.sleep(5)
                except:
                    pass
                
                # Attendre que Cloudflare passe
                for i in range(15):
                    if "just a moment" not in sb.get_title().lower():
                        logger.info("✅ Cloudflare passé!")
                        break
                    time.sleep(2)
            
            # Rechercher la sitekey MTCaptcha
            logger.info("🔍 Recherche du MTCaptcha...")
            sitekey = None
            page_source = sb.get_page_source()
            
            # Chercher la sitekey
            matches = re.findall(r'(MTPublic-[a-zA-Z0-9]+)', page_source)
            if matches:
                sitekey = matches[0]
                logger.info(f"✅ Sitekey trouvée: {sitekey}")
            else:
                logger.error("❌ Sitekey non trouvée")
                return False
            
            # Remplir le username
            try:
                for selector in ["input[name*='username']", "input[id*='username']"]:
                    if sb.is_element_present(selector) and sb.is_element_visible(selector):
                        sb.clear(selector)
                        sb.type(selector, self.username)
                        logger.info(f"✅ Username saisi: {self.username}")
                        break
            except:
                pass
            
            # Résoudre le MTCaptcha
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
            
            # Attendre la résolution
            solution = None
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
            
            if not solution:
                logger.error("❌ Timeout résolution captcha")
                return False
            
            # NOUVELLE MÉTHODE: Soumettre via AJAX
            logger.info("💉 Soumission AJAX du vote...")
            
            # Récupérer les cookies et headers nécessaires
            cookies = sb.driver.get_cookies()
            cookie_string = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
            
            # Récupérer le token CSRF si présent
            csrf_token = sb.execute_script("""
                var meta = document.querySelector('meta[name="csrf-token"]');
                return meta ? meta.content : null;
            """)
            
            # Construire et exécuter la requête AJAX
            ajax_result = sb.execute_script(f"""
                return new Promise((resolve) => {{
                    // Créer les données du formulaire
                    var formData = new FormData();
                    formData.append('username', '{self.username}');
                    formData.append('mtcaptcha-verifiedtoken', '{solution}');
                    
                    // Ajouter le CSRF token si présent
                    var csrfToken = document.querySelector('meta[name="csrf-token"]');
                    if (csrfToken) {{
                        formData.append('_token', csrfToken.content);
                    }}
                    
                    // Faire la requête AJAX
                    fetch('https://serveur-prive.net/minecraft/oneblockbyrivrs/vote/subscribe/ajax', {{
                        method: 'POST',
                        body: formData,
                        credentials: 'same-origin',
                        headers: {{
                            'X-Requested-With': 'XMLHttpRequest'
                        }}
                    }})
                    .then(response => response.text())
                    .then(data => {{
                        console.log('Réponse:', data);
                        resolve({{success: true, data: data}});
                    }})
                    .catch(error => {{
                        console.error('Erreur:', error);
                        resolve({{success: false, error: error.toString()}});
                    }});
                }});
            """)
            
            if ajax_result and ajax_result.get('success'):
                logger.info("✅ Requête AJAX envoyée avec succès")
                response_data = ajax_result.get('data', '')
                
                # Analyser la réponse
                if 'success' in response_data.lower() or 'merci' in response_data.lower():
                    logger.info("🎉 Vote confirmé par le serveur!")
                    
                    # Vérifier sur oneblock.fr
                    logger.info("🔄 Vérification du cooldown sur oneblock.fr...")
                    sb.open("https://oneblock.fr/vote")
                    time.sleep(3)
                    
                    # Réessayer avec le username
                    try:
                        sb.type("input[placeholder*='pseudo' i]", self.username)
                        buttons = sb.find_elements("button")
                        for btn in buttons:
                            if "ENVOYER" in btn.text.upper():
                                sb.execute_script("arguments[0].click();", btn)
                                break
                        time.sleep(3)
                    except:
                        pass
                    
                    # Vérifier le cooldown
                    page_text = sb.get_text("body").lower()
                    if "cooldown" in page_text or "attendre" in page_text or "wait" in page_text:
                        logger.info("🎉 SUCCÈS CONFIRMÉ! Cooldown détecté!")
                        return True
                    else:
                        logger.warning("⚠️ Vote envoyé mais cooldown non visible")
                        return True
                else:
                    logger.warning(f"❓ Réponse incertaine: {response_data[:200]}")
                    return False
            else:
                logger.error(f"❌ Échec requête AJAX: {ajax_result}")
                
                # Fallback: essayer le submit normal
                logger.info("⚠️ Fallback au submit standard...")
                sb.execute_script(f"""
                    var input = document.querySelector('input[name="mtcaptcha-verifiedtoken"]');
                    if (!input) {{
                        input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = 'mtcaptcha-verifiedtoken';
                        document.forms[0].appendChild(input);
                    }}
                    input.value = '{solution}';
                    document.forms[0].submit();
                """)
                
                time.sleep(5)
                return self.check_vote_result(sb)
                
        except Exception as e:
            logger.error(f"❌ Erreur vote serveur-prive: {str(e)}")
            return False
    
    def check_vote_result(self, sb):
        """Vérifie le résultat du vote"""
        try:
            page_text = sb.get_text("body").lower()
            current_url = sb.get_current_url()
            
            logger.info(f"📍 URL après vote: {current_url}")
            
            success_keywords = ["succès", "success", "merci", "thank you", "vote validé"]
            error_keywords = ["erreur", "error", "déjà voté", "already voted"]
            
            for keyword in success_keywords:
                if keyword in page_text:
                    logger.info(f"🎉 Vote réussi! ('{keyword}' trouvé)")
                    return True
            
            for keyword in error_keywords:
                if keyword in page_text:
                    logger.warning(f"❌ Vote échoué: '{keyword}' trouvé")
                    return False
            
            if "oneblock.fr" in current_url:
                logger.info("✅ Redirection vers oneblock.fr - vote probablement réussi")
                return True
            
            logger.info("❓ Résultat incertain")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Script de vote avec requête AJAX')
    parser.add_argument('--headless', action='store_true', default=True, help='Mode headless')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout en secondes')
    
    args = parser.parse_args()
    
    logger.info("=== 🚀 DÉMARRAGE DU VOTE AVEC AJAX ===")
    logger.info(f"Mode headless: {args.headless}")
    
    try:
        voter = MTCaptchaVoterSeleniumBase(headless=args.headless, timeout=args.timeout)
        success = voter.vote_oneblock_site1()
        
        if success:
            logger.info("🎉 Résultat final: ✅ SUCCÈS")
            exit(0)
        else:
            logger.info("❌ Résultat final: ❌ ÉCHEC")
            exit(1)
            
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()