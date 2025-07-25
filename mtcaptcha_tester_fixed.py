#!/usr/bin/env python3

import time
import logging
import argparse
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_cooldown_time(button_text):
    """Parse le temps de cooldown depuis le texte du bouton et retourne le temps en minutes"""
    import re
    
    if not button_text:
        return 0
    
    text = button_text.lower().strip()
    total_minutes = 0
    
    # Rechercher les heures (h, heure, heures)
    hours_match = re.search(r'(\d+)\s*h(?:eure)?s?', text)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60
    
    # Rechercher les minutes (m, min, minute, minutes)
    minutes_match = re.search(r'(\d+)\s*m(?:in)?(?:ute)?s?', text)
    if minutes_match:
        total_minutes += int(minutes_match.group(1))
    
    # Rechercher les secondes (s, sec, seconde, secondes) - convertir en fraction de minute
    seconds_match = re.search(r'(\d+)\s*s(?:ec)?(?:onde)?s?', text)
    if seconds_match:
        total_minutes += int(seconds_match.group(1)) / 60
    
    # Format "HH:MM:SS" ou "MM:SS"
    time_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', text)
    if time_match:
        hours = int(time_match.group(1)) if len(time_match.group(1)) <= 2 else 0
        minutes = int(time_match.group(2))
        seconds = int(time_match.group(3)) if time_match.group(3) else 0
        
        # Si le premier nombre est > 23, c'est probablement des minutes, pas des heures
        if hours > 23:
            total_minutes += hours + (seconds / 60)
        else:
            total_minutes += (hours * 60) + minutes + (seconds / 60)
    
    logger.info(f"📝 Cooldown parsé: '{button_text}' → {total_minutes:.1f} minutes")
    return max(0, total_minutes)

def load_env():
    """Charge les variables d'environnement depuis le fichier .env"""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

