#!/usr/bin/env python3

import time
import sys
from seleniumbase import SB

print("🚀 Debug du blocage en mode headless")
print(f"Platform: {sys.platform}")

# Configuration pour headless
sb_options = {
    'uc': True,
    'headless': True,
    'disable_csp': True,
    'disable_ws': True,
    'page_load_strategy': 'eager',
    'block_images': False,
}

# Sur Linux, utiliser xvfb
if sys.platform.startswith('linux'):
    sb_options['xvfb'] = True
    print("✅ Mode xvfb activé pour Linux")

print("📍 Création du driver...")
try:
    with SB(**sb_options) as sb:
        print("✅ Driver créé avec succès")
        
        print("📍 Tentative d'accès à oneblock.fr...")
        # Utiliser open normal au lieu de uc_open_with_reconnect
        sb.open("https://oneblock.fr/vote")
        print("✅ Page chargée")
        
        # Attendre un peu
        time.sleep(3)
        
        # Vérifier le titre
        title = sb.get_title()
        print(f"📄 Titre de la page: {title}")
        
        # Vérifier si on peut trouver des éléments
        print("🔍 Recherche d'éléments...")
        
        # Chercher le champ username
        try:
            if sb.is_element_present("input[placeholder*='pseudo' i]", timeout=5):
                print("✅ Champ username trouvé")
                sb.type("input[placeholder*='pseudo' i]", "zCapsLock")
                print("✅ Username saisi")
            else:
                print("❌ Champ username non trouvé")
        except Exception as e:
            print(f"❌ Erreur username: {e}")
        
        # Chercher les boutons
        try:
            buttons = sb.find_elements("button")
            print(f"📋 {len(buttons)} boutons trouvés")
            
            for btn in buttons[:3]:  # Afficher les 3 premiers
                print(f"  - Bouton: {btn.text[:30] if btn.text else 'Pas de texte'}")
        except Exception as e:
            print(f"❌ Erreur boutons: {e}")
        
        # Essayer de prendre un screenshot
        try:
            sb.save_screenshot("debug_headless.png")
            print("📸 Screenshot sauvegardé: debug_headless.png")
        except:
            pass
        
        print("✅ Test terminé sans blocage")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()