#!/usr/bin/env python3

import time
from seleniumbase import SB

print("🚀 Test de détection du cooldown en headless")

with SB(uc=True, headless=False) as sb:
    print("📍 Accès à oneblock.fr/vote...")
    sb.open("https://oneblock.fr/vote")
    time.sleep(5)
    
    print("📝 Saisie du username...")
    try:
        sb.type("input[placeholder*='pseudo' i]", "zCapsLock")
        print("✅ Username saisi")
    except Exception as e:
        print(f"❌ Erreur username: {e}")
    
    time.sleep(2)
    
    print("🔍 Recherche du bouton ENVOYER...")
    buttons = sb.find_elements("button")
    print(f"Nombre de boutons: {len(buttons)}")
    
    for btn in buttons:
        if "ENVOYER" in btn.text.upper():
            print(f"✅ Bouton ENVOYER trouvé: '{btn.text}'")
            sb.execute_script("arguments[0].click();", btn)
            print("✅ Clic effectué")
            break
    
    time.sleep(5)
    
    print("\n🔍 Recherche du bouton SITE N°1...")
    buttons = sb.find_elements("button")
    for btn in buttons:
        text = btn.text.strip()
        if "SITE N°1" in text:
            print(f"📋 Bouton SITE N°1 trouvé: '{text}'")
            
            # Vérifier le cooldown
            text_lower = text.lower()
            if "cooldown" in text_lower or "attendre" in text_lower or "prochain" in text_lower:
                print("⏰ COOLDOWN DÉTECTÉ!")
                print("✅ Le vote précédent a bien fonctionné!")
            else:
                print("❌ Pas de cooldown - bouton cliquable")
            break
    else:
        print("❌ Bouton SITE N°1 non trouvé")
    
    # Vérifier aussi le texte de la page
    page_text = sb.get_text("body").lower()
    if "cooldown" in page_text or "attendre" in page_text:
        print("⏰ COOLDOWN trouvé dans la page")
    
    print("\nFin du test.")