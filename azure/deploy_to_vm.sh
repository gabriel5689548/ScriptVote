#!/bin/bash

# Script de déploiement sur la VM Azure
# À exécuter depuis votre machine locale

VM_IP="52.224.120.195"
VM_USER="azureuser"
BRANCH="Test2"

echo "🚀 Déploiement sur la VM Azure"
echo "================================"
echo "VM: $VM_USER@$VM_IP"
echo "Branche: $BRANCH"
echo ""

# Commandes à exécuter sur la VM
COMMANDS='
cd /home/azureuser

# Clone ou mise à jour du repo
if [ -d "ScriptVote/.git" ]; then
    echo "📂 Mise à jour du projet..."
    cd ScriptVote
    git fetch origin
    git checkout Test2
    git pull origin Test2
else
    echo "📥 Clonage du projet..."
    rm -rf ScriptVote
    git clone -b Test2 https://github.com/gabriel5689548/ScriptVote.git
    cd ScriptVote
fi

# Création du venv si nécessaire
if [ ! -d "venv" ]; then
    echo "🐍 Création de l environnement virtuel..."
    python3 -m venv venv
fi

# Installation des dépendances
echo "📦 Installation des dépendances..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configuration du .env si nécessaire
if [ ! -f ".env" ]; then
    echo "⚠️ Créez le fichier .env avec:"
    echo "TWOCAPTCHA_API_KEY=votre_clé_2captcha"
    echo "username=zCapsLock"
fi

# Test rapide
echo "🧪 Test de l installation..."
python3 -c "import seleniumbase; print(\"✅ SeleniumBase installé\")"

echo "✨ Déploiement terminé!"
echo ""
echo "Pour tester le vote:"
echo "cd /home/azureuser/ScriptVote"
echo "source venv/bin/activate"
echo "python3 mtcaptcha_seleniumbase.py --headless"
'

echo "Connexion à la VM et exécution des commandes..."
echo "Vous allez devoir entrer votre mot de passe:"
ssh $VM_USER@$VM_IP "$COMMANDS"