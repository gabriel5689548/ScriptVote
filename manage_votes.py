#!/usr/bin/env python3
"""
Gestionnaire de votes automatiques
"""

import os
import signal
import subprocess
import sys
import time
from datetime import datetime

def start_auto_votes():
    """Démarre le planificateur en arrière-plan"""
    print("🚀 Démarrage du vote automatique...")
    
    # Lancer le processus en arrière-plan
    cmd = [sys.executable, "auto_vote_scheduler.py", "--headless"]
    process = subprocess.Popen(cmd, 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
    
    # Sauvegarder le PID
    with open('vote_process.pid', 'w') as f:
        f.write(str(process.pid))
    
    print(f"✅ Processus démarré (PID: {process.pid})")
    print("📊 Consultez auto_vote.log pour suivre l'activité")
    print("🛑 Utilisez 'python3 manage_votes.py stop' pour arrêter")
    
    return process

def stop_auto_votes():
    """Arrête le planificateur"""
    try:
        with open('vote_process.pid', 'r') as f:
            pid = int(f.read().strip())
        
        print(f"🛑 Arrêt du processus {pid}...")
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        
        # Vérifier si le processus est vraiment arrêté
        try:
            os.kill(pid, 0)  # Test si le processus existe
            print("⚠️  Processus résistant, force l'arrêt...")
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass  # Processus déjà arrêté
        
        os.remove('vote_process.pid')
        print("✅ Processus arrêté avec succès")
        
    except FileNotFoundError:
        print("❌ Aucun processus en cours d'exécution")
    except Exception as e:
        print(f"❌ Erreur lors de l'arrêt: {e}")

def check_status():
    """Vérifie le statut du planificateur"""
    try:
        with open('vote_process.pid', 'r') as f:
            pid = int(f.read().strip())
        
        try:
            os.kill(pid, 0)  # Test si le processus existe
            print(f"✅ Processus actif (PID: {pid})")
            
            # Afficher les dernières lignes du log
            if os.path.exists('auto_vote.log'):
                print("\n📊 DERNIÈRES ACTIVITÉS:")
                with open('auto_vote.log', 'r') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:  # 10 dernières lignes
                        print(f"   {line.strip()}")
            
        except OSError:
            print("❌ Processus non actif")
            os.remove('vote_process.pid')
            
    except FileNotFoundError:
        print("❌ Aucun processus en cours d'exécution")

def show_logs():
    """Affiche les logs en temps réel"""
    if os.path.exists('auto_vote.log'):
        print("📋 LOGS EN TEMPS RÉEL (Ctrl+C pour quitter):")
        print("=" * 60)
        try:
            # Suivre le fichier de log
            subprocess.run(['tail', '-f', 'auto_vote.log'])
        except KeyboardInterrupt:
            print("\n👋 Fermeture des logs")
    else:
        print("❌ Aucun fichier de log trouvé")

def main():
    if len(sys.argv) < 2:
        print("🤖 GESTIONNAIRE DE VOTES AUTOMATIQUES")
        print("")
        print("Usage:")
        print("  python3 manage_votes.py start   - Démarre le vote automatique")
        print("  python3 manage_votes.py stop    - Arrête le vote automatique") 
        print("  python3 manage_votes.py status  - Vérifie le statut")
        print("  python3 manage_votes.py logs    - Affiche les logs")
        print("  python3 manage_votes.py test    - Test un vote unique")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        start_auto_votes()
    elif command == 'stop':
        stop_auto_votes()
    elif command == 'status':
        check_status()
    elif command == 'logs':
        show_logs()
    elif command == 'test':
        print("🧪 Test d'un vote unique...")
        subprocess.run([sys.executable, "auto_vote_scheduler.py", "--once", "--headless"])
    else:
        print(f"❌ Commande inconnue: {command}")

if __name__ == "__main__":
    main()