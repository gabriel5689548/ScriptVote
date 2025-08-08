#!/usr/bin/env python3

import time
import os
from dotenv import load_dotenv
from seleniumbase import SB
import requests
import re

load_dotenv()

api_key = os.getenv('api_key') or os.getenv('TWOCAPTCHA_API_KEY')
if not api_key:
    print("❌ Clé API manquante dans .env")
    exit(1)

print("🚀 Test du vote complet avec résolution MTCaptcha")
print(f"🔑 API Key: {api_key[:10]}...")

with SB(uc=True, headless=False) as sb:
    # Étape 1: Accès à oneblock.fr
    print("\n📍 Étape 1: Accès à oneblock.fr/vote")
    sb.open("https://oneblock.fr/vote")
    time.sleep(3)
    
    # Gérer cookies
    try:
        if sb.is_element_visible("button:contains('J'accepte')"):
            sb.click("button:contains('J'accepte')")
            print("✅ Cookies acceptés")
    except:
        pass
    
    # Étape 2: Remplir username
    print("\n📍 Étape 2: Saisie du username")
    sb.type("input[placeholder*='pseudo' i]", "zCapsLock")
    print("✅ Username saisi")
    time.sleep(2)
    
    # Étape 3: Cliquer ENVOYER
    print("\n📍 Étape 3: Clic sur ENVOYER")
    buttons = sb.find_elements("button")
    for btn in buttons:
        if "ENVOYER" in btn.text.upper():
            sb.execute_script("arguments[0].click();", btn)
            print("✅ Clic sur ENVOYER")
            break
    
    time.sleep(5)
    
    # Étape 4: Cliquer sur SITE N°1
    print("\n📍 Étape 4: Clic sur SITE N°1")
    buttons = sb.find_elements("button")
    site1_found = False
    
    for btn in buttons:
        if "SITE N°1" in btn.text:
            print(f"✅ Trouvé: {btn.text.replace(chr(10), ' ')}")
            
            initial_tabs = len(sb.driver.window_handles)
            current_handle = sb.driver.current_window_handle
            
            btn.click()
            print("✅ Clic effectué")
            time.sleep(5)
            
            # Gérer nouvel onglet
            if len(sb.driver.window_handles) > initial_tabs:
                print("📑 Nouvel onglet détecté")
                for handle in sb.driver.window_handles:
                    if handle != current_handle:
                        sb.switch_to_window(handle)
                        break
            
            site1_found = True
            break
    
    if not site1_found:
        print("❌ SITE N°1 non trouvé")
        exit(1)
    
    # Étape 5: Gérer serveur-prive.net
    print(f"\n📍 Étape 5: Page actuelle: {sb.get_current_url()}")
    
    # Attendre Cloudflare si nécessaire
    time.sleep(5)
    
    # Étape 6: Chercher MTCaptcha
    print("\n📍 Étape 6: Recherche du MTCaptcha")
    page_source = sb.get_page_source()
    
    sitekey = None
    sitekey_match = re.search(r'(MTPublic-[a-zA-Z0-9]+)', page_source)
    if sitekey_match:
        sitekey = sitekey_match.group(1)
        print(f"✅ Sitekey trouvée: {sitekey}")
    else:
        print("❌ Sitekey non trouvée")
        # Sauvegarder la page pour debug
        with open("debug_page.html", "w") as f:
            f.write(page_source)
        print("📄 Page sauvegardée dans debug_page.html")
        exit(1)
    
    # Étape 7: Résoudre avec 2Captcha
    print("\n📍 Étape 7: Résolution avec 2Captcha")
    print("📤 Envoi à 2Captcha...")
    
    submit_data = {
        'key': api_key,
        'method': 'mt_captcha',
        'sitekey': sitekey,
        'pageurl': sb.get_current_url(),
        'json': 1
    }
    
    response = requests.post('http://2captcha.com/in.php', data=submit_data)
    result = response.json()
    
    if result['status'] != 1:
        print(f"❌ Erreur 2Captcha: {result}")
        exit(1)
    
    captcha_id = result['request']
    print(f"🎯 Captcha ID: {captcha_id}")
    
    # Attendre la résolution
    print("⏳ Attente de la résolution...")
    for i in range(30):
        time.sleep(10)
        check_response = requests.get(
            f'http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1'
        )
        check_result = check_response.json()
        
        if check_result['status'] == 1:
            solution = check_result['request']
            print(f"✅ Solution reçue!")
            break
        else:
            print(f"  {i+1}/30 - En attente...")
    else:
        print("❌ Timeout résolution")
        exit(1)
    
    # Étape 8: Injecter la solution
    print("\n📍 Étape 8: Injection de la solution")
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
    print("✅ Token injecté")
    
    # Étape 9: Soumettre le vote
    print("\n📍 Étape 9: Soumission du vote")
    
    # Chercher le bouton de vote
    vote_clicked = False
    for selector in ["#voteBtn", "button[type='submit']", "input[type='submit']"]:
        if sb.is_element_present(selector):
            sb.click(selector)
            print(f"✅ Clic sur {selector}")
            vote_clicked = True
            break
    
    if not vote_clicked:
        sb.execute_script("document.forms[0].submit();")
        print("✅ Formulaire soumis via JS")
    
    time.sleep(5)
    
    # Étape 10: Vérifier le résultat
    print("\n📍 Étape 10: Vérification du résultat")
    page_text = sb.get_text("body").lower()
    
    if "succès" in page_text or "success" in page_text or "merci" in page_text:
        print("🎉 VOTE RÉUSSI!")
    elif "déjà voté" in page_text:
        print("⚠️ Déjà voté")
    else:
        print("❓ Résultat incertain")
    
    input("\nAppuyez sur Entrée pour fermer...")