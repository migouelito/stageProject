# realtime/routing.py
from django.urls import re_path
from .consumers import GPSConsumer

websocket_urlpatterns = [
    re_path(r'ws/gps/$', GPSConsumer.as_asgi()),  # URL de connexion WebSocket
]
