#!/usr/bin/env python3

from seleniumbase import SB
import time

print("🚀 Test du clic sur SITE N°1...")

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
            sb.execute_script("arguments[0].click();", btn)
            print("✅ Clic sur ENVOYER")
            break
    
    time.sleep(3)
    
    # Chercher et cliquer sur SITE N°1
    print("\n🔍 Recherche du bouton SITE N°1...")
    buttons = sb.find_elements("button")
    for btn in buttons:
        if "SITE N°1" in btn.text:
            print(f"✅ Trouvé: {btn.text.replace(chr(10), ' ')}")
            
            # Mémoriser les onglets
            initial_tabs = len(sb.driver.window_handles)
            current_handle = sb.driver.current_window_handle
            
            # Cliquer
            btn.click()
            print("✅ Clic sur SITE N°1")
            time.sleep(5)
            
            # Vérifier si nouvel onglet
            if len(sb.driver.window_handles) > initial_tabs:
                print("📑 Nouvel onglet ouvert")
                for handle in sb.driver.window_handles:
                    if handle != current_handle:
                        sb.switch_to_window(handle)
                        print(f"📍 URL nouvel onglet: {sb.get_current_url()}")
                        
                        # Analyser la page
                        time.sleep(3)
                        page_source = sb.get_page_source()
                        
                        if "mtcaptcha" in page_source.lower():
                            print("✅ MTCaptcha détecté!")
                        
                        if "serveur-prive.net" in sb.get_current_url():
                            print("✅ Sur serveur-prive.net")
                            
                        # Chercher la sitekey
                        import re
                        sitekey_match = re.search(r'(MTPublic-[a-zA-Z0-9]+)', page_source)
                        if sitekey_match:
                            print(f"🔑 Sitekey trouvée: {sitekey_match.group(1)}")
                        
                        break
            else:
                print(f"📍 Même onglet, URL: {sb.get_current_url()}")
            
            break
    
    input("\nAppuyez sur Entrée pour fermer...")