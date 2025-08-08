#!/bin/bash

# Script de déploiement rapide avec rsync vers la VM Azure

VM_IP="52.224.120.195"
VM_USER="azureuser"
REMOTE_DIR="/home/azureuser/ScriptVote"

echo "🚀 Déploiement vers la VM Azure avec rsync"
echo "==========================================="
echo "VM: $VM_USER@$VM_IP"
echo "Destination: $REMOTE_DIR"
echo ""

# Synchronisation des fichiers
echo "📤 Synchronisation des fichiers..."
rsync -avz \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude 'logs' \
    --exclude '*.log' \
    --exclude 'screenshots' \
    --exclude '.env' \
    --exclude 'downloaded_files' \
    --exclude '.DS_Store' \
    ./ $VM_USER@$VM_IP:$REMOTE_DIR/

if [ $? -eq 0 ]; then
    echo "✅ Fichiers synchronisés avec succès!"
    
    echo ""
    echo "🔧 Configuration sur la VM..."
    echo "Connexion SSH pour finaliser l'installation..."
    
    ssh $VM_USER@$VM_IP << 'ENDSSH'
cd /home/azureuser/ScriptVote

# Créer le venv si nécessaire
if [ ! -d "venv" ]; then
    echo "🐍 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer le venv et installer les dépendances
echo "📦 Installation des dépendances..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️ ATTENTION: Fichier .env manquant!"
    echo "Créez le fichier .env avec:"
    echo "  TWOCAPTCHA_API_KEY=votre_clé_api"
    echo "  username=zCapsLock"
else
    echo "✅ Fichier .env trouvé"
fi

# Test rapide
echo ""
echo "🧪 Test de l'installation..."
python3 -c "
import seleniumbase
import requests
print('✅ SeleniumBase installé')
print('✅ Requests installé')
"

echo ""
echo "✨ Déploiement terminé!"
echo ""
echo "Pour tester le vote:"
echo "  cd /home/azureuser/ScriptVote"
echo "  source venv/bin/activate"
echo "  python3 mtcaptcha_seleniumbase.py --headless"
ENDSSH

else
    echo "❌ Erreur lors de la synchronisation!"
    exit 1
fi