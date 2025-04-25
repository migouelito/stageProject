import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from . import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ton_projet.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Cela gère les requêtes HTTP classiques
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r'ws/positions/$', consumers.PositionConsumer.as_asgi()),
        ])
    ),
})
