# 🗳️ Vote Automation with GitHub Actions

Automatisation du vote sur oneblock.fr utilisant GitHub Actions, MTCaptcha et 2Captcha.

## 🚀 Configuration

### 1. Créer un Repository GitHub
- Créez un nouveau repository (public ou privé)
- Uploadez tous les fichiers de ce dossier

### 2. Configurer les Secrets GitHub
Dans votre repository GitHub, allez dans **Settings** → **Secrets and variables** → **Actions**

Ajoutez ces secrets :
- `CAPTCHA_API_KEY` : Votre clé API 2Captcha
- `USERNAME` : Votre pseudonyme (ex: zCapsLock)

**Optionnel :**
- `DISCORD_WEBHOOK` : URL webhook Discord pour notifications d'échec

### 3. Structure des fichiers
```
votre-repo/
├── .github/workflows/
│   └── vote-automation.yml     # Configuration GitHub Actions
├── mtcaptcha_github_actions.py # Script principal optimisé
├── requirements.txt            # Dépendances Python
├── .env                       # Variables locales (pas dans le repo!)
└── README.md                  # Ce fichier
```

## ⏰ Planning des Votes

Le workflow est configuré pour voter **24/7 toutes les 1h30** :
- 16 votes par jour
- ~80 minutes de GitHub Actions par jour
- ~2400 minutes par mois (compatible GitHub Pro : 3000 min/mois)

### Horaires de vote :
- 00h00, 01h30, 03h00, 04h30
- 06h00, 07h30, 09h00, 10h30  
- 12h00, 13h30, 15h00, 16h30
- 18h00, 19h30, 21h00, 22h30

## 🔧 Test et Débogage

### Test manuel
1. Allez dans **Actions** de votre repository
2. Sélectionnez le workflow "Vote Automation 24/7"
3. Cliquez sur **Run workflow** → **Run workflow**

### Vérifier les logs
- Chaque exécution génère des logs détaillés
- En cas d'échec, des artifacts avec screenshots sont sauvegardés

## 📊 Monitoring

### Consommation GitHub Actions
- **Settings** → **Billing** → **Usage this month**
- Surveillez vos minutes consommées

### Résultats
- Chaque run génère un summary avec le résultat
- Logs détaillés pour debugging

## 🛠️ Développement Local

### Prérequis
```bash
pip install -r requirements.txt
```

### Variables d'environnement (.env)
```
api_key=votre_clé_2captcha
username=zCapsLock
```

### Test local
```bash
python3 mtcaptcha_github_actions.py --headless
```

## 🔐 Sécurité

- ✅ API keys stockées en secrets GitHub
- ✅ Mode headless obligatoire sur GitHub Actions
- ✅ Timeout de sécurité (15 minutes max)
- ✅ Retry automatique (3 tentatives)

## 🚨 Dépannage

### Le workflow ne se déclenche pas
- Vérifiez que le repository n'est pas un fork
- Les workflows sur fork nécessitent une activation manuelle

### Échecs de vote
- Vérifiez vos secrets GitHub (CAPTCHA_API_KEY)
- Consultez les logs détaillés
- Testez manuellement avec `workflow_dispatch`

### Quota GitHub Actions dépassé
- Réduisez la fréquence des votes
- Upgradez vers GitHub Team/Enterprise

## 📝 Notes

- Nécessite un compte 2Captcha avec crédit
- Compatible avec GitHub Free (2000 min/mois) en réduisant la fréquence
- Optimisé pour GitHub Pro (3000 min/mois)

## 🤝 Support

En cas de problème :
1. Vérifiez les logs GitHub Actions
2. Testez en mode manuel (`workflow_dispatch`)
3. Vérifiez la configuration des secrets