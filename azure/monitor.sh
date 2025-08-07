#!/bin/bash

PROJECT_DIR="/home/azureuser/ScriptVote"
LOG_DIR="$PROJECT_DIR/logs"
ALERT_EMAIL="${ALERT_EMAIL:-}"
MAX_DISK_USAGE=80
MAX_MEMORY_USAGE=90
MAX_LOG_SIZE_MB=100

check_disk_usage() {
    DISK_USAGE=$(df -h / | grep -vE '^Filesystem' | awk '{print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -gt "$MAX_DISK_USAGE" ]; then
        echo "[$(date)] ⚠️ ALERTE: Utilisation disque élevée: ${DISK_USAGE}%"
        
        # Nettoyage automatique
        find $LOG_DIR -name "*.log" -mtime +3 -delete
        find $PROJECT_DIR/screenshots -name "*.png" -mtime +1 -delete
        sudo apt-get autoremove -y > /dev/null 2>&1
        sudo apt-get clean > /dev/null 2>&1
        
        return 1
    else
        echo "[$(date)] ✅ Espace disque OK: ${DISK_USAGE}%"
        return 0
    fi
}

check_memory_usage() {
    MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    
    if [ "$MEMORY_USAGE" -gt "$MAX_MEMORY_USAGE" ]; then
        echo "[$(date)] ⚠️ ALERTE: Utilisation mémoire élevée: ${MEMORY_USAGE}%"
        
        # Tuer les processus Chrome zombies
        pkill -f "chrome.*defunct" 2>/dev/null
        pkill -f "chrome.*--headless" 2>/dev/null
        
        return 1
    else
        echo "[$(date)] ✅ Mémoire OK: ${MEMORY_USAGE}%"
        return 0
    fi
}

check_service_health() {
    if systemctl is-active --quiet scriptvote.service; then
        echo "[$(date)] ✅ Service scriptvote actif"
    else
        echo "[$(date)] ❌ Service scriptvote inactif - redémarrage..."
        sudo systemctl restart scriptvote.service
        return 1
    fi
    
    return 0
}

check_chrome_processes() {
    CHROME_COUNT=$(pgrep -f "chrome" | wc -l)
    
    if [ "$CHROME_COUNT" -gt 10 ]; then
        echo "[$(date)] ⚠️ Trop de processus Chrome ($CHROME_COUNT) - nettoyage..."
        pkill -f "chrome.*--headless"
        sleep 2
        pkill -9 -f "chrome.*--headless" 2>/dev/null
        return 1
    else
        echo "[$(date)] ✅ Processus Chrome OK: $CHROME_COUNT"
        return 0
    fi
}

check_log_sizes() {
    for logfile in $LOG_DIR/*.log; do
        if [ -f "$logfile" ]; then
            SIZE_MB=$(du -m "$logfile" | cut -f1)
            if [ "$SIZE_MB" -gt "$MAX_LOG_SIZE_MB" ]; then
                echo "[$(date)] 📄 Rotation du log: $(basename $logfile) (${SIZE_MB}MB)"
                mv "$logfile" "${logfile}.old"
                touch "$logfile"
            fi
        fi
    done
}

check_azure_budget() {
    # Utilise Azure CLI si disponible
    if command -v az &> /dev/null; then
        CURRENT_COST=$(az consumption usage list \
            --start-date $(date -d "30 days ago" +%Y-%m-%d) \
            --end-date $(date +%Y-%m-%d) \
            --query "[?contains(instanceName, 'scriptvote')] | [0].pretaxCost" \
            -o tsv 2>/dev/null || echo "0")
        
        if (( $(echo "$CURRENT_COST > 8" | bc -l) )); then
            echo "[$(date)] 💰 ALERTE BUDGET: Consommation mensuelle: \$${CURRENT_COST}"
            return 1
        else
            echo "[$(date)] ✅ Budget OK: \$${CURRENT_COST}/mois"
        fi
    fi
    return 0
}

generate_stats() {
    if [ -f "$LOG_DIR/vote_stats.csv" ]; then
        TOTAL=$(tail -n +2 "$LOG_DIR/vote_stats.csv" | wc -l)
        SUCCESS=$(grep ",SUCCESS," "$LOG_DIR/vote_stats.csv" | wc -l)
        FAILURE=$(grep ",FAILURE," "$LOG_DIR/vote_stats.csv" | wc -l)
        
        if [ "$TOTAL" -gt 0 ]; then
            SUCCESS_RATE=$((SUCCESS * 100 / TOTAL))
            echo "[$(date)] 📊 Stats: Total=$TOTAL, Succès=$SUCCESS ($SUCCESS_RATE%), Échecs=$FAILURE"
        fi
    fi
}

send_alert() {
    MESSAGE=$1
    
    if [ ! -z "$ALERT_EMAIL" ]; then
        echo "$MESSAGE" | mail -s "ScriptVote Alert - $(hostname)" "$ALERT_EMAIL" 2>/dev/null
    fi
    
    # Log dans le système
    logger -t "ScriptVote" "$MESSAGE"
}

main() {
    echo "=========================================="
    echo "[$(date)] 🔍 Début du monitoring"
    echo "=========================================="
    
    ALERT_COUNT=0
    
    check_disk_usage || ((ALERT_COUNT++))
    check_memory_usage || ((ALERT_COUNT++))
    check_service_health || ((ALERT_COUNT++))
    check_chrome_processes || ((ALERT_COUNT++))
    check_log_sizes
    check_azure_budget || ((ALERT_COUNT++))
    generate_stats
    
    if [ "$ALERT_COUNT" -gt 0 ]; then
        echo "[$(date)] ⚠️ $ALERT_COUNT alertes détectées"
        send_alert "ScriptVote: $ALERT_COUNT alertes détectées sur $(hostname)"
    else
        echo "[$(date)] ✅ Tous les checks sont OK"
    fi
    
    echo "=========================================="
    echo ""
}

case "${1:-}" in
    check)
        main
        ;;
    stats)
        generate_stats
        ;;
    clean)
        echo "🧹 Nettoyage forcé..."
        find $LOG_DIR -name "*.log.old" -delete
        find $PROJECT_DIR/screenshots -name "*.png" -delete
        pkill -f "chrome.*--headless" 2>/dev/null
        echo "✅ Nettoyage terminé"
        ;;
    *)
        echo "Usage: $0 {check|stats|clean}"
        exit 1
        ;;
esac