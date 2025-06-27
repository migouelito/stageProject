'''import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from capteurs import routing  # Assure-toi que capteurs.routing est bien importé

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stageproject.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns  # Les routes WebSocket configurées dans capteurs/routing.py
        )
    ),
})'''

import os
import django
from django.core.asgi import get_asgi_application
from django.core.management import call_command
from django.contrib.auth import get_user_model

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from capteurs import routing  # Assure-toi que capteurs.routing est bien importé

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stageproject.settings')

# Initialisation Django
django.setup()

# Lancer les migrations automatiquement
try:
    call_command('migrate', interactive=False)
except Exception as e:
    print(f"Erreur lors des migrations : {e}")

# Créer un superuser si aucun n'existe
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("Création d'un superuser par défaut...")
    User.objects.create_superuser(
        username='migouelito',
        email='migouelito123@gmail.com',
        password='123456'  # Change ce mot de passe après le premier lancement !
    )

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})

