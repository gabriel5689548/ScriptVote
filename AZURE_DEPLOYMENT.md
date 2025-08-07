# 🚀 Guide de déploiement Azure pour ScriptVote

## 📋 Prérequis
- Compte Azure avec abonnement étudiant ($100 de crédit)
- Azure CLI installé localement
- Repository GitHub avec le projet ScriptVote
- Clé API 2Captcha/CapSolver

## 💰 Estimation des coûts (24/7)
| Ressource | Coût mensuel | Coût annuel |
|-----------|--------------|-------------|
| VM B1s (1 vCPU, 1GB RAM) | ~$3.80 | ~$45.60 |
| Stockage 30GB HDD | ~$1.50 | ~$18.00 |
| IP statique | ~$3.65 | ~$43.80 |
| **TOTAL** | **~$8.95** | **~$107.40** |

⚠️ **Note**: Dépasse légèrement les $100/an. Solutions:
- Utiliser les crédits gratuits Azure for Students
- Option VM B1ls si disponible (0.5GB RAM, moins cher)
- Surveiller la consommation via Azure Cost Management

## 🔧 Déploiement rapide (Option 1: ARM Template)

### 1. Se connecter à Azure
```bash
az login
az account set --subscription "Azure for Students"
```

### 2. Créer un groupe de ressources
```bash
az group create --name scriptvote-rg --location eastus
```

### 3. Déployer avec le template ARM
```bash
az deployment group create \
  --resource-group scriptvote-rg \
  --template-file azure/azuredeploy.json \
  --parameters \
    adminPassword='VotreMotDePasse123!' \
    captchaApiKey='VOTRE_CLE_API' \
    voteUsername='zCapsLock'
```

### 4. Récupérer l'IP publique
```bash
az vm show -d -g scriptvote-rg -n scriptvote-vm --query publicIps -o tsv
```

## 🛠️ Déploiement manuel (Option 2)

### 1. Créer la VM via le portail Azure
1. Aller sur [portal.azure.com](https://portal.azure.com)
2. Créer une ressource → Machine virtuelle
3. Configuration:
   - **Nom**: scriptvote-vm
   - **Région**: East US (ou moins cher)
   - **Image**: Ubuntu Server 22.04 LTS
   - **Taille**: B1s (1 vCPU, 1GB RAM)
   - **Authentification**: Mot de passe
   - **Ports entrants**: SSH (22)

### 2. Se connecter à la VM
```bash
ssh azureuser@<IP_PUBLIQUE>
```

### 3. Cloner le repository
```bash
git clone https://github.com/VOTRE_USERNAME/ScriptVote.git
cd ScriptVote/azure
```

### 4. Configurer les variables d'environnement
```bash
export CAPTCHA_API_KEY="votre_cle_api"
export VOTE_USERNAME="zCapsLock"
```

### 5. Exécuter les scripts d'installation
```bash
chmod +x *.sh
sudo ./azure_setup.sh
./deploy.sh
./vote_scheduler.sh
```

## 📅 Configuration du scheduler

Le vote s'exécute automatiquement toutes les 4 heures (6 fois par jour).

### Modifier la fréquence
```bash
crontab -e
# Modifier la ligne: 0 */4 * * * (toutes les 4 heures)
# Exemples:
# 0 */2 * * * - toutes les 2 heures
# 0 */6 * * * - toutes les 6 heures
# 0 0,6,12,18 * * * - à 00h, 6h, 12h, 18h
```

## 📊 Monitoring

### Voir les logs en temps réel
```bash
tail -f ~/ScriptVote/logs/cron.log
```

### Vérifier le status du service
```bash
sudo systemctl status scriptvote
```

### Voir les statistiques
```bash
cat ~/ScriptVote/logs/vote_stats.csv
```

### Lancer un check de santé
```bash
~/ScriptVote/azure/monitor.sh check
```

## 🔒 Sécurité

### 1. Restreindre l'accès SSH
```bash
# Dans Azure Portal → VM → Networking
# Modifier la règle SSH pour autoriser uniquement votre IP
```

### 2. Activer les mises à jour automatiques
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Configurer les alertes budget
1. Azure Portal → Cost Management
2. Créer une alerte à 80% du budget ($80)
3. Créer une alerte critique à 95% ($95)

## 🛑 Arrêt d'urgence

Si les coûts dépassent le budget:
```bash
# Arrêter la VM (conserve l'IP)
az vm deallocate -g scriptvote-rg -n scriptvote-vm

# Redémarrer plus tard
az vm start -g scriptvote-rg -n scriptvote-vm
```

## 🔧 Dépannage

### Problème: Vote échoue
```bash
# Vérifier les logs
tail -n 50 ~/ScriptVote/logs/cron.log

# Tester manuellement
cd ~/ScriptVote
source venv/bin/activate
python3 mtcaptcha_seleniumbase.py --headless
```

### Problème: Manque de mémoire
```bash
# Voir l'utilisation
free -h

# Nettoyer
~/ScriptVote/azure/monitor.sh clean

# Si persistant, upgrade vers B1ms (2GB RAM)
```

### Problème: Espace disque plein
```bash
# Voir l'utilisation
df -h

# Nettoyer les logs
find ~/ScriptVote/logs -name "*.log" -mtime +7 -delete
find ~/ScriptVote/screenshots -name "*.png" -delete
```

## 📈 Optimisation des coûts

### 1. Surveillance quotidienne
```bash
# Installer Azure CLI sur la VM
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Voir la consommation
az consumption usage list \
  --start-date $(date -d "30 days ago" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "sum([].pretaxCost)" -o tsv
```

### 2. Réduction des coûts
- Utiliser une région moins chère (ex: Central US)
- Désactiver l'IP statique si possible (utiliser DynDNS)
- Considérer Azure Spot VMs (jusqu'à 90% de réduction)

## 🚀 Commandes utiles

```bash
# Démarrer un vote manuel
~/ScriptVote/azure/run_vote.sh

# Voir tous les processus Chrome
ps aux | grep chrome

# Tuer tous les Chrome zombies
pkill -f "chrome.*--headless"

# Redémarrer le service
sudo systemctl restart scriptvote

# Voir les crons actifs
crontab -l

# Éditer la configuration
nano ~/ScriptVote/.env
```

## 📞 Support

En cas de problème:
1. Vérifier les logs: `~/ScriptVote/logs/`
2. Consulter Azure Status: [status.azure.com](https://status.azure.com)
3. Ouvrir un ticket Azure Support (gratuit avec abonnement étudiant)