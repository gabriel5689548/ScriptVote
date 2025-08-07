# Solution Cloudflare pour ScriptVote

## Problème

Cloudflare bloque l'accès à serveur-prive.net depuis GitHub Actions car:
1. GitHub Actions utilise des IPs de datacenter qui sont blacklistées
2. Le mode headless est plus facilement détectable
3. Selenium standard est facilement identifiable comme bot

## Solutions Implémentées

### 1. SeleniumBase avec UC Mode (Recommandé)

**Fichier**: `mtcaptcha_seleniumbase.py`
**Workflow**: `vote-seleniumbase.yml`

Avantages:
- Mode UC (UndetectedChromedriver) intégré
- Support xvfb pour Linux headless
- Méthodes spéciales pour bypass (`uc_open_with_reconnect`, `uc_gui_click_captcha`)

Configuration requise:
```bash
pip install seleniumbase
```

### 2. Undetected-ChromeDriver Direct

**Fichier**: `mtcaptcha_undetected.py`

Avantages:
- Plus de contrôle sur la configuration
- Compatible avec Chrome 126 (meilleure version pour bypass)

Configuration requise:
```bash
pip install undetected-chromedriver
```

### 3. Configuration Proxy (OBLIGATOIRE pour GitHub Actions)

Pour contourner le blacklist IP de GitHub Actions, vous DEVEZ utiliser un proxy:

1. **Ajoutez ces secrets GitHub**:
   ```
   PROXY_HOST=votre-proxy.com
   PROXY_PORT=8080
   PROXY_USER=username
   PROXY_PASS=password
   ```

2. **Services proxy recommandés**:
   - Bright Data: ~$15/GB (très fiable)
   - IPRoyal: ~$7/GB (bon rapport qualité/prix)
   - Smartproxy: ~$12.5/GB (facile à utiliser)

3. **Alternative gratuite**: GitHub Self-Hosted Runner
   - Installez un runner sur votre machine/VPS
   - Utilisez votre IP résidentielle
   - Guide: https://docs.github.com/en/actions/hosting-your-own-runners

## Test Local

Pour tester en local:
```bash
# Sans proxy
python mtcaptcha_seleniumbase.py --headless

# Avec proxy
export PROXY_HOST=proxy.com
export PROXY_PORT=8080
export PROXY_USER=user
export PROXY_PASS=pass
python mtcaptcha_seleniumbase.py --headless
```

## Déploiement GitHub Actions

1. **Configurez les secrets GitHub**:
   - `CAPTCHA_API_KEY`: Votre clé 2Captcha
   - `USERNAME`: Votre pseudo de vote
   - `PROXY_*`: Vos credentials proxy

2. **Testez manuellement**:
   - Allez dans Actions > Vote Automation SeleniumBase UC Mode
   - Cliquez "Run workflow"
   - Activez "use_proxy" si vous avez configuré un proxy

3. **Activez le schedule** (après tests réussis):
   - Décommentez les lignes `schedule:` dans le workflow
   - Le vote s'exécutera automatiquement toutes les 1h30

## Dépannage

### "Just a moment..." persiste
- Vérifiez que votre proxy fonctionne
- Essayez un autre service proxy
- Utilisez un self-hosted runner

### MTCaptcha sitekey non trouvée
- Le site a peut-être changé de structure
- Vérifiez manuellement sur serveur-prive.net
- Ajustez les sélecteurs CSS si nécessaire

### Vote échoue même avec proxy
- Cloudflare a peut-être mis à jour ses défenses
- Essayez la version non-headless en local
- Considérez des solutions commerciales (ZenRows, ScrapingBee)

## Notes Importantes

1. **Ne pas abuser**: Respectez les limites de vote du site
2. **Proxy obligatoire**: GitHub Actions ne fonctionnera PAS sans proxy
3. **Coût**: Prévoyez ~$5-10/mois pour un proxy décent
4. **Alternative**: Self-hosted runner = gratuit mais nécessite maintenance

## Historique

- Script fonctionnait en Juillet 2025 (trouvait sitekey "MTPublic-42pXmytZe")
- Cloudflare a renforcé ses protections depuis
- Solutions 2025: SeleniumBase UC mode + Proxy résidentiel