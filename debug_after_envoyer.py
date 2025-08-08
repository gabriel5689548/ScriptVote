#\!/usr/bin/env python3

from seleniumbase import SB
import time

print("🚀 Test après clic ENVOYER...")

with SB(uc=True, headless=False) as sb:
    print("📍 Accès à oneblock.fr/vote...")
    sb.open("https://oneblock.fr/vote")
    time.sleep(3)
    
    # Accepter cookies
    try:
        if sb.is_element_visible("button:contains('J'accepte')"):
            sb.click("button:contains('J'accepte')")
            print("✅ Cookies acceptés")
            time.sleep(1)
    except:
        pass
    
    # Remplir username
    sb.type("input[placeholder*='pseudo' i]", "zCapsLock")
    print("✅ Username saisi")
    time.sleep(2)
    
    # Cliquer ENVOYER
    buttons = sb.find_elements("button")
    for btn in buttons:
        if "ENVOYER" in btn.text.upper():
            sb.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(1)
            sb.execute_script("arguments[0].click();", btn)
            print("✅ Clic sur ENVOYER")
            break
    
    # Attendre et observer
    print("\n⏳ Attente après clic...")
    for i in range(10):
        time.sleep(1)
        print(f"  {i+1}s - URL: {sb.get_current_url()}")
        
        # Vérifier si des boutons SITE apparaissent
        try:
            buttons = sb.find_elements("button")
            site_buttons = [b for b in buttons if "SITE" in b.text]
            if site_buttons:
                print(f"  ✅ {len(site_buttons)} boutons SITE trouvés\!")
                for btn in site_buttons:
                    print(f"    - {btn.text.replace(chr(10), ' ')}")
                break
        except:
            pass
    
    # Si toujours pas de boutons SITE
    if not site_buttons:
        print("\n❌ Aucun bouton SITE trouvé après 10 secondes")
        
    input("\nAppuyez sur Entrée pour fermer...")
