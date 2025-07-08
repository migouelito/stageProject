import json
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs
from asgiref.sync import sync_to_async

class PositionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'position_channel'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        positions = data.get('positions', [])

        if positions:
            for position in positions:
                latitude = position.get('latitude')
                longitude = position.get('longitude')
                tracker_id = position.get('tracker_id')
                type_animal = position.get('type_animal')  # Ajout ici

                if latitude and longitude and tracker_id:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_position',
                            'latitude': latitude,
                            'longitude': longitude,
                            'tracker_id': tracker_id,
                            'type_animal': type_animal  # Ajout dans l'événement
                        }
                    )

    '''async def send_position(self, event):
        latitude = event['latitude']
        longitude = event['longitude']
        tracker_id = event['tracker_id']
        type_animal = event.get('type_animal')  # Récupération ici

        # Vérification zone
        dans_zone = await self.is_capteur_in_zone(tracker_id, latitude, longitude)
        print(f"📍 Capteur {tracker_id} est dans la zone ? {'✅ Oui' if dans_zone else '❌ Non'}")

        query_string = self.scope['query_string'].decode()
        parsed_query = parse_qs(query_string)
        current_user_id = parsed_query.get('user_id', [None])[0]

        
        if not current_user_id:
            return

        user = await self.get_user(current_user_id)
        if not user:
            return

        has_access = await self.user_has_access_to_tracker(user, tracker_id)
        if not has_access:
            return

        # Envoi des données avec type_animal
        await self.send(text_data=json.dumps({
            'latitude': latitude,
            'longitude': longitude,
            'tracker_id': tracker_id,
            'type_animal': type_animal  # Inclusion dans l'envoi final
        }))'''

    async def send_position(self, event):
        latitude = event['latitude']
        longitude = event['longitude']
        tracker_id = event['tracker_id']
        type_animal = event.get('type_animal')

        # Vérification zone (facultatif)
        dans_zone = await self.is_capteur_in_zone(tracker_id, latitude, longitude)
        print(f"📍 Capteur {tracker_id} est dans la zone ? {'✅ Oui' if dans_zone else '❌ Non'}")

        # ✅ Envoi direct (sans filtrage par utilisateur)
        await self.send(text_data=json.dumps({
            'latitude': latitude,
            'longitude': longitude,
            'tracker_id': tracker_id,
            'type_animal': type_animal,
            'dans_zone': dans_zone
        }))


    @sync_to_async
    def is_capteur_in_zone(self, tracker_id, latitude, longitude):
        from capteurs.models import Capteur
        capteur = Capteur.objects.filter(identifiant=tracker_id).first()
        if capteur:
            # Ici, vous passez l'identifiant, latitude et longitude à la méthode is_capteur_in_zone
            return capteur.is_capteur_in_zone(tracker_id, latitude, longitude)
        return False

    @sync_to_async
    def get_user(self, user_id):
        from utilisateurs.models import User  # ✅ import déplacé ici
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @sync_to_async
    def user_has_access_to_tracker(self, user, tracker_id):
        from capteurs.models import Capteur  # ✅ import local ici
        capteurs = Capteur.get_capteurs_for_user(user)
        return capteurs.filter(identifiant=tracker_id).exists()


    @sync_to_async
    def is_tracker_unregistered(self, tracker_id):
        from capteurs.models import Capteur
        return not Capteur.objects.filter(identifiant=tracker_id).exists()