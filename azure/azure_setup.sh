#!/bin/bash

set -e

echo "🚀 Configuration initiale Azure VM pour ScriptVote"
echo "=================================================="

sudo apt-get update
sudo apt-get upgrade -y

echo "📦 Installation des dépendances système..."
sudo apt-get install -y \
    python3.9 \
    python3-pip \
    python3.9-venv \
    git \
    wget \
    curl \
    unzip \
    xvfb \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    htop \
    tmux

echo "🌐 Installation de Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt-get update
sudo apt-get install -y google-chrome-stable

echo "✅ Version Chrome: $(google-chrome --version)"

echo "📁 Création de la structure du projet..."
cd /home/azureuser
mkdir -p ScriptVote/logs
mkdir -p ScriptVote/screenshots

echo "🐍 Configuration de l'environnement Python..."
cd ScriptVote
python3.9 -m venv venv
source venv/bin/activate

echo "📚 Installation des dépendances Python..."
pip install --upgrade pip
pip install \
    selenium==4.15.2 \
    seleniumbase==4.34.7 \
    undetected-chromedriver==3.6.0 \
    requests==2.31.0 \
    python-dotenv==1.0.0 \
    pyvirtualdisplay==3.0

echo "🔧 Configuration de logrotate..."
sudo tee /etc/logrotate.d/scriptvote > /dev/null <<EOF
/home/azureuser/ScriptVote/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 azureuser azureuser
}
EOF

echo "🔒 Configuration du firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw reload

echo "📊 Installation des outils de monitoring..."
sudo apt-get install -y sysstat iotop

echo "🎯 Configuration du swap (pour VM 1GB RAM)..."
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

echo "✨ Configuration initiale terminée!"
echo "Prochaine étape: exécuter deploy.sh pour cloner et configurer le projet"