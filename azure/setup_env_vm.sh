#!/bin/bash

# Script pour configurer le .env sur la VM
# À exécuter sur la VM après le déploiement

echo "🔧 Configuration du fichier .env"
echo "================================"

cd /home/azureuser/ScriptVote

# Demander la clé API 2Captcha
read -p "Entrez votre clé API 2Captcha: " API_KEY
read -p "Entrez le username pour voter (par défaut: zCapsLock): " USERNAME
USERNAME=${USERNAME:-zCapsLock}

# Créer le fichier .env
cat > .env <<EOF
TWOCAPTCHA_API_KEY=$API_KEY
username=$USERNAME
EOF

chmod 600 .env

echo "✅ Fichier .env créé avec succès!"
echo ""
echo "Test du script:"
echo "==============="

source venv/bin/activate
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
api = os.getenv('TWOCAPTCHA_API_KEY')
user = os.getenv('username')
if api:
    print(f'✅ API Key configurée: {api[:10]}...')
    print(f'✅ Username: {user}')
else:
    print('❌ API Key non trouvée!')
"

echo ""
echo "Pour tester le vote:"
echo "python3 mtcaptcha_seleniumbase.py --headless"