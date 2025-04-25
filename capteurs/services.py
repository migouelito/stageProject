import time
import threading
from datetime import datetime, timezone
from capteurs.models import ZoneSecurite, Capteur, Message
from django.contrib.auth.models import User  # Assumons que User est déjà importé
import time
from datetime import datetime, timezone
from .models import ZoneSecurite
import time
from datetime import datetime, timezone
from .models import ZoneSecurite

def verifier_zones_en_boucle():
    while True:
        now = datetime.now(timezone.utc)
        zones = ZoneSecurite.objects.all()

        for zone in zones:
            capteurs = zone.capteur_set.all()

            # Marquer inactifs les capteurs trop vieux
            for capteur in capteurs:
                if not capteur.last_seen or (now - capteur.last_seen).total_seconds() > 10:
                    if capteur.actif:
                        capteur.actif = False
                        capteur.save()
                        print(f"⚠️ Capteur {capteur.identifiant} inactif")
                else:
                    if not capteur.actif:
                        capteur.actif = True
                        capteur.save()
                        print(f"✅ Capteur {capteur.identifiant} redevenu actif")

            capteurs_actifs = capteurs.filter(actif=True)
            ancien_is_zone = zone.is_zone
            ancien_is_pred = zone.is_pred

            if not capteurs_actifs.exists():
                # Aucun capteur actif : on ne touche à rien
                print(f"⚠️ Zone {zone.nom} : aucun capteur actif → état inchangé (is_zone={ancien_is_zone}, is_pred={ancien_is_pred})")
                continue

            au_moins_un_hors_zone = any(not c.is_zone for c in capteurs_actifs)

            if au_moins_un_hors_zone:
                # Au moins un capteur actif est hors zone
                if zone.is_zone or zone.is_pred:
                    zone.is_zone = False
                    if zone.is_pred:
                        zone.is_pred = False
                        zone.save()
                        print(f"❌ Zone {zone.nom} : capteurs hors zone → is_pred=False")
                        envoyer_message_alerte(zone, "Les animaux ne sont plus en sécurité.")
                    else:
                        zone.save()
                        print(f"Zone {zone.nom} : capteurs hors zone → is_zone=False (déjà is_pred=False)")
                else:
                    print(f"Zone {zone.nom} : déjà marquée non sécurisée")
            else:
                # Tous les capteurs actifs sont dans la zone
                if not zone.is_zone or not zone.is_pred:
                    zone.is_zone = True
                    if not zone.is_pred:
                        zone.is_pred = True
                        zone.save()
                        print(f"✅ Zone {zone.nom} : tous capteurs ok → is_pred=True")
                        envoyer_message_alerte(zone, "Les animaux sont en sécurité.")
                    else:
                        zone.save()
                        print(f"Zone {zone.nom} : is_zone=True (is_pred déjà True)")
                else:
                    print(f"Zone {zone.nom} : déjà marquée sécurisée")

            print("-" * 50)

        time.sleep(1)



def envoyer_message_alerte(zone, message):
    """Envoie un message d'alerte uniquement à l'utilisateur associé à la zone."""
    utilisateur = zone.user  # Récupère l'utilisateur associé à cette zone (relation OneToOne ou ForeignKey)
    
    if utilisateur:  # Si un utilisateur est associé à la zone
        Message.objects.create(
            zone=zone,
            user=utilisateur,
            corps_message=message,
            is_read=False
        )
        print(f"Message envoyé à {utilisateur.username}: {message}")
    else:
        print(f"Aucun utilisateur associé à la zone {zone.nom}")


def start_verification():
    thread = threading.Thread(target=verifier_zones_en_boucle)
    thread.daemon = True
    thread.start()