class MTCaptchaVoter:
    def __init__(self, timeout=120):
        self.timeout = timeout
        # Charger la clé API depuis .env
        load_env()
        self.api_key = os.getenv('TWOCAPTCHA_API_KEY', '')
        if not self.api_key:
            raise ValueError("Clé API 2Captcha non trouvée dans .env (TWOCAPTCHA_API_KEY)")
        self.username = "zCapsLock"
        
        # Configuration Chrome (mode visible uniquement)
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        logger.info("Configuration du driver Selenium...")
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Driver Selenium configuré avec succès")
    
    def check_initial_cooldown(self):
        """Vérifie l'état initial du cooldown sur OneBlock"""
        
        try:
            logger.info("🔍 Vérification de l'état initial du cooldown...")
            
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
                logger.info(f"✅ Pseudonyme '{self.username}' saisi")
            except Exception as e:
                logger.warning(f"⚠️ Erreur remplissage pseudo: {str(e)}")
            
            # Étape 3: Cliquer sur ENVOYER avec méthodes robustes
            try:
                envoyer_button = None
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                        envoyer_button = btn
                        break
                
                if envoyer_button:
                    # Méthode 1: Scroll et clic normal
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", envoyer_button)
                        time.sleep(2)
                        envoyer_button.click()
                        logger.info("✅ Bouton ENVOYER cliqué (méthode normale)")
                    except:
                        # Méthode 2: JavaScript click
                        try:
                            self.driver.execute_script("arguments[0].click();", envoyer_button)
                            logger.info("✅ Bouton ENVOYER cliqué (JavaScript)")
                        except:
                            # Méthode 3: Forcer avec ActionChains
                            try:
                                from selenium.webdriver.common.action_chains import ActionChains
                                ActionChains(self.driver).move_to_element(envoyer_button).click().perform()
                                logger.info("✅ Bouton ENVOYER cliqué (ActionChains)")
                            except Exception as final_error:
                                logger.error(f"❌ Impossible de cliquer sur ENVOYER: {final_error}")
                                return None
                    
                    time.sleep(5)  # Attendre le chargement
                else:
                    logger.warning("⚠️ Bouton ENVOYER non trouvé")
                    return None
            except Exception as e:
                logger.warning(f"⚠️ Erreur générale clic ENVOYER: {str(e)}")
                return None
            
            # Étape 4: Chercher le bouton SITE N°1 et analyser son état
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                site1_button = None
                
                for btn in all_buttons:
                    text = btn.text.strip()
                    if "SITE N°1" in text and btn.is_displayed():
                        site1_button = btn
                        logger.info(f"🎯 Bouton SITE N°1 trouvé: '{text}'")
                        break
                
                if site1_button:
                    button_text = site1_button.text.strip()
                    
                    # Vérifier si c'est disponible pour voter
                    if "Votez maintenant" in button_text:
                        logger.info("✅ Vote disponible - aucun cooldown actif")
                        return 0  # Pas de cooldown
                    
                    # Vérifier si c'est en cooldown
                    elif any(x in button_text.lower() for x in ["min", "sec", "heure", "h", "m", "s", ":"]) and any(x in button_text for x in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]):
                        cooldown_minutes = parse_cooldown_time(button_text)
                        logger.info(f"⏰ Cooldown actif: {cooldown_minutes:.1f} minutes restantes")
                        return cooldown_minutes
                    
                    else:
                        logger.warning(f"❓ État du bouton unclear: '{button_text}'")
                        return None
                else:
                    logger.warning("⚠️ Bouton SITE N°1 non trouvé")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Erreur vérification bouton: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification cooldown initial: {str(e)}")
            return None
    
    def vote_oneblock_site1(self, base_url):
        """Vote pour le SITE N°1 sur oneblock.fr avec la logique corrigée"""
        
        try:
            logger.info("🎯 Démarrage du processus de vote pour: " + base_url)
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
                logger.info(f"✅ Pseudonyme '{self.username}' saisi dans oneblock.fr (placeholder: '{username_input.get_attribute('placeholder')}')")
            except Exception as e:
                logger.warning(f"⚠️ Erreur remplissage pseudo oneblock.fr: {str(e)}")
            
            # Étape 3: Cliquer sur ENVOYER avec méthodes robustes
            envoyer_button = None
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                    envoyer_button = btn
                    logger.info(f"✅ Bouton 'Envoyer' identifié: '{btn.text.strip()}'")
                    break
            
            if envoyer_button:
                logger.info("🔘 Clic sur bouton: 'ENVOYER'")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", envoyer_button)
                time.sleep(2)
                
                # Méthode 1: Clic normal
                try:
                    envoyer_button.click()
                    logger.info("✅ Clic normal sur 'ENVOYER' réussi")
                except:
                    # Méthode 2: JavaScript click
                    try:
                        self.driver.execute_script("arguments[0].click();", envoyer_button)
                        logger.info("✅ Clic JavaScript sur 'ENVOYER' réussi")
                    except:
                        # Méthode 3: ActionChains
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            ActionChains(self.driver).move_to_element(envoyer_button).click().perform()
                            logger.info("✅ Clic ActionChains sur 'ENVOYER' réussi")
                        except Exception as final_error:
                            logger.error(f"❌ Impossible de cliquer sur ENVOYER: {final_error}")
                
                time.sleep(5)
            
            # Étape 4: Chercher et cliquer sur le bouton SITE N°1
            logger.info("🔍 Recherche et clic direct sur bouton SITE N°1...")
            
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            site1_button = None
            
            for btn in all_buttons:
                text = btn.text.strip()
                if "SITE N°1" in text and "Votez maintenant" in text and btn.is_displayed():
                    site1_button = btn
                    logger.info(f"🎯 Bouton SITE N°1 trouvé: '{text}'")
                    break
            
            if site1_button:
                # Cliquer sur le bouton
                logger.info("🖱️ Clic sur bouton SITE N°1...")
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", site1_button)
                time.sleep(2)
                site1_button.click()
                logger.info("✅ Clic sur SITE N°1 effectué")
                
                # Attendre et vérifier si le vote est enregistré
                logger.info("⏳ Vérification du résultat du vote...")
                for wait_time in range(1, 31):  # Attendre jusqu'à 30 secondes pour l'AJAX
                    time.sleep(1)
                    
                    # Vérifier l'URL en priorité pour détecter la redirection rapidement
                    current_url = self.driver.current_url
                    if 'oneblock.fr' not in current_url:
                        logger.info(f"🎯 Redirection détectée vers: {current_url}")
                        # Continuer le processus de vote sur serveur-prive.net
                        return self.continue_vote_on_serveur_prive()
                    
                    # Vérifier s'il y a de nouvelles fenêtres/onglets
                    try:
                        window_handles = self.driver.window_handles
                        if len(window_handles) > 1:
                            logger.info(f"🪟 Nouvelle fenêtre détectée, basculement...")
                            # Basculer vers la nouvelle fenêtre
                            for handle in window_handles:
                                if handle != self.driver.current_window_handle:
                                    self.driver.switch_to.window(handle)
                                    new_url = self.driver.current_url
                                    logger.info(f"🎯 Nouvelle fenêtre URL: {new_url}")
                                    if 'serveur-prive.net' in new_url.lower():
                                        return self.continue_vote_on_serveur_prive()
                                    # Revenir à la fenêtre principale si ce n'est pas serveur-prive.net
                                    self.driver.switch_to.window(window_handles[0])
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur vérification fenêtres: {e}")
                    
                    # Vérifier l'état du bouton seulement si on est toujours sur OneBlock
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
                        # Si on ne peut plus accéder au bouton, c'est peut-être dû à une redirection
                        logger.info("⚠️ Impossible d'accéder au bouton - vérification redirection...")
                        pass
                
                logger.warning("⚠️ Pas de cooldown visible après 30s")
                return False
            else:
                logger.warning("⚠️ Bouton SITE N°1 'Votez maintenant' non trouvé")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erreur dans vote_oneblock_site1: {str(e)}")
            return False
    
    def continue_vote_on_serveur_prive(self):
        """Continue le processus de vote sur serveur-prive.net"""
        
        try:
            # Vérifier si on est sur serveur-prive.net
            current_url = self.driver.current_url
            logger.info(f"🔍 URL actuelle: {current_url}")
            if 'serveur-prive.net' not in current_url.lower():
                logger.error(f"❌ Pas sur serveur-prive.net. URL actuelle: {current_url}")
                return False
            
            logger.info("🌐 Sur serveur-prive.net, recherche du MTCaptcha...")
            
            # Attendre que le MTCaptcha se charge complètement
            logger.info("⏳ Attente du chargement complet du MTCaptcha...")
            time.sleep(5)
            
            # Chercher la sitekey MTCaptcha
            sitekey = None
            try:
                # Chercher dans les scripts
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                for script in scripts:
                    script_text = script.get_attribute('innerHTML') or ''
                    if 'MTPublic-' in script_text:
                        import re
                        matches = re.findall(r'MTPublic-[a-zA-Z0-9]+', script_text)
                        if matches:
                            sitekey = matches[0]
                            logger.info(f"Sitekey MTCaptcha trouvée dans JS config: {sitekey}")
                            break
                
                if not sitekey:
                    # Chercher dans les attributs data
                    captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-sitekey], [data-site-key]")
                    for elem in captcha_elements:
                        potential_key = elem.get_attribute('data-sitekey') or elem.get_attribute('data-site-key')
                        if potential_key and 'MTPublic-' in potential_key:
                            sitekey = potential_key
                            logger.info(f"Sitekey MTCaptcha trouvée dans attribut: {sitekey}")
                            break
                
                if not sitekey:
                    logger.error("❌ Sitekey MTCaptcha non trouvée")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erreur recherche sitekey: {str(e)}")
                return False
            
            # Remplir le pseudonyme si nécessaire
            logger.info("Vérification si pseudonyme doit être rempli...")
            try:
                username_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[name*='username'], input[id*='username'], input[placeholder*='pseudo']")
                for field in username_fields:
                    if field.is_displayed():
                        current_value = field.get_attribute('value')
                        if not current_value or current_value.strip() == '':
                            field.clear()
                            field.send_keys(self.username)
                            logger.info(f"Pseudonyme '{self.username}' saisi dans: {field.get_attribute('name') or field.get_attribute('id')}")
                        break
                else:
                    logger.info("Aucun champ pseudonyme trouvé ou accessible")
            except Exception as e:
                logger.warning(f"⚠️ Erreur avec champ username: {e}")
                try:
                    # Essayer avec JavaScript
                    self.driver.execute_script(f"document.querySelector('input[name*=\"username\"], input[id*=\"username\"]').value = '{self.username}';")
                    logger.info(f"✅ Pseudonyme '{self.username}' saisi via JavaScript")
                except Exception as e2:
                    logger.warning(f"⚠️ Erreur JavaScript username: {e2}")
            
            # Résoudre le MTCaptcha avec 2Captcha
            logger.info("Envoi de la demande de résolution à 2Captcha...")
            try:
                page_url = self.driver.current_url
                submit_data = {
                    'key': self.api_key,
                    'method': 'mt_captcha',
                    'sitekey': sitekey,
                    'pageurl': page_url,
                    'json': 1
                }
                
                response = requests.post('http://2captcha.com/in.php', data=submit_data, timeout=30)
                result = response.json()
                
                if result['status'] != 1:
                    logger.error(f"❌ Erreur soumission 2Captcha: {result}")
                    return False
                
                captcha_id = result['request']
                logger.info(f"Captcha soumis avec l'ID: {captcha_id}")
                
                # Attendre la résolution
                for attempt in range(30):
                    time.sleep(10)
                    
                    check_response = requests.get(f'http://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}&json=1', timeout=30)
                    check_result = check_response.json()
                    
                    if check_result['status'] == 1:
                        solution = check_result['request']
                        logger.info("MTCaptcha résolu avec succès!")
                        break
                    elif check_result.get('request') == 'CAPCHA_NOT_READY':
                        logger.info("Captcha en cours de résolution...")
                        continue
                    else:
                        logger.error(f"❌ Erreur résolution captcha: {check_result}")
                        return False
                else:
                    logger.error("❌ Timeout résolution captcha")
                    return False
                
                # Injecter la solution
                logger.info("Injection de la solution dans la page...")
                
                # Injecter dans le champ MTCaptcha
                try:
                    self.driver.execute_script(f"document.querySelector('input[name=\"mtcaptcha-verifiedtoken\"]').value = '{solution}';")
                    logger.info("Solution injectée dans: input[name='mtcaptcha-verifiedtoken']")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur injection solution: {e}")
                
                # Soumettre le formulaire
                logger.info("Soumission du formulaire...")
                
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
                                    logger.info(f"Formulaire soumis via clic: {selector}")
                                    form_submitted = True
                                    break
                                except:
                                    try:
                                        self.driver.execute_script("arguments[0].click();", element)
                                        logger.info(f"Formulaire soumis via JavaScript: {selector}")
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
                        logger.info("Formulaire soumis via JavaScript générique")
                        form_submitted = True
                    except Exception as e:
                        logger.error(f"❌ Erreur soumission formulaire: {e}")
                        return False
                
                # Vérifier le résultat
                logger.info("Vérification du résultat...")
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
                        logger.info(f"✅ Message de succès trouvé: '{success_msg}'")
                        
                        # Fermer la fenêtre serveur-privé et retourner sur OneBlock
                        logger.info("🔄 Fermeture de la fenêtre serveur-privé et retour sur OneBlock...")
                        return self.close_serveur_prive_and_check_cooldown()
                
                for pattern in error_patterns:
                    if pattern in visible_text:
                        error_msg = [line.strip() for line in visible_text.split('\n') if pattern in line][0]
                        logger.info(f"❌ Message d'erreur trouvé: '{error_msg}'")
                        return False
                
                # Si pas de message clair, considérer comme succès si on est toujours sur la bonne page
                if 'serveur-prive.net' in current_url:
                    logger.info("✅ Probablement réussi (pas de message d'erreur)")
                    logger.info("🔄 Fermeture de la fenêtre serveur-privé et retour sur OneBlock...")
                    return self.close_serveur_prive_and_check_cooldown()
                else:
                    logger.warning(f"⚠️ Résultat incertain, URL: {current_url}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erreur traitement MTCaptcha: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur générale: {str(e)}")
            return False
    
    def close_serveur_prive_and_check_cooldown(self):
        """Ferme la fenêtre serveur-privé et retourne sur OneBlock pour vérifier le cooldown"""
        
        try:
            # Fermer la fenêtre serveur-privé actuelle
            logger.info("🗂️ Fermeture de la fenêtre serveur-privé...")
            current_window = self.driver.current_window_handle
            self.driver.close()
            logger.info("✅ Fenêtre serveur-privé fermée")
            
            # Basculer vers la fenêtre OneBlock (première fenêtre)
            window_handles = self.driver.window_handles
            if len(window_handles) > 0:
                oneblock_window = window_handles[0]
                self.driver.switch_to.window(oneblock_window)
                logger.info("✅ Retour sur la fenêtre OneBlock")
            else:
                logger.error("❌ Aucune fenêtre OneBlock trouvée")
                return False
            
            # Continuer avec la vérification du cooldown
            return self.check_oneblock_cooldown()
            
        except Exception as e:
            logger.error(f"❌ Erreur fermeture fenêtre: {str(e)}")
            # En cas d'erreur, essayer quand même de vérifier le cooldown
            return self.check_oneblock_cooldown()
    
    def check_oneblock_cooldown(self):
        """Retourne sur OneBlock pour vérifier le cooldown"""
        
        try:
            # Basculer vers la fenêtre OneBlock existante
            logger.info("🔄 Basculement vers la fenêtre OneBlock existante...")
            window_handles = self.driver.window_handles
            
            # Trouver la fenêtre OneBlock (la première fenêtre ouverte)
            oneblock_window = window_handles[0] if len(window_handles) > 0 else None
            
            if oneblock_window:
                self.driver.switch_to.window(oneblock_window)
                logger.info("✅ Basculement vers OneBlock réussi")
                time.sleep(2)
                
                # Rafraîchir la page pour voir l'état actuel
                logger.info("🔄 Rafraîchissement de la page OneBlock...")
                self.driver.refresh()
                time.sleep(3)
            else:
                logger.error("❌ Fenêtre OneBlock non trouvée")
                return False
            
            # Remplir le pseudonyme si nécessaire
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
                )
                username_input.clear()
                username_input.send_keys(self.username)
                logger.info(f"✅ Pseudonyme '{self.username}' ressaisi sur OneBlock")
            except Exception as e:
                logger.warning(f"⚠️ Erreur remplissage pseudo OneBlock: {str(e)}")
            
            # Cliquer sur ENVOYER
            try:
                envoyer_button = None
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                        envoyer_button = btn
                        break
                
                if envoyer_button:
                    envoyer_button.click()
                    logger.info("✅ Bouton ENVOYER cliqué sur OneBlock")
                    time.sleep(3)
                else:
                    logger.warning("⚠️ Bouton ENVOYER non trouvé")
            except Exception as e:
                logger.warning(f"⚠️ Erreur clic ENVOYER: {str(e)}")
            
            # Chercher le bouton SITE N°1 et vérifier son état
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                site1_button = None
                
                for btn in all_buttons:
                    text = btn.text.strip()
                    if "SITE N°1" in text and btn.is_displayed():
                        site1_button = btn
                        logger.info(f"🎯 Bouton SITE N°1 trouvé: '{text}'")
                        break
                
                if site1_button:
                    button_text = site1_button.text.strip()
                    
                    # Vérifier si c'est un cooldown
                    if any(x in button_text.lower() for x in ["min", "sec", "heure", "h", "m", "s"]) and any(x in button_text for x in [":", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]):
                        logger.info(f"🎉 COOLDOWN DÉTECTÉ! Le vote est confirmé: '{button_text}'")
                        return True
                    elif "Votez maintenant" in button_text:
                        logger.warning(f"⚠️ Pas de cooldown - bouton encore disponible: '{button_text}'")
                        return False
                    else:
                        logger.info(f"📊 État du bouton SITE N°1: '{button_text}'")
                        # Si ce n'est ni "Votez maintenant" ni un temps, c'est peut-être un cooldown
                        return True
                else:
                    logger.warning("⚠️ Bouton SITE N°1 non trouvé sur OneBlock")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erreur vérification cooldown: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur retour OneBlock: {str(e)}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("Driver fermé")

