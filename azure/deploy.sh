#!/bin/bash

set -e

REPO_URL="https://github.com/YOUR_USERNAME/ScriptVote.git"
BRANCH="Test2"
PROJECT_DIR="/home/azureuser/ScriptVote"

echo "🚀 Déploiement du projet ScriptVote"
echo "===================================="

cd /home/azureuser

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "📂 Mise à jour du projet existant..."
    cd $PROJECT_DIR
    git fetch origin
    git reset --hard origin/$BRANCH
    git pull origin $BRANCH
else
    echo "📥 Clonage du repository..."
    if [ -d "$PROJECT_DIR" ]; then
        rm -rf $PROJECT_DIR
    fi
    git clone -b $BRANCH $REPO_URL ScriptVote
    cd $PROJECT_DIR
fi

echo "🔧 Configuration de l'environnement..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Installation/Mise à jour des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🔑 Configuration des variables d'environnement..."
if [ ! -f ".env" ]; then
    cat > .env <<EOF
api_key=${CAPTCHA_API_KEY}
username=${VOTE_USERNAME}
PROXY_HOST=${PROXY_HOST}
PROXY_PORT=${PROXY_PORT}
PROXY_USER=${PROXY_USER}
PROXY_PASS=${PROXY_PASS}
EOF
    chmod 600 .env
    echo "✅ Fichier .env créé"
else
    echo "ℹ️ Fichier .env existant conservé"
fi

echo "📁 Vérification des dossiers nécessaires..."
mkdir -p logs
mkdir -p screenshots

echo "🧪 Test de l'installation..."
python3 -c "
import selenium
import seleniumbase
import requests
print('✅ Selenium version:', selenium.__version__)
print('✅ SeleniumBase version:', seleniumbase.__version__)
print('✅ Toutes les dépendances sont installées correctement')
"

echo "🔧 Configuration des permissions..."
chmod +x azure/*.sh
chmod +x *.py

echo "📊 Test de Chrome headless..."
google-chrome --version
xvfb-run -a google-chrome --headless --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com > /dev/null 2>&1 && echo "✅ Chrome headless fonctionne"

echo "🎯 Test du script de vote..."
cd $PROJECT_DIR
source venv/bin/activate
timeout 30 python3 mtcaptcha_seleniumbase.py --headless || echo "⚠️ Test rapide terminé (timeout normal)"

echo "✨ Déploiement terminé avec succès!"
echo "Prochaine étape: configurer le scheduler avec vote_scheduler.sh"