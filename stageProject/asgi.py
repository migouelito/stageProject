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