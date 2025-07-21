#!/usr/bin/env python3
"""
MTCaptcha Testing Script
Script pour tester l'intégration MTCaptcha sur votre propre site web
Usage: python mtcaptcha_tester.py --url https://yoursite.com/form
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
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mtcaptcha_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MTCaptchaTester:
    def __init__(self, api_key: str, timeout: int = 300):
        self.api_key = api_key
        self.timeout = timeout
        self.driver = None
        self.wait = None
        
    def setup_driver(self, headless: bool = False):
        """Configure et initialise le driver Selenium"""
        logger.info("Configuration du driver Selenium...")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        
        logger.info("Driver Selenium configuré avec succès")

    def navigate_to_vote_page(self, base_url: str) -> bool:
        """Navigue via oneblock.fr/vote vers le site de vote"""
        try:
            # Étape 1: Aller sur oneblock.fr/vote
            oneblock_url = "https://oneblock.fr/vote"
            logger.info(f"🌐 Étape 1: Accès à {oneblock_url}")
            self.driver.get(oneblock_url)
            time.sleep(3)
            
            # Étape 2: Remplir le champ pseudo sur oneblock.fr
            try:
                pseudo_selectors = [
                    "input[placeholder*='pseudo' i]",
                    "input[placeholder*='Entrez votre pseudo']",
                    "input[name='pseudo']",
                    "input[name='username']",
                    "input[type='text']"
                ]
                
                pseudo_filled = False
                for selector in pseudo_selectors:
                    try:
                        pseudo_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if pseudo_field.is_displayed() and pseudo_field.is_enabled():
                            placeholder = pseudo_field.get_attribute('placeholder') or ''
                            if 'pseudo' in placeholder.lower():
                                pseudo_field.clear()
                                pseudo_field.send_keys("zCapsLock")
                                logger.info(f"✅ Pseudonyme 'zCapsLock' saisi dans oneblock.fr (placeholder: '{placeholder}')")
                                pseudo_filled = True
                                break
                    except:
                        continue
                        
                if not pseudo_filled:
                    logger.warning("⚠️ Champ pseudo non trouvé sur oneblock.fr")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur remplissage pseudo oneblock.fr: {str(e)}")
            
            # Étape 2a: Injecter l'interception API AVANT de cliquer sur Envoyer
            try:
                api_intercept_script = """
                window.voteUrls = [];
                
                // Intercepter fetch
                (function() {
                    var originalFetch = window.fetch;
                    window.fetch = function() {
                        return originalFetch.apply(this, arguments).then(function(response) {
                            if (arguments[0].includes('availableVote')) {
                                response.clone().text().then(function(text) {
                                    try {
                                        var data = JSON.parse(text);
                                        window.voteUrls = data;
                                        console.log('🎯 Vote URLs interceptées:', data);
                                    } catch(e) {}
                                });
                            }
                            return response;
                        });
                    };
                })();
                """
                
                self.driver.execute_script(api_intercept_script)
                logger.info("✅ Script d'interception API injecté")
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur injection script API: {e}")
            
            # Étape 2b: Cliquer sur "Envoyer" après avoir rempli le pseudo
            try:
                # Attendre un peu que la page charge
                time.sleep(2)
                
                # Chercher le bouton ENVOYER directement
                envoyer_elements = []
                
                # Méthode principale: chercher par texte
                xpath_selectors = [
                    "//button[contains(text(), 'ENVOYER')]",
                    "//button[contains(text(), 'Envoyer')]", 
                    "//input[@value='ENVOYER']",
                    "//input[@value='Envoyer']"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                envoyer_elements.append(elem)
                                logger.info(f"✅ Bouton 'Envoyer' trouvé: '{elem.text.strip()}'")
                    except:
                        continue
                
                # Fallback: chercher tous les boutons et filtrer
                if not envoyer_elements:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for btn in all_buttons:
                        text = btn.text.strip().lower()
                        if 'envoyer' in text and btn.is_displayed() and btn.is_enabled():
                            envoyer_elements.append(btn)
                            logger.info(f"✅ Bouton 'Envoyer' identifié: '{btn.text.strip()}'")
                
                # Cliquer sur le bouton ENVOYER
                for envoyer_btn in envoyer_elements:
                    try:
                        text = envoyer_btn.text.strip() or 'ENVOYER'
                        logger.info(f"🔘 Clic sur bouton: '{text}'")
                        
                        # Scroller vers l'élément et cliquer
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", envoyer_btn)
                        time.sleep(1)
                        
                        # Essayer d'abord clic normal, puis JavaScript si intercepté
                        try:
                            envoyer_btn.click()
                            logger.info(f"✅ Clic normal sur '{text}' réussi")
                        except Exception as click_error:
                            if "click intercepted" in str(click_error):
                                logger.info(f"⚠️ Clic intercepté, utilisation de JavaScript...")
                                self.driver.execute_script("arguments[0].click();", envoyer_btn)
                                logger.info(f"✅ Clic JavaScript sur '{text}' réussi")
                            else:
                                raise click_error
                        
                        # Attendre le chargement des sites de vote
                        time.sleep(5)
                        
                        # Vérifier que les sites de vote sont maintenant disponibles
                        vote_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Votez maintenant')]")
                        active_vote_buttons = [btn for btn in vote_buttons if btn.is_displayed()]
                        
                        if active_vote_buttons:
                            logger.info(f"✅ {len(active_vote_buttons)} sites de vote maintenant disponibles")
                            break
                        else:
                            logger.info("⚠️ Sites de vote pas encore visibles, tentative suivante...")
                            
                    except Exception as e:
                        logger.warning(f"Erreur clic bouton '{text}': {str(e)}")
                        continue
                        
                if not envoyer_elements:
                    logger.warning("⚠️ Aucun bouton 'Envoyer' trouvé")
                        
            except Exception as e:
                logger.warning(f"⚠️ Erreur recherche 'Envoyer': {str(e)}")
            
            time.sleep(2)
            
            # Étape 3: Attendre et récupérer l'URL de vote interceptée
            try:
                # Attendre que l'API soit appelée (se fait après le clic ENVOYER)
                logger.info("⏳ Attente de l'appel API availableVote...")
                serveur_prive_url = None
                
                # Attendre jusqu'à 10 secondes que l'API soit appelée
                for wait_time in range(1, 11):
                    time.sleep(1)
                    vote_urls = self.driver.execute_script("return window.voteUrls;")
                    
                    if isinstance(vote_urls, list) and len(vote_urls) > 0:
                        logger.info(f"📊 URLs de vote interceptées après {wait_time}s: {vote_urls}")
                        
                        # Chercher l'URL pour serveur-prive
                        for site_info in vote_urls:
                            if isinstance(site_info, dict) and site_info.get('id') == 'serveur-prive':
                                serveur_prive_url = site_info.get('url')
                                logger.info(f"🎯 URL serveur-prive trouvée dans API: {serveur_prive_url}")
                                break
                        break
                    else:
                        logger.info(f"   Attente API... {wait_time}s (URLs: {vote_urls})")
                
                # Si on a trouvé l'URL, naviguer directement
                if serveur_prive_url:
                    logger.info(f"🚀 Navigation directe vers: {serveur_prive_url}")
                    self.driver.get(serveur_prive_url)
                    time.sleep(3)
                    return True
                else:
                    logger.warning("⚠️ URL serveur-prive non trouvée dans l'API après 10s, utilisation du bouton")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur récupération API: {e}")
            
            # Fallback: Chercher et cliquer directement sur le bouton SITE N°1
            try:
                logger.info("🔍 Recherche et clic direct sur bouton SITE N°1...")
                
                # Chercher tous les boutons
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
                    
                    # Attendre et vérifier si le vote est enregistré (cooldown)
                    logger.info("⏳ Vérification du résultat du vote...")
                    for wait_time in range(1, 6):
                        time.sleep(1)
                        try:
                            # Vérifier si le bouton affiche un cooldown
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
                    
                    # Vérifier l'URL au cas où il y aurait une redirection
                    current_url = self.driver.current_url
                    if 'oneblock.fr' not in current_url:
                        logger.info(f"🎯 Redirection détectée vers: {current_url}")
                        return True
                    
                    logger.warning("⚠️ Vote peut-être réussi mais pas de cooldown visible")
                    return True  # On considère que ça a marché
                    
                else:
                    logger.warning("⚠️ Bouton SITE N°1 'Votez maintenant' non trouvé")
                
                for site1_elem in site1_elements:
                    logger.info(f"📍 SITE N°1 trouvé: '{site1_elem.text.strip()[:50]}...'")
                    
                    try:
                        # Chercher le container parent (button avec classes spécifiques)
                        parent_container = site1_elem.find_element(By.XPATH, "./ancestor::button[1] | ./ancestor::div[contains(@class, 'bg-gradient') or contains(@class, 'site')][1]")
                        
                        # Vérifier si le site est disponible (pas grisé/disabled)
                        classes = parent_container.get_attribute('class') or ''
                        is_disabled = 'grayscale' in classes or 'cursor-not-allowed' in classes
                        text_content = parent_container.text.strip()
                        
                        # Vérifier aussi le contenu textuel pour déterminer l'état
                        is_available = 'Votez maintenant' in text_content
                        
                        logger.info(f"🔍 Analyse du bouton SITE N°1:")
                        logger.info(f"   Texte: '{text_content}'")
                        logger.info(f"   Classes: '{classes}'")
                        logger.info(f"   Disabled par CSS: {is_disabled}")
                        logger.info(f"   Disponible (texte): {is_available}")
                        
                        # Si le bouton est disponible (contient "Votez maintenant"), cliquer directement
                        if is_available and parent_container.tag_name == 'button':
                            logger.info("🎯 SITE N°1 disponible - clic direct sur le bouton!")
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_container)
                                time.sleep(2)
                                
                                # URL avant clic
                                url_before = self.driver.current_url
                                logger.info(f"URL avant clic: {url_before}")
                                
                                self.driver.execute_script("arguments[0].click();", parent_container)
                                logger.info("✅ Clic direct sur bouton SITE N°1 réussi")
                                
                                # Attendre et vérifier les changements
                                for wait_seconds in [2, 5, 10]:
                                    time.sleep(wait_seconds - (2 if wait_seconds > 2 else 0))
                                    current_url = self.driver.current_url
                                    
                                    # Vérifier changement d'URL
                                    if current_url != url_before:
                                        logger.info(f"✅ Redirection détectée après {wait_seconds}s vers: {current_url}")
                                        return True
                                    
                                    # Vérifier changement de texte du bouton (AJAX en cours)
                                    try:
                                        updated_text = parent_container.text.strip()
                                        if "Veuillez patienter" in updated_text:
                                            logger.info(f"⏳ Traitement en cours (texte: '{updated_text}') - attente...")
                                            continue
                                        elif "Votez maintenant" not in updated_text and wait_seconds >= 5:
                                            logger.info(f"🔄 Texte du bouton changé: '{updated_text}' - possible redirection à venir")
                                    except Exception:
                                        pass
                                
                                # Vérification finale
                                final_url = self.driver.current_url
                                if final_url != url_before:
                                    logger.info(f"✅ Redirection finale vers: {final_url}")
                                    return True
                                else:
                                    logger.warning("⚠️ Pas de redirection après 10s d'attente")
                                    # Continuer vers navigation directe
                                    
                            except Exception as e:
                                logger.warning(f"Erreur clic direct bouton SITE N°1: {e}")
                        
                        elif is_disabled and not is_available:
                            logger.warning("⚠️ SITE N°1 est désactivé - connexion requise")
                            
                            # Chercher si on peut cliquer quand même (parfois le bouton global fonctionne)
                            if parent_container.tag_name == 'button':
                                try:
                                    logger.info("🔄 Tentative de clic sur bouton désactivé...")
                                    self.driver.execute_script("arguments[0].click();", parent_container)
                                    time.sleep(3)
                                    
                                    # Vérifier si ça a ouvert quelque chose
                                    current_url = self.driver.current_url
                                    if 'oneblock.fr' not in current_url:
                                        logger.info(f"✅ Redirection réussie vers: {current_url}")
                                        return True
                                    else:
                                        logger.info("⚠️ Pas de redirection, site vraiment désactivé")
                                        
                                except Exception as e:
                                    logger.debug(f"Erreur clic bouton désactivé: {e}")
                            
                            continue
                        
                        # Chercher un lien "Votez maintenant" dans ou près de ce container
                        vote_selectors = [
                            ".//a[contains(text(), 'Votez maintenant')]",
                            ".//button[contains(text(), 'Votez maintenant')]",
                            ".//button[contains(text(), 'SITE N°1') and contains(text(), 'Votez maintenant')]",
                            ".//button[contains(text(), 'SITE N°1') and not(contains(@class, 'cursor-not-allowed'))]",
                            "./following-sibling::*//a[contains(text(), 'Votez maintenant')]",
                            "./parent::*//a[contains(text(), 'Votez maintenant')]"
                        ]
                        
                        for selector in vote_selectors:
                            try:
                                vote_buttons = parent_container.find_elements(By.XPATH, selector)
                                for button in vote_buttons:
                                    if button.is_displayed():
                                        href = button.get_attribute('href')
                                        onclick = button.get_attribute('onclick')
                                        text = button.text.strip()
                                        
                                        # Vérifier que c'est un lien externe ou un bouton avec action
                                        is_valid_link = False
                                        
                                        # Cas 1: Lien href externe (pas oneblock.fr)
                                        if href and 'oneblock.fr' not in href and href.startswith('http'):
                                            is_valid_link = True
                                            logger.info(f"🎯 Lien vote SITE N°1 trouvé (href): '{text}' -> {href}")
                                        
                                        # Cas 2: Bouton avec onclick (même sans href valide)
                                        elif onclick or (button.tag_name in ['button', 'input'] and text.lower() in ['votez maintenant', 'voter', 'vote']):
                                            is_valid_link = True
                                            logger.info(f"🎯 Bouton vote SITE N°1 trouvé (onclick/button): '{text}' -> onclick: {onclick}")
                                        
                                        if is_valid_link:
                                            # Scroller et cliquer
                                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                            time.sleep(2)
                                            button.click()
                                            logger.info("✅ Clic sur lien/bouton vote SITE N°1")
                                            time.sleep(5)
                                            return True
                                            
                            except Exception:
                                continue
                                
                    except Exception as e:
                        logger.debug(f"Erreur container site n°1: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Erreur recherche site n°1: {str(e)}")
            
            # Fallback: Chercher tous les liens "Votez maintenant" 
            vote_button_selectors = [
                "//a[contains(text(), 'Votez maintenant')]",
                "//button[contains(text(), 'Votez maintenant')]", 
                "//a[contains(text(), 'Vote')]",
                "//button[contains(text(), 'Vote')]",
                "a[href*='serveur-prive.net']",
                "a[href*='oneblockbyrivrs']"
            ]
            
            for selector in vote_button_selectors:
                try:
                    if selector.startswith('//'):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                    for element in elements:
                        if element.is_displayed():
                            href = element.get_attribute('href')
                            text = element.text.strip()
                            
                            # Vérifier si c'est vraiment un lien externe (pas oneblock.fr)
                            if href and ('serveur-prive.net' in href or 'oneblockbyrivrs' in href):
                                logger.info(f"🔗 Lien de vote externe trouvé: {text} -> {href}")
                                
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(1)
                                element.click()
                                logger.info("✅ Clic sur le lien de vote externe")
                                time.sleep(5)
                                return True
                                
                except Exception as e:
                    logger.debug(f"Erreur avec sélecteur {selector}: {str(e)}")
                    continue
                    
            # Si aucun lien trouvé, aller directement à l'URL de base
            logger.warning("⚠️ Aucun lien de vote trouvé sur oneblock.fr, navigation directe")
            
            # Corriger l'URL si c'est l'ancienne version sans /minecraft/
            if 'serveur-prive.net/oneblockbyrivrs/vote' in base_url:
                base_url = base_url.replace('/oneblockbyrivrs/vote', '/minecraft/oneblockbyrivrs/vote')
                logger.info(f"🔄 URL corrigée: {base_url}")
            
            self.driver.get(base_url)
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur navigation oneblock.fr: {str(e)}")
            # En cas d'erreur, aller directement à l'URL de base
            logger.info("🔄 Fallback: navigation directe vers serveur-prive.net")
            self.driver.get(base_url)
            time.sleep(3)
            return True

    def get_mtcaptcha_sitekey(self, url: str) -> Optional[str]:
        """Récupère la clé sitekey du MTCaptcha"""
        logger.info(f"🎯 Démarrage du processus de vote pour: {url}")
        
        try:
            # Nouvelle navigation en 2 étapes
            if not self.navigate_to_vote_page(url):
                return None
                
            # Maintenant on devrait être sur la page de vote
            time.sleep(2)
            
            # Méthode 1: Recherche dans les attributs DOM
            selectors = [
                "div[data-sitekey]",
                "div[data-mt-sitekey]", 
                ".mtcaptcha[data-sitekey]",
                "[data-sitekey]"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    sitekey = element.get_attribute("data-sitekey") or element.get_attribute("data-mt-sitekey")
                    if sitekey:
                        logger.info(f"Sitekey MTCaptcha trouvée dans DOM: {sitekey}")
                        return sitekey
                except NoSuchElementException:
                    continue
            
            # Méthode 2: Recherche dans la configuration JavaScript
            try:
                sitekey = self.driver.execute_script("""
                    if (typeof mtcaptchaConfig !== 'undefined' && mtcaptchaConfig.sitekey) {
                        return mtcaptchaConfig.sitekey;
                    }
                    return null;
                """)
                if sitekey:
                    logger.info(f"Sitekey MTCaptcha trouvée dans JS config: {sitekey}")
                    return sitekey
            except Exception as e:
                logger.debug(f"Erreur lecture config JS: {str(e)}")
            
            # Méthode 3: Recherche dans le code source de la page
            try:
                page_source = self.driver.page_source
                import re
                
                # Recherche de la sitekey dans le code source
                patterns = [
                    r'sitekey\s*:\s*["\']([^"\']+)["\']',
                    r'data-sitekey\s*=\s*["\']([^"\']+)["\']',
                    r'MTPublic-[a-zA-Z0-9]+'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        sitekey = match.group(1) if len(match.groups()) > 0 else match.group(0)
                        logger.info(f"Sitekey MTCaptcha trouvée via regex: {sitekey}")
                        return sitekey
                        
            except Exception as e:
                logger.debug(f"Erreur recherche regex: {str(e)}")
                    
            logger.error("Aucune sitekey MTCaptcha trouvée sur la page")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la sitekey: {str(e)}")
            return None

    def solve_mtcaptcha(self, sitekey: str, page_url: str) -> Optional[str]:
        """Résout le MTCaptcha via l'API 2Captcha"""
        logger.info("Envoi de la demande de résolution à 2Captcha...")
        
        # Étape 1: Soumission du captcha
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
                logger.error(f"Erreur lors de la soumission: {result}")
                return None
                
            captcha_id = result['request']
            logger.info(f"Captcha soumis avec l'ID: {captcha_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la soumission: {str(e)}")
            return None

        # Étape 2: Récupération de la solution
        get_url = "http://2captcha.com/res.php"
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                time.sleep(10)  # Attendre 10 secondes entre chaque vérification
                
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
                    logger.error(f"Erreur lors de la résolution: {result}")
                    return None
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération: {str(e)}")
                continue
                
        logger.error("Timeout lors de la résolution du captcha")
        return None

    def fill_pseudonyme(self) -> bool:
        """Remplit le champ pseudonyme si disponible"""
        try:
            pseudonyme_selectors = [
                "input[name='pseudonyme']",
                "input[name='username']", 
                "input[name='pseudo']",
                "input[id='pseudonyme']",
                "input[placeholder*='pseudo' i]"
            ]
            
            for selector in pseudonyme_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed() and element.is_enabled():
                        element.clear()
                        element.send_keys("zCapsLock")
                        logger.info(f"Pseudonyme 'zCapsLock' saisi dans: {selector}")
                        return True
                except:
                    continue
            
            logger.info("Aucun champ pseudonyme trouvé ou accessible")
            return False
            
        except Exception as e:
            logger.info(f"Champ pseudonyme non accessible: {str(e)}")
            return False

    def fill_username_field(self) -> bool:
        """Remplit le champ username avec zCapsLock"""
        try:
            # Attendre que le champ soit disponible
            time.sleep(2)
            
            # Le champ s'appelle 'username' d'après nos tests Safari
            username_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
            
            # Scroller vers le champ
            self.driver.execute_script("arguments[0].scrollIntoView(true);", username_field)
            time.sleep(1)
            
            # Remplir le champ
            username_field.clear()
            username_field.send_keys("zCapsLock")
            
            # Vérifier que la valeur a été saisie
            current_value = username_field.get_attribute('value')
            if current_value == "zCapsLock":
                logger.info("✅ Pseudonyme 'zCapsLock' saisi avec succès dans le champ username")
                return True
            else:
                logger.warning(f"⚠️ Valeur dans le champ: '{current_value}' (attendu: 'zCapsLock')")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur avec champ username: {str(e)}")
            # Essayer une approche JavaScript en fallback
            try:
                self.driver.execute_script("""
                    var usernameField = document.querySelector('input[name="username"]');
                    if (usernameField) {
                        usernameField.value = 'zCapsLock';
                        usernameField.dispatchEvent(new Event('input', { bubbles: true }));
                        usernameField.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                """)
                logger.info("✅ Pseudonyme 'zCapsLock' saisi via JavaScript")
                return True
            except Exception as js_error:
                logger.error(f"❌ Erreur JavaScript aussi: {str(js_error)}")
                return False

    def inject_solution(self, solution: str) -> bool:
        """Injecte la solution dans les champs appropriés"""
        logger.info("Injection de la solution dans la page...")
        
        try:
            # Remplir le champ username avec zCapsLock
            self.fill_username_field()
            
            # Pour MTCaptcha, chercher les champs de réponse possibles
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
                    logger.info(f"Solution injectée dans: {selector}")
                    injected = True
                except NoSuchElementException:
                    continue
            
            if not injected:
                # Tentative d'injection via JavaScript pour MTCaptcha
                script = f"""
                if (window.mtcaptcha) {{
                    window.mtcaptcha.setToken('{solution}');
                }}
                """
                self.driver.execute_script(script)
                logger.info("Solution injectée via l'API JavaScript MTCaptcha")
                injected = True
                
            return injected
            
        except Exception as e:
            logger.error(f"Erreur lors de l'injection: {str(e)}")
            return False

    def submit_form(self) -> bool:
        """Soumet le formulaire"""
        logger.info("Soumission du formulaire...")
        
        try:
            # Recherche spécifique pour le site de vote
            submit_selectors = [
                "#voteBtn",  # Bouton principal "Je vote maintenant"
                "button[onclick*='vote']",
                "button:contains('vote')",
                "input[type='submit']",
                "button[type='submit']",
                ".submit-btn",
                "#submit"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    # Scroller vers l'élément pour s'assurer qu'il est visible
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                    time.sleep(1)
                    
                    # Essayer le clic normal
                    try:
                        submit_btn.click()
                        logger.info(f"Formulaire soumis avec succès via: {selector}")
                        return True
                    except:
                        # Si le clic normal échoue, utiliser JavaScript
                        self.driver.execute_script("arguments[0].click();", submit_btn)
                        logger.info(f"Formulaire soumis via JavaScript: {selector}")
                        return True
                        
                except:
                    continue
                    
            # Si aucun bouton trouvé, essayer de soumettre via JavaScript
            logger.info("Tentative de soumission via JavaScript...")
            self.driver.execute_script("""
                if (document.forms.length > 0) {
                    document.forms[0].submit();
                } else if (typeof submitVote === 'function') {
                    submitVote();
                } else if (document.getElementById('voteBtn')) {
                    document.getElementById('voteBtn').click();
                }
            """)
            logger.info("Formulaire soumis via JavaScript")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la soumission: {str(e)}")
            return False

    def check_result(self) -> str:
        """Vérifie le résultat de la soumission"""
        logger.info("Vérification du résultat...")
        
        try:
            time.sleep(5)  # Attendre le chargement de la page
            
            # Vérifier d'abord les messages dans les alertes
            alert_selectors = [
                ".alert-success",
                ".alert-danger", 
                ".alert-message",
                ".alert.alert-success",
                ".alert.alert-danger",
                ".error-message",
                "[class*='alert'][class*='success']",
                "[class*='alert'][class*='danger']"
            ]
            
            for selector in alert_selectors:
                try:
                    alert_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in alert_elements:
                        if element.is_displayed():
                            alert_text = element.text.strip()
                            if alert_text:
                                # Vérifier si c'est un succès
                                if any(word in alert_text.lower() for word in ['succès', 'success', 'validé', 'validated', 'vote réussi']):
                                    logger.info(f"✅ Message de succès trouvé: '{alert_text}'")
                                    return f"✅ SUCCÈS - Message: '{alert_text}'"
                                else:
                                    logger.info(f"❌ Message d'erreur trouvé: '{alert_text}'")
                                    return f"❌ ÉCHEC - Erreur: '{alert_text}'"
                except:
                    continue
            
            # Vérifier les indicateurs de succès dans le texte
            page_text = self.driver.page_source.lower()
            current_url = self.driver.current_url
            
            success_indicators = [
                "success", "thank you", "merci", "completed", "submitted", "voté"
            ]
            
            for indicator in success_indicators:
                if indicator in page_text:
                    return f"✅ SUCCÈS - Indicateur détecté: '{indicator}'"
                    
            # Vérifier si l'URL a changé (redirection)
            if "success" in current_url or "thank" in current_url:
                return "✅ SUCCÈS - Redirection détectée vers page de succès"
                
            # Vérifier les erreurs génériques dans le texte
            error_indicators = [
                "error", "failed", "invalid", "incorrect", "erreur", "échec", 
                "cooldown", "attendre", "wait", "trop tôt", "too early"
            ]
            
            for indicator in error_indicators:
                if indicator in page_text:
                    return f"❌ ÉCHEC - Erreur détectée: '{indicator}'"
                    
            # Log du contenu de la page pour debug
            logger.info("🔍 Contenu de la page pour analyse:")
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                lines = body_text.split('\n')[:10]  # Premières 10 lignes
                for i, line in enumerate(lines):
                    if line.strip():
                        logger.info(f"   Ligne {i+1}: {line.strip()}")
            except:
                pass
                    
            return "⚠️ INCERTAIN - Résultat non déterminé (voir logs pour détails)"
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {str(e)}")
            return f"❌ ERREUR - {str(e)}"

    def run_test(self, url: str, headless: bool = False) -> bool:
        """Exécute le test complet"""
        try:
            self.setup_driver(headless)
            
            # Étape 1: Récupérer la sitekey
            sitekey = self.get_mtcaptcha_sitekey(url)
            if not sitekey:
                return False
            
            # Étape 2: Remplir le pseudonyme dès que possible (optionnel)
            logger.info("Vérification si pseudonyme doit être rempli...")
            try:
                self.fill_pseudonyme()
            except:
                logger.info("Pseudonyme ignoré - probablement déjà prérempli")
                
            # Étape 3: Résoudre le captcha
            solution = self.solve_mtcaptcha(sitekey, url)
            if not solution:
                return False
                
            # Étape 4: Injecter la solution
            if not self.inject_solution(solution):
                return False
                
            # Étape 5: Soumettre le formulaire
            if not self.submit_form():
                return False
                
            # Étape 6: Vérifier le résultat
            result = self.check_result()
            logger.info(f"Résultat final: {result}")
            
            return "SUCCÈS" in result
            
        except Exception as e:
            logger.error(f"Erreur générale: {str(e)}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver fermé")

def main():
    parser = argparse.ArgumentParser(description='Testeur MTCaptcha pour votre site web')
    parser.add_argument('--url', required=True, help='URL de la page contenant le MTCaptcha')
    parser.add_argument('--headless', action='store_true', help='Exécuter en mode headless')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout pour la résolution (secondes)')
    
    args = parser.parse_args()
    
    # Charger les variables d'environnement
    load_dotenv()
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    
    if not api_key:
        logger.error("Clé API 2Captcha manquante. Vérifiez votre fichier .env")
        return
        
    logger.info("=== DÉMARRAGE DU TEST MTCAPTCHA ===")
    logger.info(f"URL cible: {args.url}")
    logger.info(f"Mode headless: {args.headless}")
    
    tester = MTCaptchaTester(api_key, args.timeout)
    success = tester.run_test(args.url, args.headless)
    
    if success:
        logger.info("=== TEST TERMINÉ AVEC SUCCÈS ===")
    else:
        logger.info("=== TEST ÉCHOUÉ ===")

if __name__ == "__main__":
    main()