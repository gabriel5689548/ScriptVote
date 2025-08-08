#!/usr/bin/env python3

import time
import os
import re
from dotenv import load_dotenv
from seleniumbase import SB
import requests

load_dotenv()
api_key = os.getenv('TWOCAPTCHA_API_KEY')

print("🚀 Debug de la soumission du vote après captcha")

with SB(uc=True, headless=True, xvfb=True) as sb:
    # Aller directement à serveur-prive.net pour tester
    print("📍 Accès direct à serveur-prive.net...")
    sb.open("https://serveur-prive.net/minecraft/oneblockbyrivrs/vote")
    time.sleep(5)
    
    # Gérer Cloudflare si nécessaire
    page_source = sb.get_page_source().lower()
    if "cloudflare" in page_source:
        print("⏳ Cloudflare détecté, attente...")
        time.sleep(10)
    
    # Chercher le formulaire et ses éléments
    print("\n🔍 Analyse du formulaire...")
    
    # Chercher tous les formulaires
    forms = sb.find_elements("form")
    print(f"Nombre de formulaires: {len(forms)}")
    
    if forms:
        form = forms[0]
        form_action = form.get_attribute("action")
        form_method = form.get_attribute("method")
        print(f"Form action: {form_action}")
        print(f"Form method: {form_method}")
    
    # Chercher les inputs
    inputs = sb.find_elements("input")
    print(f"\nNombre d'inputs: {len(inputs)}")
    for inp in inputs:
        input_type = inp.get_attribute("type")
        input_name = inp.get_attribute("name")
        input_value = inp.get_attribute("value")
        if input_type != "hidden" or "captcha" in str(input_name).lower():
            print(f"  - {input_type} | name={input_name} | value={input_value[:20] if input_value else 'None'}")
    
    # Chercher le username field
    print("\n📝 Remplissage du username...")
    username_filled = False
    for inp in inputs:
        input_name = inp.get_attribute("name") or ""
        input_type = inp.get_attribute("type") or ""
        if "username" in input_name.lower() or (input_type == "text" and inp.is_displayed()):
            try:
                inp.clear()
                inp.send_keys("zCapsLock")
                print(f"✅ Username saisi dans: {input_name}")
                username_filled = True
                break
            except:
                pass
    
    if not username_filled:
        print("❌ Impossible de remplir le username")
    
    # Chercher la sitekey
    print("\n🔑 Recherche de la sitekey...")
    page_source = sb.get_page_source()
    sitekey_match = re.search(r'(MTPublic-[a-zA-Z0-9]+)', page_source)
    
    if not sitekey_match:
        print("❌ Sitekey non trouvée")
        exit(1)
    
    sitekey = sitekey_match.group(1)
    print(f"✅ Sitekey: {sitekey}")
    
    # Résoudre avec 2Captcha
    print("\n📤 Résolution du captcha...")
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
        print(f"❌ Erreur: {result}")
        exit(1)
    
    captcha_id = result['request']
    print(f"Captcha ID: {captcha_id}")
    
    # Attendre la solution
    for i in range(30):
        time.sleep(10)
        check_response = requests.get(
            f'http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1'
        )
        check_result = check_response.json()
        
        if check_result['status'] == 1:
            solution = check_result['request']
            print(f"✅ Solution reçue: {solution[:50]}...")
            break
        print(f"  {i+1}/30 - Attente...")
    else:
        print("❌ Timeout")
        exit(1)
    
    # Injecter la solution de différentes manières
    print("\n💉 Injection du token...")
    
    # Méthode 1: Chercher un input existant
    token_input = None
    for inp in sb.find_elements("input"):
        input_name = inp.get_attribute("name") or ""
        if "mtcaptcha" in input_name.lower() or "token" in input_name.lower():
            token_input = inp
            print(f"✅ Input trouvé: {input_name}")
            break
    
    if token_input:
        sb.execute_script(f"arguments[0].value = '{solution}';", token_input)
    else:
        # Méthode 2: Créer l'input
        print("📝 Création de l'input mtcaptcha-verifiedtoken...")
        sb.execute_script(f"""
            var input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'mtcaptcha-verifiedtoken';
            input.value = '{solution}';
            document.forms[0].appendChild(input);
            console.log('Token injecté:', input.value.substring(0, 50));
        """)
    
    # Vérifier que le token est bien injecté
    token_check = sb.execute_script("""
        var inputs = document.querySelectorAll('input[name*="mtcaptcha"]');
        if (inputs.length > 0) {
            return inputs[0].value.substring(0, 50);
        }
        return null;
    """)
    print(f"Token vérifié: {token_check}...")
    
    # Chercher et cliquer sur le bouton de vote
    print("\n🎯 Recherche du bouton de soumission...")
    
    buttons = sb.find_elements("button")
    print(f"Nombre de boutons: {len(buttons)}")
    
    vote_button = None
    for btn in buttons:
        btn_text = btn.text.lower()
        btn_type = btn.get_attribute("type")
        btn_id = btn.get_attribute("id")
        
        print(f"  - '{btn_text}' | type={btn_type} | id={btn_id}")
        
        if "vote" in btn_text or btn_type == "submit" or btn_id == "voteBtn":
            vote_button = btn
            print(f"✅ Bouton de vote trouvé!")
            break
    
    if vote_button:
        print("🖱️ Clic sur le bouton...")
        try:
            vote_button.click()
        except:
            sb.execute_script("arguments[0].click();", vote_button)
        print("✅ Clic effectué")
    else:
        print("⚠️ Pas de bouton, soumission du formulaire...")
        sb.execute_script("document.forms[0].submit();")
    
    # Attendre et vérifier le résultat
    time.sleep(5)
    
    print(f"\n📍 URL finale: {sb.get_current_url()}")
    
    # Retourner sur oneblock pour vérifier le cooldown
    print("\n🔄 Retour sur oneblock.fr...")
    sb.open("https://oneblock.fr/vote")
    time.sleep(3)
    
    # Remplir le username
    sb.type("input[placeholder*='pseudo' i]", "zCapsLock")
    time.sleep(1)
    
    # Cliquer ENVOYER
    buttons = sb.find_elements("button")
    for btn in buttons:
        if "ENVOYER" in btn.text.upper():
            sb.execute_script("arguments[0].click();", btn)
            break
    
    time.sleep(3)
    
    # Vérifier le cooldown
    page_text = sb.get_text("body")
    if "cooldown" in page_text.lower() or "attendre" in page_text.lower() or "wait" in page_text.lower():
        print("🎉 SUCCÈS! Cooldown détecté = vote validé!")
    else:
        print("❌ Pas de cooldown = vote non validé")
        
        # Vérifier l'état des boutons
        buttons = sb.find_elements("button")
        for btn in buttons:
            if "SITE N°1" in btn.text:
                if "Votez maintenant" in btn.text:
                    print("  ❌ Bouton toujours actif: vote non passé")
                else:
                    print(f"  État du bouton: {btn.text}")