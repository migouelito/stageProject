import os
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
})
