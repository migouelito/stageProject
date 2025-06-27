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
from capteurs import routing  # Import des routes WebSocket

# Définir le fichier settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stageproject.settings')

# Initialisation Django
django.setup()

# Étape 1 : Créer toutes les migrations pour toutes les apps
try:
    print("🔧 Génération des fichiers de migration...")
    call_command('makemigrations', interactive=False)
except Exception as e:
    print(f"⚠️ Erreur lors de makemigrations : {e}")

# Étape 2 : Appliquer toutes les migrations
try:
    print("🔁 Application des migrations...")
    call_command('migrate', interactive=False)
except Exception as e:
    print(f"❌ Erreur lors des migrations : {e}")

# Étape 3 : Créer un superuser s'il n'existe pas
try:
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        print("👤 Création d'un superuser par défaut...")
        User.objects.create_superuser(
            username='migouelito',
            email='migouelito123@gmail.com',
            password='123456'
        )
except Exception as e:
    print(f"❌ Erreur création superutilisateur : {e}")

# ASGI application (http + websocket)
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