def main():
    parser = argparse.ArgumentParser(description='Script de vote automatique MTCaptcha avec mode continu intelligent')
    parser.add_argument('--url', required=True, help='URL de vote sur serveur-prive.net')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout en secondes')
    parser.add_argument('--continuous', action='store_true', help='Mode continu intelligent avec détection du cooldown')
    
    args = parser.parse_args()
    
    logger.info("=== DÉMARRAGE DU SCRIPT DE VOTE MTCAPTCHA INTELLIGENT ===")
    logger.info(f"URL cible: {args.url}")
    logger.info(f"Mode continu intelligent: {args.continuous}")
    
    if args.continuous:
        run_continuous_voting(args)
    else:
        run_single_vote(args)

def run_single_vote(args):
    """Lance un vote unique"""
    voter = None
    try:
        voter = MTCaptchaVoter(timeout=args.timeout)
        
        success = voter.vote_oneblock_site1(args.url)
        
        if success:
            logger.info("Résultat final: ✅ SUCCÈS")
            logger.info("=== TEST TERMINÉ AVEC SUCCÈS ===")
        else:
            logger.info("Résultat final: ❌ ÉCHEC")
            logger.info("=== TEST ÉCHOUÉ ===")
            
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {str(e)}")
        logger.info("=== TEST ÉCHOUÉ ===")
    finally:
        if voter:
            voter.close()

