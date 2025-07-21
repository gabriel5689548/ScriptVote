#!/usr/bin/env python3

import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_ajax_intercept():
    """Intercepter les appels AJAX lors du clic sur Votez maintenant"""
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        logger.info("=== DEBUG AJAX INTERCEPT ===")
        
        # Activer l'interception réseau
        driver.execute_cdp_cmd('Network.enable', {})
        
        # Injecter un script pour intercepter les appels AJAX
        ajax_intercept_script = """
        window.ajaxRequests = [];
        window.ajaxResponses = [];
        
        // Intercepter XMLHttpRequest
        (function() {
            var originalOpen = XMLHttpRequest.prototype.open;
            var originalSend = XMLHttpRequest.prototype.send;
            
            XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
                this._method = method;
                this._url = url;
                console.log('🌐 AJAX Request:', method, url);
                window.ajaxRequests.push({method: method, url: url, timestamp: Date.now()});
                return originalOpen.apply(this, arguments);
            };
            
            XMLHttpRequest.prototype.send = function(body) {
                var xhr = this;
                xhr.addEventListener('readystatechange', function() {
                    if (xhr.readyState === 4) {
                        console.log('📥 AJAX Response:', xhr._method, xhr._url, xhr.status, xhr.responseText.substring(0, 200));
                        window.ajaxResponses.push({
                            method: xhr._method,
                            url: xhr._url,
                            status: xhr.status,
                            response: xhr.responseText,
                            timestamp: Date.now()
                        });
                    }
                });
                return originalSend.apply(this, arguments);
            };
        })();
        
        // Intercepter fetch
        (function() {
            var originalFetch = window.fetch;
            window.fetch = function() {
                console.log('🌐 Fetch Request:', arguments[0], arguments[1]);
                window.ajaxRequests.push({method: 'FETCH', url: arguments[0], timestamp: Date.now()});
                
                return originalFetch.apply(this, arguments).then(function(response) {
                    response.clone().text().then(function(text) {
                        console.log('📥 Fetch Response:', arguments[0], response.status, text.substring(0, 200));
                        window.ajaxResponses.push({
                            method: 'FETCH',
                            url: arguments[0],
                            status: response.status,
                            response: text,
                            timestamp: Date.now()
                        });
                    });
                    return response;
                });
            };
        })();
        
        console.log('✅ AJAX interception enabled');
        """
        
        # Setup oneblock.fr
        logger.info("🌐 Accès à https://oneblock.fr/vote")
        driver.get("https://oneblock.fr/vote")
        time.sleep(2)
        
        # Injecter le script d'interception
        driver.execute_script(ajax_intercept_script)
        logger.info("✅ Script d'interception AJAX injecté")
        
        # Setup du vote
        logger.info("📝 Setup du vote...")
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='pseudo'], input[name*='username'], input[id*='username']"))
        )
        username_input.clear()
        username_input.send_keys("TestUser123")
        
        # Cliquer ENVOYER
        envoyer_button = None
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if btn.text.strip() == "ENVOYER" and btn.is_displayed():
                envoyer_button = btn
                break
        
        if envoyer_button:
            # Vider les logs avant le clic ENVOYER
            driver.execute_script("window.ajaxRequests = []; window.ajaxResponses = [];")
            driver.execute_script("arguments[0].click();", envoyer_button)
            logger.info("✅ ENVOYER cliqué")
            time.sleep(5)
            
            # Vérifier les requêtes après ENVOYER
            envoyer_requests = driver.execute_script("return window.ajaxRequests;")
            envoyer_responses = driver.execute_script("return window.ajaxResponses;")
            
            logger.info(f"📊 Requêtes après ENVOYER: {len(envoyer_requests)}")
            for req in envoyer_requests:
                logger.info(f"   {req['method']} {req['url']}")
            
            logger.info(f"📊 Réponses après ENVOYER: {len(envoyer_responses)}")
            for resp in envoyer_responses:
                logger.info(f"   {resp['method']} {resp['url']} -> {resp['status']}")
                if 'vote' in resp['url'].lower() or 'serveur' in resp['url'].lower():
                    logger.info(f"      🎯 Réponse intéressante: {resp['response'][:200]}...")
        
        # Trouver le bouton "Votez maintenant"
        logger.info("🔍 Recherche du bouton Votez maintenant...")
        vote_buttons = []
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        
        for btn in all_buttons:
            text = btn.text.strip()
            if "Votez maintenant" in text and "SITE" in text and btn.is_displayed():
                vote_buttons.append(btn)
                logger.info(f"   Bouton trouvé: '{text}'")
        
        if not vote_buttons:
            logger.error("❌ Aucun bouton 'Votez maintenant' trouvé")
            return
        
        vote_button = vote_buttons[0]
        
        # Vider les logs avant le clic sur vote
        logger.info("\n🖱️ CLIC SUR VOTEZ MAINTENANT AVEC INTERCEPTION AJAX:")
        driver.execute_script("window.ajaxRequests = []; window.ajaxResponses = [];")
        
        # Cliquer sur le bouton
        logger.info("   Clic sur le bouton...")
        vote_button.click()
        
        # Surveiller les requêtes AJAX pendant 15 secondes
        for wait_time in range(1, 16):
            time.sleep(1)
            
            # Récupérer les nouvelles requêtes
            current_requests = driver.execute_script("return window.ajaxRequests;")
            current_responses = driver.execute_script("return window.ajaxResponses;")
            
            # Afficher les nouvelles requêtes
            if len(current_requests) > 0:
                logger.info(f"   📤 Nouvelles requêtes (t={wait_time}s): {len(current_requests)}")
                for req in current_requests[-3:]:  # Dernières 3
                    logger.info(f"      {req['method']} {req['url']}")
            
            # Afficher les nouvelles réponses
            if len(current_responses) > 0:
                logger.info(f"   📥 Nouvelles réponses (t={wait_time}s): {len(current_responses)}")
                for resp in current_responses[-3:]:  # Dernières 3
                    logger.info(f"      {resp['method']} {resp['url']} -> Status: {resp['status']}")
                    
                    # Analyser les réponses qui contiennent des URLs de vote
                    response_text = resp['response']
                    if ('serveur-prive.net' in response_text or 
                        'vote' in response_text.lower() or 
                        'redirect' in response_text.lower() or
                        'url' in response_text.lower()):
                        
                        logger.info(f"      🎯 RÉPONSE IMPORTANTE:")
                        logger.info(f"         Contenu: {response_text[:300]}...")
                        
                        # Essayer de parser comme JSON
                        try:
                            json_data = json.loads(response_text)
                            logger.info(f"         📋 JSON parsé: {json_data}")
                            
                            # Chercher des URLs dans le JSON
                            def find_urls_in_json(obj, path=""):
                                urls = []
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if isinstance(value, str) and ('http' in value or 'serveur-prive' in value):
                                            urls.append((f"{path}.{key}", value))
                                        elif isinstance(value, (dict, list)):
                                            urls.extend(find_urls_in_json(value, f"{path}.{key}"))
                                elif isinstance(obj, list):
                                    for i, item in enumerate(obj):
                                        if isinstance(item, (dict, list)):
                                            urls.extend(find_urls_in_json(item, f"{path}[{i}]"))
                                return urls
                            
                            urls = find_urls_in_json(json_data)
                            if urls:
                                logger.info(f"         🎯 URLs trouvées dans JSON:")
                                for path, url in urls:
                                    logger.info(f"            {path}: {url}")
                                    
                        except json.JSONDecodeError:
                            # Pas du JSON, chercher des URLs dans le texte
                            import re
                            urls = re.findall(r'https?://[^\s<>"]+', response_text)
                            if urls:
                                logger.info(f"         🎯 URLs trouvées dans texte:")
                                for url in urls:
                                    logger.info(f"            {url}")
            
            # Vérifier l'URL de la page
            current_url = driver.current_url
            if current_url != "https://oneblock.fr/vote":
                logger.info(f"   🎉 REDIRECTION DÉTECTÉE vers: {current_url}")
                break
            
            # Vérifier si le bouton a changé
            try:
                button_text = vote_button.text.strip()
                if "Veuillez patienter" in button_text and wait_time <= 3:
                    logger.info(f"   ⏳ Bouton en attente: '{button_text}'")
            except:
                pass
        
        # Résumé final
        final_requests = driver.execute_script("return window.ajaxRequests;")
        final_responses = driver.execute_script("return window.ajaxResponses;")
        
        logger.info(f"\n📊 RÉSUMÉ FINAL:")
        logger.info(f"   Total requêtes: {len(final_requests)}")
        logger.info(f"   Total réponses: {len(final_responses)}")
        logger.info(f"   URL finale: {driver.current_url}")
        
        if driver.current_url == "https://oneblock.fr/vote":
            logger.warning("   ⚠️ Aucune redirection - le JavaScript n'a peut-être pas terminé")
            
            # Attendre encore un peu au cas où
            logger.info("   ⏳ Attente supplémentaire de 10s...")
            time.sleep(10)
            final_url = driver.current_url
            logger.info(f"   URL après attente: {final_url}")
        
        input("\n🔍 Appuyez sur Entrée pour terminer...")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_ajax_intercept()