#!/bin/bash

# Script pour configurer le cron sur la VM Azure
# Vote automatique toutes les 1h30

echo "⏰ Configuration du vote automatique toutes les 1h30"
echo "===================================================="

# Créer le script de vote
cat > /home/azureuser/vote.sh << 'EOF'
#!/bin/bash

# Script de vote automatique
LOG_FILE="/home/azureuser/ScriptVote/logs/vote_$(date +%Y%m%d).log"
mkdir -p /home/azureuser/ScriptVote/logs

echo "========================================" >> $LOG_FILE
echo "🚀 Vote lancé à $(date)" >> $LOG_FILE

cd /home/azureuser/ScriptVote
source venv/bin/activate

# Lancer le vote
python3 mtcaptcha_seleniumbase.py --headless >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Vote réussi à $(date)" >> $LOG_FILE
else
    echo "❌ Vote échoué à $(date)" >> $LOG_FILE
fi

echo "========================================" >> $LOG_FILE
echo "" >> $LOG_FILE
EOF

chmod +x /home/azureuser/vote.sh

echo "✅ Script de vote créé: /home/azureuser/vote.sh"

# Configurer le cron pour toutes les 1h30 (90 minutes)
echo "📝 Configuration du cron..."

# Supprimer l'ancienne entrée si elle existe
(crontab -l 2>/dev/null | grep -v "vote.sh") | crontab -

# Ajouter la nouvelle entrée
# Toutes les 1h30 = */90 minutes, mais cron ne supporte pas directement */90
# On utilise donc plusieurs entrées pour simuler toutes les 1h30
(crontab -l 2>/dev/null; cat << 'CRON'
# Vote automatique toutes les 1h30
# Minutes: 0, puis +90 = 30 dans l'heure suivante
0 0,3,6,9,12,15,18,21 * * * /home/azureuser/vote.sh
30 1,4,7,10,13,16,19,22 * * * /home/azureuser/vote.sh
CRON
) | crontab -

echo "✅ Cron configuré pour voter toutes les 1h30"

# Vérifier la configuration
echo ""
echo "📋 Configuration actuelle du cron:"
crontab -l | grep vote.sh

echo ""
echo "📊 Pour voir les logs:"
echo "  tail -f /home/azureuser/ScriptVote/logs/vote_$(date +%Y%m%d).log"

echo ""
echo "🧪 Test immédiat du script:"
/home/azureuser/vote.sh

echo ""
echo "✨ Configuration terminée!"
echo ""
echo "Le vote sera exécuté automatiquement:"
echo "  - À 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00"
echo "  - À 01:30, 04:30, 07:30, 10:30, 13:30, 16:30, 19:30, 22:30"
echo "  = Toutes les 1h30 !"