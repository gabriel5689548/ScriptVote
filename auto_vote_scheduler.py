#!/usr/bin/env python3
"""
Auto Vote Scheduler - Vote automatique toutes les 1h30
"""

import os
import time
import logging
import schedule
from datetime import datetime, timedelta
from typing import Optional
from mtcaptcha_tester import MTCaptchaTester
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_vote.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoVoteScheduler:
    def __init__(self, api_key: str, vote_url: str):
        self.api_key = api_key
        self.vote_url = vote_url
        self.vote_count = 0
        self.start_time = datetime.now()
        
    def perform_vote(self):
        """Effectue un vote automatique"""
        try:
            self.vote_count += 1
            logger.info(f"=== TENTATIVE DE VOTE #{self.vote_count} ===")
            logger.info(f"Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Créer une instance du testeur
            tester = MTCaptchaTester(self.api_key, timeout=300)
            
            # Exécuter le vote en mode headless pour plus de discrétion
            success = tester.run_test(self.vote_url, headless=True)
            
            if success:
                logger.info(f"✅ VOTE #{self.vote_count} RÉUSSI!")
                self.log_statistics()
                # Programmer le prochain vote dans 1h30
                next_vote_time = datetime.now() + timedelta(hours=1, minutes=30)
                logger.info(f"⏰ Prochain vote programmé à: {next_vote_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                logger.error(f"❌ VOTE #{self.vote_count} ÉCHOUÉ")
                # Lire les logs pour détecter les erreurs de cooldown
                cooldown_minutes = self.extract_cooldown_from_logs()
                if cooldown_minutes:
                    next_vote_time = datetime.now() + timedelta(minutes=cooldown_minutes + 2)  # +2 min de sécurité
                    logger.info(f"⏰ Cooldown détecté: {cooldown_minutes} min. Prochain vote à: {next_vote_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    # Erreur inconnue, réessayer dans 10 minutes
                    next_vote_time = datetime.now() + timedelta(minutes=10)
                    logger.info(f"⏰ Erreur inconnue, réessai dans 10 min à: {next_vote_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
        except Exception as e:
            logger.error(f"Erreur lors du vote #{self.vote_count}: {str(e)}")
            
        logger.info("=" * 60)

    def extract_cooldown_from_logs(self) -> Optional[int]:
        """Extrait le temps de cooldown depuis les logs"""
        try:
            import re
            with open('mtcaptcha_test.log', 'r') as f:
                logs = f.read()
                
            # Chercher le pattern "Prochain vote dans X heure(s) Y minutes Z secondes"
            patterns = [
                # "1 heure 25 minutes 49 secondes"
                r'Prochain vote dans (\d+) heures?\s+(\d+) minutes?\s+(\d+) secondes?',
                # "1 heure 25 minutes"  
                r'Prochain vote dans (\d+) heures?\s+(\d+) minutes?',
                # "25 minutes 49 secondes"
                r'Prochain vote dans (\d+) minutes?\s+(\d+) secondes?',
                # "25 minutes"
                r'Prochain vote dans (\d+) minutes?',
                # Autres patterns
                r'wait (\d+) minutes?',
                r'cooldown.*?(\d+).*?minutes?'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, logs, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    total_minutes = 0
                    
                    if len(groups) == 3:  # heures + minutes + secondes
                        hours = int(groups[0])
                        minutes = int(groups[1])
                        seconds = int(groups[2])
                        total_minutes = hours * 60 + minutes + (1 if seconds > 0 else 0)
                        logger.info(f"🕒 Cooldown extrait: {hours}h {minutes}min {seconds}s = {total_minutes} minutes")
                    elif len(groups) == 2:
                        if 'heure' in pattern:  # heures + minutes
                            hours = int(groups[0])
                            minutes = int(groups[1])
                            total_minutes = hours * 60 + minutes
                            logger.info(f"🕒 Cooldown extrait: {hours}h {minutes}min = {total_minutes} minutes")
                        else:  # minutes + secondes
                            minutes = int(groups[0])
                            seconds = int(groups[1])
                            total_minutes = minutes + (1 if seconds > 0 else 0)
                            logger.info(f"🕒 Cooldown extrait: {minutes}min {seconds}s = {total_minutes} minutes")
                    else:  # juste minutes
                        total_minutes = int(groups[0])
                        logger.info(f"🕒 Cooldown extrait: {total_minutes} minutes")
                    
                    return total_minutes
                    
            return None
            
        except Exception as e:
            logger.debug(f"Erreur extraction cooldown: {str(e)}")
            return None

    def log_statistics(self):
        """Affiche les statistiques"""
        elapsed = datetime.now() - self.start_time
        hours = elapsed.total_seconds() / 3600
        
        logger.info(f"📊 STATISTIQUES:")
        logger.info(f"   - Votes réussis: {self.vote_count}")
        logger.info(f"   - Temps de fonctionnement: {hours:.1f}h")
        logger.info(f"   - Moyenne: {self.vote_count/hours:.2f} votes/heure" if hours > 0 else "   - Moyenne: N/A")

    def run_once(self):
        """Effectue un vote immédiatement"""
        logger.info("🚀 LANCEMENT D'UN VOTE IMMÉDIAT")
        self.perform_vote()

    def start_scheduler(self):
        """Démarre le planificateur automatique"""
        logger.info("🤖 DÉMARRAGE DU PLANIFICATEUR AUTO-VOTE")
        logger.info(f"URL cible: {self.vote_url}")
        logger.info(f"Intervalle: 1h30 (90 minutes)")
        logger.info(f"Heure de démarrage: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Programmer les votes toutes les 1h30
        schedule.every(90).minutes.do(self.perform_vote)
        
        # Effectuer le premier vote immédiatement
        logger.info("Premier vote dans 5 secondes...")
        time.sleep(5)
        self.perform_vote()
        
        # Boucle principale
        logger.info("🔄 PLANIFICATEUR ACTIF - Votes automatiques toutes les 1h30")
        logger.info("Appuyez sur Ctrl+C pour arrêter")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
                
        except KeyboardInterrupt:
            logger.info("🛑 ARRÊT DU PLANIFICATEUR")
            self.log_statistics()
            logger.info("Au revoir!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Planificateur de votes automatiques')
    parser.add_argument('--url', default='https://serveur-prive.net/minecraft/oneblockbyrivrs/vote', 
                       help='URL de vote')
    parser.add_argument('--once', action='store_true', help='Effectuer un seul vote puis quitter')
    parser.add_argument('--headless', action='store_true', help='Mode headless (sans interface)')
    
    args = parser.parse_args()
    
    # Charger la configuration
    load_dotenv()
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    
    if not api_key:
        logger.error("❌ Clé API 2Captcha manquante dans .env")
        return
    
    # Créer le planificateur
    scheduler = AutoVoteScheduler(api_key, args.url)
    
    if args.once:
        scheduler.run_once()
    else:
        scheduler.start_scheduler()

if __name__ == "__main__":
    main()