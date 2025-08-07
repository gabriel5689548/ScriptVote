#!/bin/bash

PROJECT_DIR="/home/azureuser/ScriptVote"
LOG_DIR="$PROJECT_DIR/logs"
VOTE_SCRIPT="mtcaptcha_seleniumbase.py"
LOCK_FILE="/tmp/scriptvote.lock"

echo "🗳️ Configuration du scheduler de vote 24/7"
echo "=========================================="

install_cron() {
    echo "📅 Configuration des tâches cron..."
    
    CRON_JOBS=$(cat <<'EOF'
# ScriptVote - Exécution toutes les 4 heures (6 fois par jour)
0 */4 * * * /home/azureuser/ScriptVote/azure/run_vote.sh >> /home/azureuser/ScriptVote/logs/cron.log 2>&1

# Nettoyage des logs tous les jours à 3h du matin
0 3 * * * find /home/azureuser/ScriptVote/logs -name "*.log" -mtime +7 -delete

# Nettoyage des screenshots tous les 3 jours
0 2 */3 * * find /home/azureuser/ScriptVote/screenshots -name "*.png" -mtime +3 -delete

# Monitoring de santé toutes les heures
0 * * * * /home/azureuser/ScriptVote/azure/monitor.sh check >> /home/azureuser/ScriptVote/logs/monitor.log 2>&1

# Redémarrage du service si nécessaire (tous les lundis à 4h)
0 4 * * 1 sudo systemctl restart scriptvote.service
EOF
)
    
    (crontab -l 2>/dev/null; echo "$CRON_JOBS") | crontab -
    echo "✅ Tâches cron installées"
}

create_run_script() {
    echo "📝 Création du script d'exécution..."
    
    cat > $PROJECT_DIR/azure/run_vote.sh <<'EOF'
#!/bin/bash

PROJECT_DIR="/home/azureuser/ScriptVote"
LOCK_FILE="/tmp/scriptvote.lock"
MAX_RETRIES=3
RETRY_DELAY=300

if [ -f "$LOCK_FILE" ]; then
    PID=$(cat $LOCK_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "[$(date)] ⚠️ Vote déjà en cours (PID: $PID)"
        exit 0
    else
        echo "[$(date)] 🔓 Suppression du lock obsolète"
        rm -f $LOCK_FILE
    fi
fi

echo $$ > $LOCK_FILE
trap "rm -f $LOCK_FILE" EXIT

cd $PROJECT_DIR
source venv/bin/activate

echo "[$(date)] 🚀 Démarrage du vote automatique"

export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
XVFB_PID=$!
sleep 2

ATTEMPT=1
SUCCESS=false

while [ $ATTEMPT -le $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
    echo "[$(date)] 🔄 Tentative $ATTEMPT/$MAX_RETRIES"
    
    timeout 120 python3 mtcaptcha_seleniumbase.py --headless
    RESULT=$?
    
    if [ $RESULT -eq 0 ]; then
        echo "[$(date)] ✅ Vote réussi!"
        SUCCESS=true
        
        # Log pour statistiques
        echo "$(date '+%Y-%m-%d %H:%M:%S'),SUCCESS,$ATTEMPT" >> logs/vote_stats.csv
    else
        echo "[$(date)] ❌ Échec (code: $RESULT)"
        
        if [ $ATTEMPT -lt $MAX_RETRIES ]; then
            echo "[$(date)] ⏳ Attente de $RETRY_DELAY secondes..."
            sleep $RETRY_DELAY
        else
            echo "[$(date)] 💥 Échec après $MAX_RETRIES tentatives"
            echo "$(date '+%Y-%m-%d %H:%M:%S'),FAILURE,$ATTEMPT" >> logs/vote_stats.csv
        fi
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
done

kill $XVFB_PID 2>/dev/null
rm -f $LOCK_FILE

echo "[$(date)] 🏁 Fin du processus de vote"
echo "----------------------------------------"
EOF
    
    chmod +x $PROJECT_DIR/azure/run_vote.sh
    echo "✅ Script d'exécution créé"
}

create_systemd_service() {
    echo "🔧 Création du service systemd..."
    
    sudo tee /etc/systemd/system/scriptvote.service > /dev/null <<EOF
[Unit]
Description=ScriptVote Automation Service
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/ScriptVote
Environment="PATH=/home/azureuser/ScriptVote/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/azureuser/ScriptVote/azure/run_vote.sh
Restart=on-failure
RestartSec=300
StandardOutput=append:/home/azureuser/ScriptVote/logs/service.log
StandardError=append:/home/azureuser/ScriptVote/logs/service-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable scriptvote.service
    echo "✅ Service systemd configuré"
}

setup_logging() {
    echo "📊 Configuration des logs..."
    
    mkdir -p $LOG_DIR
    touch $LOG_DIR/cron.log
    touch $LOG_DIR/service.log
    touch $LOG_DIR/service-error.log
    touch $LOG_DIR/monitor.log
    touch $LOG_DIR/vote_stats.csv
    
    if [ ! -s "$LOG_DIR/vote_stats.csv" ]; then
        echo "timestamp,status,attempts" > $LOG_DIR/vote_stats.csv
    fi
    
    echo "✅ Structure de logs créée"
}

echo "🔧 Installation des composants..."
create_run_script
install_cron
create_systemd_service
setup_logging

echo ""
echo "✨ Configuration du scheduler terminée!"
echo ""
echo "📋 Commandes utiles:"
echo "  - Voir les logs: tail -f $LOG_DIR/cron.log"
echo "  - Status du service: sudo systemctl status scriptvote"
echo "  - Démarrer manuellement: $PROJECT_DIR/azure/run_vote.sh"
echo "  - Voir les stats: cat $LOG_DIR/vote_stats.csv"
echo "  - Éditer le cron: crontab -e"
echo ""
echo "⏰ Le vote s'exécutera automatiquement toutes les 4 heures 24/7"