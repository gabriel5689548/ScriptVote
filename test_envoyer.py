#!/usr/bin/env python3

from seleniumbase import SB
import time

print("🚀 Test du bouton ENVOYER...")

with SB(uc=True, headless=False) as sb:
    print("📍 Accès à oneblock.fr/vote...")
    sb.open("https://oneblock.fr/vote")
    time.sleep(3)
    
    # Accepter cookies si présents
    try:
        if sb.is_element_visible("button:contains('J'accepte')"):
            sb.click("button:contains('J'accepte')")
            print("✅ Cookies acceptés")
            time.sleep(1)
    except:
        pass
    
    # Remplir le champ username avec différentes méthodes
    print("\n🔍 Remplissage du champ username...")
    
    # Méthode 1: Par placeholder
    if sb.is_element_present("input[placeholder*='pseudo' i]"):
        sb.type("input[placeholder*='pseudo' i]", "zCapsLock")
        print("✅ Username saisi (par placeholder)")
    # Méthode 2: Par name
    elif sb.is_element_present("input[name='username']"):
        sb.type("input[name='username']", "zCapsLock")
        print("✅ Username saisi (par name)")
    # Méthode 3: Premier input visible
    elif sb.is_element_present("input[type='text']"):
        sb.type("input[type='text']", "zCapsLock")
        print("✅ Username saisi (par type)")
    else:
        # Méthode 4: JavaScript
        sb.execute_script("""
            var inputs = document.querySelectorAll('input');
            for(var inp of inputs) {
                if(inp.type !== 'hidden') {
                    inp.value = 'zCapsLock';
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                    break;
                }
            }
        """)
        print("✅ Username saisi (par JavaScript)")
    
    time.sleep(2)
    
    # Rechercher le bouton ENVOYER avec toutes les méthodes possibles
    print("\n🔍 Recherche du bouton ENVOYER...")
    
    # Lister tous les boutons d'abord
    buttons = sb.find_elements("button")
    print(f"Nombre de boutons trouvés: {len(buttons)}")
    for i, btn in enumerate(buttons):
        text = btn.text.strip()
        classes = btn.get_attribute('class')
        visible = btn.is_displayed()
        print(f"  Bouton {i}: '{text}' | Classes: {classes} | Visible: {visible}")
    
    # Essayer de cliquer sur ENVOYER
    print("\n🎯 Tentative de clic sur ENVOYER...")
    
    # Méthode 1: Recherche case-insensitive
    for btn in buttons:
        if "ENVOYER" in btn.text.upper() and btn.is_displayed():
            print(f"  → Trouvé: '{btn.text}'")
            try:
                # Scroll vers le bouton
                sb.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(1)
                # Clic normal
                btn.click()
                print("✅ Clic réussi (méthode normale)")
                break
            except Exception as e:
                print(f"❌ Clic normal échoué: {e}")
                # Essayer JavaScript
                try:
                    sb.execute_script("arguments[0].click();", btn)
                    print("✅ Clic réussi (JavaScript)")
                    break
                except Exception as e2:
                    print(f"❌ Clic JavaScript échoué: {e2}")
    
    time.sleep(3)
    
    # Vérifier si on est passé à l'étape suivante
    print("\n📍 Vérification après clic...")
    print(f"URL: {sb.get_current_url()}")
    
    # Chercher les boutons SITE
    if sb.is_element_present("button"):
        buttons = sb.find_elements("button")
        for btn in buttons:
            if "SITE" in btn.text:
                print(f"✅ Bouton de vote trouvé: {btn.text}")
    
    time.sleep(10)  # Garder ouvert pour observation