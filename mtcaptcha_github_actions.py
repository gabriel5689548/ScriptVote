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

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MTCaptchaVoter:
    def __init__(self, headless=True, timeout=120):
        self.timeout = timeout
        # Compatible avec les deux formats d'API key
        self.api_key = os.getenv('api_key') or os.getenv('TWOCAPTCHA_API_KEY')
        self.username = os.getenv('username', 'zCapsLock')  # Par défaut zCapsLock
        
        if not self.api_key:
            raise ValueError("❌ API key non trouvée dans .env ! Ajoutez: api_key=votre_clé ou TWOCAPTCHA_API_KEY=votre_clé")
        
        # Configuration Chrome pour GitHub Actions avec contournement Cloudflare
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Toujours headless sur GitHub Actions
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        # Garder JavaScript activé pour Cloudflare
        # chrome_options.add_argument("--disable-javascript")  # Commenté pour Cloudflare
        
        # User agent plus réaliste pour éviter la détection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
        
        # Options pour contourner la détection de bot
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Headers plus réalistes
        chrome_options.add_argument("--accept-lang=fr-FR,fr;q=0.9,en;q=0.8")
        chrome_options.add_argument("--accept-encoding=gzip, deflate, br")
        chrome_options.add_argument("--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
        
        logger.info("🔧 Configuration du driver Selenium pour GitHub Actions...")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Masquer les propriétés WebDriver pour éviter la détection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Driver Selenium configuré avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur configuration driver: {e}")
            raise
    
    def vote_oneblock_site1(self):
        """Vote pour le SITE N°1 sur oneblock.fr - Version GitHub Actions"""
        
        try:
            logger.info("🎯 Démarrage du processus de vote sur oneblock.fr")
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
                logger.info(f"✅ Pseudonyme '{self.username}' saisi dans oneblock.fr")
            except Exception as e:
                logger.warning(f"⚠️ Erreur remplissage pseudo oneblock.fr: {str(e)}")
            
            # Étape 3: Cliquer sur ENVOYER
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
            
            # Étape 4: Chercher et cliquer sur le bouton SITE N°1
            logger.info("🔍 Recherche et clic direct sur bouton SITE N°1...")
            
            # Attendre un peu plus pour que la page se charge complètement
            time.sleep(3)
            
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            site1_button = None
            
            logger.info(f"📊 Nombre de boutons trouvés: {len(all_buttons)}")
            
            # Debug: afficher tous les boutons trouvés
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
            
            # Si pas trouvé avec "Votez maintenant", chercher juste "SITE N°1"
            if not site1_button:
                logger.info("🔍 Recherche élargie sans 'Votez maintenant'...")
                for btn in all_buttons:
                    try:
                        text = btn.text.strip()
                        if "SITE N°1" in text and btn.is_displayed():
                            site1_button = btn
                            logger.info(f"🎯 Bouton SITE N°1 trouvé (état: '{text}')")
                            break
                    except Exception:
                        continue
            
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
                                # Procéder au vote sur cette nouvelle page
                                vote_result = self.continue_vote_on_any_page()
                                # Fermer l'onglet et revenir à l'original
                                self.driver.close()
                                self.driver.switch_to.window(original_tab)
                                logger.info("🔄 Retour à l'onglet oneblock.fr")
                                
                                # Si le vote a réussi sur serveur-prive.net, on considère que c'est un succès
                                if vote_result:
                                    logger.info("🎉 Vote confirmé sur serveur-prive.net!")
                                    
                                    # Essayer de rafraîchir la page oneblock.fr pour forcer la synchronisation
                                    logger.info("🔄 Rafraîchissement de oneblock.fr pour synchronisation...")
                                    self.driver.refresh()
                                    time.sleep(5)
                                    
                                    # Rechercher à nouveau le bouton Site N°1 après rafraîchissement
                                    try:
                                        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                                        refreshed_site1_button = None
                                        
                                        for btn in all_buttons:
                                            text = btn.text.strip()
                                            if "SITE N°1" in text and btn.is_displayed():
                                                refreshed_site1_button = btn
                                                logger.info(f"🔍 Bouton Site N°1 après rafraîchissement: '{text}'")
                                                break
                                        
                                        if refreshed_site1_button:
                                            cooldown_confirmed = self.check_cooldown_on_oneblock(refreshed_site1_button)
                                        else:
                                            logger.warning("⚠️ Bouton Site N°1 non trouvé après rafraîchissement")
                                            cooldown_confirmed = False
                                            
                                    except Exception as e:
                                        logger.warning(f"⚠️ Erreur lors du rafraîchissement: {e}")
                                        cooldown_confirmed = False
                                    
                                    if cooldown_confirmed:
                                        logger.info("✅ Cooldown confirmé sur oneblock.fr après rafraîchissement")
                                    else:
                                        logger.info("ℹ️ Cooldown non visible sur oneblock.fr mais vote validé sur serveur-prive.net")
                                    
                                    # Dans tous les cas, considérer comme succès si validé sur serveur-prive.net
                                    return True
                                else:
                                    logger.warning("⚠️ Vote échoué sur serveur-prive.net")
                                    return False
                        break
                    
                    # Si pas de nouvel onglet, vérifier si le bouton change d'état
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
                
                if not new_tab_opened:
                    logger.warning("⚠️ Aucun nouvel onglet détecté après 10s")
            else:
                logger.warning("⚠️ Bouton SITE N°1 'Votez maintenant' non trouvé")
            
            # Si aucun nouvel onglet ne s'ouvre, le vote a peut-être échoué
            logger.warning("⚠️ Aucun nouvel onglet détecté, vote probablement échoué")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur dans vote_oneblock_site1: {str(e)}")
            return False
    
    def continue_vote_on_any_page(self):
        """Continue le processus de vote sur n'importe quelle page de vote"""
        
        try:
            current_url = self.driver.current_url
            logger.info(f"📍 Page de vote détectée: {current_url}")
            
            logger.info("🌐 Recherche du MTCaptcha sur la page de vote...")
            
            # Vérifier et attendre que Cloudflare termine
            cloudflare_attempts = 0
            max_cloudflare_attempts = 12  # 120 secondes max (2 minutes)
            
            while cloudflare_attempts < max_cloudflare_attempts:
                # Délai aléatoire pour éviter la détection de patterns
                import random
                delay = random.randint(8, 15)
                time.sleep(delay)
                
                current_url = self.driver.current_url
                page_source = self.driver.page_source
                
                logger.info(f"📍 URL après attente #{cloudflare_attempts+1}: {current_url}")
                
                # Vérifier si on est encore sur la page Cloudflare
                if "Just a moment..." in page_source or "_cf_chl_opt" in page_source:
                    logger.info(f"⏳ Cloudflare en cours... Tentative {cloudflare_attempts+1}/{max_cloudflare_attempts} (délai: {delay}s)")
                    cloudflare_attempts += 1
                    continue
                else:
                    logger.info("✅ Cloudflare passé, page chargée")
                    break
            
            if cloudflare_attempts >= max_cloudflare_attempts:
                logger.error("❌ Timeout Cloudflare - impossible d'accéder à la page")
                return False
            
            # Chercher la sitekey MTCaptcha
            sitekey = None
            try:
                # Chercher dans les scripts
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                logger.info(f"📊 Nombre de scripts trouvés: {len(scripts)}")
                
                for i, script in enumerate(scripts):
                    script_text = script.get_attribute('innerHTML') or ''
                    if len(script_text) > 0:
                        logger.info(f"🔍 Script {i+1}: {script_text[:100]}...")
                    
                    if 'MTPublic-' in script_text:
                        import re
                        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', script_text)
                        if matches:
                            sitekey = matches[0]
                            logger.info(f"✅ Sitekey MTCaptcha trouvée dans JS config: {sitekey}")
                            break
                
                if not sitekey:
                    # Chercher dans les attributs data
                    logger.info("🔍 Recherche dans les attributs data...")
                    captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey], [data-site-key]")
                    logger.info(f"📊 Éléments avec data-sitekey trouvés: {len(captcha_elements)}")
                    
                    for elem in captcha_elements:
                        potential_key = elem.get_attribute('data-sitekey') or elem.get_attribute('data-site-key')
                        logger.info(f"🔍 Sitekey potentielle: {potential_key}")
                        if potential_key and 'MTPublic-' in potential_key:
                            sitekey = potential_key
                            logger.info(f"✅ Sitekey MTCaptcha trouvée dans attribut: {sitekey}")
                            break
                
                if not sitekey:
                    # Debug: afficher le HTML de la page pour comprendre
                    logger.info("🔍 Debug: Contenu de la page...")
                    page_source = self.driver.page_source
                    if 'MTPublic-' in page_source:
                        logger.info("✅ MTPublic- trouvé dans le HTML")
                        import re
                        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', page_source)
                        if matches:
                            sitekey = matches[0]
                            logger.info(f"✅ Sitekey MTCaptcha trouvée dans HTML: {sitekey}")
                        else:
                            logger.warning("⚠️ MTPublic- trouvé mais pas de match regex")
                    else:
                        logger.warning("⚠️ MTPublic- non trouvé dans le HTML")
                        # Afficher les premiers 1000 caractères pour debug
                        logger.info(f"🔍 Début du HTML: {page_source[:1000]}")
                
                if not sitekey:
                    logger.error("❌ Sitekey MTCaptcha non trouvée après toutes les tentatives")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erreur recherche sitekey: {str(e)}")
                return False
            
            # Remplir le pseudonyme si nécessaire
            logger.info("🔍 Vérification si pseudonyme doit être rempli...")
            try:
                username_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[id*='username'], input[placeholder*='pseudo']")
                for field in username_fields:
                    if field.is_displayed():
                        current_value = field.get_attribute('value')
                        if not current_value or current_value.strip() == '':
                            field.clear()
                            field.send_keys(self.username)
                            logger.info(f"✅ Pseudonyme '{self.username}' saisi dans: {field.get_attribute('name') or field.get_attribute('id')}")
                        break
                else:
                    logger.info("ℹ️ Aucun champ pseudonyme trouvé ou accessible")
            except Exception as e:
                logger.warning(f"⚠️ Erreur avec champ username: {e}")
                try:
                    # Essayer avec JavaScript
                    self.driver.execute_script(f"document.querySelector('input[name*=\"username\"], input[id*=\"username\"]').value = '{self.username}';")
                    logger.info(f"✅ Pseudonyme '{self.username}' saisi via JavaScript")
                except Exception as e2:
                    logger.warning(f"⚠️ Erreur JavaScript username: {e2}")
            
            # Résoudre le MTCaptcha avec 2Captcha
            logger.info("📤 Envoi de la demande de résolution à 2Captcha...")
            try:
                page_url = self.driver.current_url
                submit_data = {
                    'key': self.api_key,
                    'method': 'mt_captcha',
                    'sitekey': sitekey,
                    'pageurl': page_url,
                    'json': 1
                }
                
                logger.info(f"📊 Données envoyées à 2Captcha: sitekey={sitekey}, pageurl={page_url}")
                
                response = requests.post('http://2captcha.com/in.php', data=submit_data, timeout=30)
                
                # Vérifier que la réponse est valide
                if response.status_code != 200:
                    logger.error(f"❌ Erreur HTTP 2Captcha: {response.status_code}")
                    return False
                
                try:
                    result = response.json()
                except ValueError as e:
                    logger.error(f"❌ Réponse 2Captcha invalide (pas JSON): {response.text}")
                    return False
                
                logger.info(f"📊 Réponse 2Captcha: {result}")
                
                if result.get('status') != 1:
                    error_msg = result.get('request', 'Erreur inconnue')
                    logger.error(f"❌ Erreur soumission 2Captcha: {error_msg}")
                    return False
                
                captcha_id = result['request']
                logger.info(f"🎯 Captcha soumis avec l'ID: {captcha_id}")
                
                # Attendre la résolution
                solution = None
                for attempt in range(30):
                    time.sleep(10)
                    
                    try:
                        check_response = requests.get(f'http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}&json=1', timeout=30)
                        
                        if check_response.status_code != 200:
                            logger.warning(f"⚠️ Erreur HTTP lors de la vérification: {check_response.status_code}")
                            continue
                        
                        try:
                            check_result = check_response.json()
                        except ValueError:
                            logger.warning(f"⚠️ Réponse non-JSON: {check_response.text}")
                            continue
                        
                        logger.info(f"📊 Vérification captcha #{attempt+1}: {check_result}")
                        
                        if check_result.get('status') == 1:
                            solution = check_result.get('request')
                            if solution:
                                logger.info("🎉 MTCaptcha résolu avec succès!")
                                break
                            else:
                                logger.warning("⚠️ Solution vide reçue")
                                continue
                        elif check_result.get('error') == 'CAPCHA_NOT_READY':
                            logger.info(f"⏳ Captcha en cours de résolution... (tentative {attempt+1}/30)")
                            continue
                        elif check_result.get('status') == 0 and check_result.get('error'):
                            logger.error(f"❌ Erreur résolution captcha: {check_result['error']}")
                            return False
                        else:
                            logger.warning(f"⚠️ Réponse inattendue: {check_result}")
                            continue
                            
                    except requests.RequestException as e:
                        logger.warning(f"⚠️ Erreur réseau lors de la vérification #{attempt+1}: {e}")
                        continue
                else:
                    logger.error("❌ Timeout résolution captcha (5 minutes)")
                    return False
                
                if not solution:
                    logger.error("❌ Aucune solution reçue")
                    return False
                
                # Injecter la solution
                logger.info("💉 Injection de la solution dans la page...")
                
                # Injecter dans le champ MTCaptcha
                try:
                    self.driver.execute_script(f"document.querySelector('input[name=\"mtcaptcha-verifiedtoken\"]').value = '{solution}';")
                    logger.info("✅ Solution injectée dans: input[name='mtcaptcha-verifiedtoken']")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur injection solution: {e}")
                
                # Soumettre le formulaire
                logger.info("📤 Soumission du formulaire...")
                
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
                                    logger.info(f"✅ Formulaire soumis via clic: {selector}")
                                    form_submitted = True
                                    break
                                except:
                                    try:
                                        self.driver.execute_script("arguments[0].click();", element)
                                        logger.info(f"✅ Formulaire soumis via JavaScript: {selector}")
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
                        logger.info("✅ Formulaire soumis via JavaScript générique")
                        form_submitted = True
                    except Exception as e:
                        logger.error(f"❌ Erreur soumission formulaire: {e}")
                        return False
                
                # Vérifier le résultat
                logger.info("🔍 Vérification du résultat...")
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
                        logger.info(f"🎉 Message de succès trouvé: '{success_msg}'")
                        return True
                
                for pattern in error_patterns:
                    if pattern in visible_text:
                        error_msg = [line.strip() for line in visible_text.split('\n') if pattern in line][0]
                        logger.info(f"❌ Message d'erreur trouvé: '{error_msg}'")
                        return False
                
                # Si pas de message clair, considérer comme succès par défaut
                logger.info("✅ Vote probablement réussi (aucun message d'erreur détecté)")
                return True
                    
            except Exception as e:
                logger.error(f"❌ Erreur traitement MTCaptcha: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur générale: {str(e)}")
            return False
    
    def check_cooldown_on_oneblock(self, site1_button):
        """Vérifie le cooldown sur oneblock.fr après le vote"""
        
        try:
            logger.info("🔍 Vérification du cooldown sur oneblock.fr...")
            
            # Attendre que la page se mette à jour
            time.sleep(5)
            
            # Vérifier l'état du bouton Site N°1
            for wait_time in range(1, 21):
                try:
                    button_text = site1_button.text.strip()
                    logger.info(f"📊 État du bouton Site N°1: '{button_text}'")
                    
                    # Détecter les messages de cooldown
                    if "min" in button_text and "s" in button_text:
                        logger.info(f"🎉 VOTE RÉUSSI! Cooldown détecté: '{button_text}'")
                        return True
                    elif "prochain vote" in button_text.lower():
                        logger.info(f"🎉 VOTE RÉUSSI! Cooldown détecté: '{button_text}'")
                        return True
                    elif "h" in button_text and "min" in button_text:
                        logger.info(f"🎉 VOTE RÉUSSI! Cooldown détecté: '{button_text}'")
                        return True  
                    elif "Veuillez patienter" in button_text:
                        logger.info(f"⏳ Mise à jour en cours... '{button_text}' (attendre {21-wait_time}s)")
                    elif "Votez maintenant" in button_text:
                        logger.info(f"⚠️ Bouton encore actif: '{button_text}'")
                    else:
                        logger.info(f"📊 État bouton: '{button_text}'")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur lecture bouton: {e}")
                
                time.sleep(1)
            
            # Vérifier dans le texte de la page
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                cooldown_patterns = [
                    "prochain vote", "minutes", "heures", "cooldown", 
                    "déjà voté", "already voted", "vote enregistré"
                ]
                
                for pattern in cooldown_patterns:
                    if pattern in page_text:
                        success_msg = [line.strip() for line in page_text.split('\n') if pattern in line]
                        if success_msg:
                            logger.info(f"🎉 VOTE RÉUSSI! Message trouvé: '{success_msg[0]}'")
                            return True
                        
            except Exception as e:
                logger.warning(f"⚠️ Erreur lecture page: {e}")
            
            logger.warning("⚠️ Cooldown non détecté clairement")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification cooldown: {str(e)}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Driver fermé")

def main():
    parser = argparse.ArgumentParser(description='Script de vote automatique MTCaptcha pour GitHub Actions')
    parser.add_argument('--headless', action='store_true', default=True, help='Mode headless (défaut: True)')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout en secondes')
    
    args = parser.parse_args()
    
    logger.info("=== 🚀 DÉMARRAGE DU VOTE AUTOMATIQUE GITHUB ACTIONS ===")
    logger.info(f"Mode headless: {args.headless}")
    
    voter = None
    try:
        voter = MTCaptchaVoter(headless=args.headless, timeout=args.timeout)
        
        success = voter.vote_oneblock_site1()
        
        if success:
            logger.info("🎉 Résultat final: ✅ SUCCÈS")
            logger.info("=== ✅ VOTE TERMINÉ AVEC SUCCÈS ===")
            exit(0)  # Code de sortie 0 = succès
        else:
            logger.info("❌ Résultat final: ❌ ÉCHEC")
            logger.info("=== ❌ VOTE ÉCHOUÉ ===")
            exit(1)  # Code de sortie 1 = échec
            
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {str(e)}")
        logger.info("=== ❌ VOTE ÉCHOUÉ ===")
        exit(1)
    finally:
        if voter:
            voter.close()

if __name__ == "__main__":
    main()