# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from capteurs.consumers import PositionConsumer # adapte selon ton app

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stageProject.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"^ws/positions/$", PositionConsumer.as_asgi()),
        ])
    ),
})

'''import os
import django
from django.core.asgi import get_asgi_application
from django.core.management import call_command
from django.contrib.auth import get_user_model

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from capteurs.consumers import PositionConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stageProject.settings")

# Initialise Django (indispensable pour exécuter les commandes en standalone)
django.setup()

# Générer les migrations (optionnel si déjà faites)
try:
    call_command('makemigrations', interactive=False)
except Exception as e:
    print(f"Erreur makemigrations : {e}")

# Appliquer les migrations
try:
    call_command('migrate', interactive=False)
except Exception as e:
    print(f"Erreur migrate : {e}")

# Créer superuser si aucun n'existe
try:
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser(
            username='migouelito',
            email='migouelito123@gmail.com',
            password='123456'
        )
        print("Superuser créé automatiquement")
except Exception as e:
    print(f"Erreur création superuser : {e}")

# Application ASGI (HTTP + WebSocket)
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"^ws/positions/$", PositionConsumer.as_asgi()),
        ])
    ),
})'''

'''import os
import django
from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from capteurs.consumers import PositionConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stageProject.settings")
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"^ws/positions/$", PositionConsumer.as_asgi()),
        ])
    ),
})
'''
