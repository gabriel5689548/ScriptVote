#!/usr/bin/env python3

from seleniumbase import SB
import time

print("🚀 Test simple de navigation...")

with SB(uc=True, headless=False) as sb:
    print("📍 Accès à oneblock.fr/vote...")
    sb.open("https://oneblock.fr/vote")
    time.sleep(3)
    
    print("📸 Screenshot initial...")
    sb.save_screenshot("screenshots/initial.png")
    
    # Accepter cookies si présents
    try:
        if sb.is_element_visible("button:contains('J'accepte')"):
            sb.click("button:contains('J'accepte')")
            print("✅ Cookies acceptés")
            time.sleep(1)
    except:
        pass
    
    # Chercher le champ username
    print("\n🔍 Recherche du champ username...")
    if sb.is_element_present("input[type='text']"):
        sb.type("input[type='text']", "zCapsLock")
        print("✅ Username saisi")
    elif sb.is_element_present("input:not([type='hidden'])"):
        sb.type("input:not([type='hidden']):first", "zCapsLock")
        print("✅ Username saisi (méthode 2)")
    
    time.sleep(2)
    
    # Chercher le bouton ENVOYER  
    print("\n🔍 Recherche du bouton ENVOYER...")
    
    # Méthode 1: Scroll down pour voir si le bouton est plus bas
    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    
    if sb.is_element_visible("button:contains('ENVOYER')"):
        print("✅ Bouton ENVOYER trouvé après scroll")
        sb.click("button:contains('ENVOYER')")
        time.sleep(3)
    else:
        # Méthode 2: Cliquer par JavaScript
        result = sb.execute_script("""
            var buttons = document.querySelectorAll('button');
            for(var btn of buttons) {
                if(btn.textContent.includes('ENVOYER')) {
                    btn.click();
                    return 'clicked';
                }
            }
            return 'not found';
        """)
        print(f"JavaScript result: {result}")
    
    time.sleep(3)
    
    # Vérifier si on voit les boutons de vote
    print("\n🔍 Recherche des boutons de vote...")
    if sb.is_element_visible("button:contains('SITE')"):
        buttons = sb.find_elements("button:contains('SITE')")
        for btn in buttons:
            print(f"  → Trouvé: {btn.text}")
    
    print("\n📍 URL finale:", sb.get_current_url())
    
    input("\nAppuyez sur Entrée pour fermer...")