#!/usr/bin/env python3

import os
from dotenv import load_dotenv

load_dotenv()

print("Test rapide...")
print(f"API Key: {os.getenv('TWOCAPTCHA_API_KEY', 'NON TROUVÉE')[:10]}...")

from mtcaptcha_seleniumbase import MTCaptchaVoterSeleniumBase

print("Création de l'instance...")
voter = MTCaptchaVoterSeleniumBase(headless=False, timeout=30)

print("Lancement du vote...")
result = voter.vote_oneblock_site1()

print(f"Résultat: {result}")