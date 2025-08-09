#!/bin/bash

# Script de monitoring des votes

echo "📊 Monitoring des votes automatiques"
echo "====================================="
echo ""

LOG_DIR="/home/azureuser/ScriptVote/logs"

# Afficher les derniers votes
echo "📅 Derniers votes effectués:"
if [ -d "$LOG_DIR" ]; then
    grep -h "Vote " $LOG_DIR/vote_*.log 2>/dev/null | tail -10
else
    echo "Pas encore de logs"
fi

echo ""
echo "📈 Statistiques:"
if [ -d "$LOG_DIR" ]; then
    TOTAL=$(grep -h "Vote lancé" $LOG_DIR/vote_*.log 2>/dev/null | wc -l)
    SUCCESS=$(grep -h "✅ Vote réussi" $LOG_DIR/vote_*.log 2>/dev/null | wc -l)
    FAILED=$(grep -h "❌ Vote échoué" $LOG_DIR/vote_*.log 2>/dev/null | wc -l)
    COOLDOWN=$(grep -h "COOLDOWN DÉTECTÉ" $LOG_DIR/vote_*.log 2>/dev/null | wc -l)
    
    echo "  Total de tentatives: $TOTAL"
    echo "  Votes réussis: $SUCCESS"
    echo "  Votes échoués: $FAILED"
    echo "  Cooldowns détectés: $COOLDOWN"
else
    echo "Pas encore de statistiques"
fi

echo ""
echo "⏰ Prochains votes programmés:"
crontab -l | grep vote.sh

echo ""
echo "📝 Log du jour:"
TODAY_LOG="$LOG_DIR/vote_$(date +%Y%m%d).log"
if [ -f "$TODAY_LOG" ]; then
    echo "Dernières 20 lignes de $TODAY_LOG:"
    tail -20 "$TODAY_LOG"
else
    echo "Pas encore de log aujourd'hui"
fi

echo ""
echo "💡 Commandes utiles:"
echo "  tail -f $LOG_DIR/vote_$(date +%Y%m%d).log  # Suivre les logs en temps réel"
echo "  crontab -e                                  # Éditer le cron"
echo "  ./vote.sh                                   # Lancer un vote manuel"