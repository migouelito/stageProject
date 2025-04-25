import os
import subprocess
from datetime import datetime

def commit_changes():
    # Ajoute les modifications
    subprocess.run(["git", "add", "."])

    # Crée un message de commit avec la date et l'heure
    message = f"Commit automatique : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Effectue le commit
    subprocess.run(["git", "commit", "-m", message])

    # Pousse les changements sur le dépôt distant
    subprocess.run(["git", "push", "origin", "master"])

if __name__ == "__main__":
    commit_changes()

