from django.apps import AppConfig


class CapteursConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'capteurs'
    def ready(self):
        # Démarrer la vérification dans un thread séparé
        from .services import start_verification
        start_verification()