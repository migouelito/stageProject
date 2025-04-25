# realtime/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GPSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "gps_data"  # Groupe pour la communication

        # Joindre le groupe WebSocket
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Quitter le groupe WebSocket
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Recevoir des messages du WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        lat = data['lat']
        lng = data['lng']

        # Envoyer les données GPS à tous les clients connectés via le groupe WebSocket
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'gps_position',
                'lat': lat,
                'lng': lng
            }
        )

    # Envoi de la position GPS à WebSocket
    async def gps_position(self, event):
        lat = event['lat']
        lng = event['lng']

        # Envoyer la position GPS au WebSocket
        await self.send(text_data=json.dumps({
            'lat': lat,
            'lng': lng
        }))
