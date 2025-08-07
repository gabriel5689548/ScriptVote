# Configuration Proxy pour Contourner Cloudflare

## Pourquoi un proxy est nécessaire

GitHub Actions utilise des adresses IP de datacenter qui sont automatiquement blacklistées par Cloudflare. Pour contourner ce problème, vous devez utiliser un proxy résidentiel.

## Services de proxy recommandés

1. **Bright Data (anciennement Luminati)**
   - Proxies résidentiels de haute qualité
   - API simple et fiable
   - Prix: ~$15/GB

2. **IPRoyal**
   - Bon rapport qualité/prix
   - Proxies résidentiels rotatifs
   - Prix: ~$7/GB

3. **Smartproxy**
   - Interface simple
   - Bonne couverture géographique
   - Prix: ~$12.5/GB

4. **Oxylabs**
   - Très fiable mais plus cher
   - Excellente pour les sites difficiles
   - Prix: ~$15/GB

## Configuration dans GitHub Secrets

Ajoutez ces secrets dans votre repository GitHub:

```
PROXY_HOST=your-proxy-host.com
PROXY_PORT=8080
PROXY_USER=your-username
PROXY_PASS=your-password
```

## Format proxy dans le script

Le script SeleniumBase supporte automatiquement les proxies via les variables d'environnement configurées.

## Proxy gratuit (déconseillé)

Les proxies gratuits sont généralement bloqués par Cloudflare. Si vous voulez tester, vous pouvez utiliser:
- https://www.proxy-list.download/
- https://free-proxy-list.net/

Mais le taux de succès sera très faible.

## Alternative: GitHub Self-Hosted Runner

Si vous ne voulez pas payer pour un proxy, vous pouvez:
1. Configurer un runner GitHub self-hosted sur votre propre machine/VPS
2. Utiliser une IP résidentielle (votre connexion internet domestique)
3. Suivre: https://docs.github.com/en/actions/hosting-your-own-runners