def run_continuous_voting(args):
    """Lance le mode de vote continu intelligent"""
    logger.info("🤖 MODE CONTINU INTELLIGENT ACTIVÉ")
    logger.info("📋 Le script va détecter automatiquement les cooldowns")
    logger.info("🛑 Appuyez sur Ctrl+C pour arrêter")
    
    vote_count = 0
    
    try:
        while True:
            vote_count += 1
            logger.info(f"🎯 === CYCLE #{vote_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            
            voter = None
            try:
                voter = MTCaptchaVoter(timeout=args.timeout)
                
                # Étape 1: Vérifier l'état initial du cooldown
                logger.info("🔍 Phase 1: Vérification du cooldown...")
                initial_cooldown = voter.check_initial_cooldown()
                
                if initial_cooldown is None:
                    logger.error("❌ Impossible de déterminer l'état du cooldown")
                    wait_minutes = 5  # Attendre 5 minutes par défaut
                elif initial_cooldown > 0:
                    logger.info(f"⏰ Cooldown détecté: {initial_cooldown:.1f} minutes")
                    wait_minutes = initial_cooldown + 2  # Ajouter 2 minutes de marge
                    logger.info(f"💤 Attente du cooldown + 2min de marge = {wait_minutes:.1f} minutes...")
                    
                    # Attendre le cooldown avec affichage du temps restant
                    wait_and_display_countdown(wait_minutes)
                    
                    logger.info("⏰ Cooldown terminé - Nouvelle vérification...")
                    
                    # Re-vérifier après attente
                    recheck_cooldown = voter.check_initial_cooldown()
                    if recheck_cooldown is not None and recheck_cooldown > 0:
                        logger.warning(f"⚠️ Cooldown encore actif: {recheck_cooldown:.1f} minutes - attente supplémentaire...")
                        wait_and_display_countdown(recheck_cooldown + 1)
                
                # Étape 2: Tenter le vote
                if initial_cooldown == 0 or initial_cooldown is None:
                    logger.info("🗳️ Phase 2: Tentative de vote...")
                    success = voter.vote_oneblock_site1(args.url)
                    
                    if success:
                        logger.info(f"✅ Vote #{vote_count} réussi!")
                        
                        # Étape 3: Détecter le nouveau cooldown après vote réussi
                        logger.info("🔍 Phase 3: Détection du nouveau cooldown...")
                        time.sleep(3)  # Laisser le temps au système de s'actualiser
                        
                        try:
                            new_cooldown = voter.check_initial_cooldown()
                            if new_cooldown is not None and new_cooldown > 0:
                                wait_minutes = new_cooldown + 2  # Marge de sécurité
                                logger.info(f"🎯 Nouveau cooldown détecté: {new_cooldown:.1f} minutes")
                                logger.info(f"⏳ Prochain vote dans ~{wait_minutes:.1f} minutes")
                            else:
                                wait_minutes = 90  # Cooldown par défaut de 1h30
                                logger.warning(f"⚠️ Cooldown non détecté, utilisation du défaut: {wait_minutes} minutes")
                        except:
                            wait_minutes = 90  # Sécurité
                            logger.warning(f"⚠️ Erreur détection cooldown, utilisation du défaut: {wait_minutes} minutes")
                    else:
                        logger.warning(f"❌ Vote #{vote_count} échoué")
                        wait_minutes = 10  # Réessayer dans 10 minutes en cas d'échec
                        logger.info(f"🔄 Nouvelle tentative dans {wait_minutes} minutes...")
                
                # Attendre avant le prochain cycle
                if 'wait_minutes' in locals() and wait_minutes > 0:
                    next_vote_time = datetime.now() + timedelta(minutes=wait_minutes)
                    logger.info(f"⏱️ Prochain cycle prévu à: {next_vote_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    wait_and_display_countdown(wait_minutes)
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors du cycle #{vote_count}: {str(e)}")
                wait_minutes = 10  # Attendre 10 minutes en cas d'erreur
                logger.info(f"🔄 Nouvelle tentative dans {wait_minutes} minutes...")
                wait_and_display_countdown(wait_minutes)
            finally:
                if voter:
                    try:
                        voter.close()
                    except:
                        pass
            
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur")
        logger.info(f"📊 Total des cycles effectués: {vote_count}")
        logger.info("=== SCRIPT ARRÊTÉ ===")
    except Exception as e:
        logger.error(f"❌ Erreur fatale en mode continu: {str(e)}")
        logger.info(f"📊 Total des cycles effectués: {vote_count}")
        logger.info("=== SCRIPT TERMINÉ AVEC ERREUR ===")

def wait_and_display_countdown(wait_minutes):
    """Attend le temps spécifié avec affichage du temps restant"""
    wait_seconds = int(wait_minutes * 60)
    
    # Affichage initial
    logger.info(f"💤 Début de l'attente: {wait_minutes:.1f} minutes...")
    
    # Afficher le temps restant toutes les minutes (ou moins si < 5 minutes)
    interval = 60 if wait_minutes > 5 else 30
    
    for remaining in range(wait_seconds, 0, -interval):
        remaining_minutes = remaining / 60
        if remaining_minutes >= 1:
            logger.info(f"⏳ Temps restant: {remaining_minutes:.1f} minute(s)")
        elif remaining <= 60:
            logger.info(f"⏳ Temps restant: {remaining} seconde(s)")
        time.sleep(min(interval, remaining))
    
    logger.info("✅ Attente terminée!")

if __name__ == "__main__":
    main()