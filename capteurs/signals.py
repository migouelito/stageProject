# capteurs/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .services import start_verification

@receiver(post_migrate)
def start_verification_after_migrate(sender, **kwargs):
    # Lancer la vérification après les migrations
    start_verification()

