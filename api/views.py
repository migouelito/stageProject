# views.py

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Bienvenue, vous êtes authentifié!'})


from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import EmailTokenObtainPairSerializer

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

# views.py


from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import UserSerializer

class UserDetail(APIView):
    permission_classes = [IsAuthenticated]  # Assurez-vous que seul un utilisateur authentifié peut accéder à cette vue

    def get(self, request):
        # Récupère l'utilisateur authentifié
        user = request.user
        serializer = UserSerializer(user)  # Sérialisation de l'utilisateur
        return Response(serializer.data)  # Retourne les données de l'utilisateur dans la réponse

    def put(self, request):
        # Met à jour l'utilisateur authentifié avec les données envoyées dans la requête
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)  # Utilisation de partial=True pour permettre la mise à jour partielle

        if serializer.is_valid():
            serializer.save()  # Sauvegarde les modifications
            return Response(serializer.data)  # Retourne les nouvelles données de l'utilisateur après la mise à jour
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Retourne les erreurs si la validation échoue

from rest_framework.permissions import IsAuthenticated  # Utilise l'authentification
from rest_framework.authentication import TokenAuthentication  # Utilise TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserProfileSerializer
from utilisateurs.models import User

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Assurez-vous que l'utilisateur est authentifié
    authentication_classes = [TokenAuthentication]  # Authentification par token

    def get(self, request):
        try:
            # Récupérer l'utilisateur authentifié
            user = request.user  # L'utilisateur est récupéré depuis le token dans la requête

            # Sérialiser les données de l'utilisateur
            serializer = UserProfileSerializer(user)

            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": f"Une erreur est survenue: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            user = request.user  # L'utilisateur authentifié

            # Sérialiser les données reçues et valider
            serializer = UserProfileSerializer(user, data=request.data, partial=True)  # Utilisez partial=True pour la mise à jour partielle
            if serializer.is_valid():
                # Mettre à jour l'utilisateur
                serializer.save()  # Cela va appeler la méthode update du sérialiseur

                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Une erreur est survenue: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import generics, permissions
from capteurs.models import ZoneSecurite
from .serializers import ZoneSecuriteStatistiquesSerializer

class ZoneSecuriteStatistiquesView(generics.ListAPIView):
    serializer_class = ZoneSecuriteStatistiquesSerializer
    permission_classes = [permissions.IsAuthenticated]  # ✅ S'assurer que l'utilisateur est connecté

    def get_queryset(self):
        """
        Récupère les zones de sécurité de l'utilisateur connecté
        """
        user = self.request.user  # ✅ Prendre l'utilisateur connecté
        return ZoneSecurite.objects.filter(user=user)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from capteurs.models import Capteur
from .serializers import CapteurSerializer

class CapteurListAPIView(APIView):
    def get(self, request):
        user = request.user  # utilisateur connecté
        
        # Récupérer les capteurs associés aux zones de cet utilisateur
        capteurs = Capteur.objects.filter(zone_securite__user=user)
        
        serialized_capteurs = CapteurSerializer(capteurs, many=True).data
        
        return Response(serialized_capteurs, status=status.HTTP_200_OK)



from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from capteurs.models import Message
from .serializers import MessageSerializer

class MessageListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]  # Assurez-vous que l'utilisateur est authentifié

    def get_queryset(self):
        """
        Récupère uniquement les messages liés à l'utilisateur authentifié.
        """
        user = self.request.user  # Récupère l'utilisateur authentifié à partir du token
        return Message.objects.filter(user=user).order_by('-date_heure')  # Trier les messages du plus récent au plus ancien


# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from capteurs.models import Message

@api_view(['PATCH'])
def mark_message_as_read(request, pk):
    """
    Marque un message comme lu.
    Cette vue est appelée avec une méthode PATCH pour mettre à jour le statut 'is_read' du message.
    """
    try:
        # Récupérer le message par son ID
        message = Message.objects.get(pk=pk)
    except Message.DoesNotExist:
        # Si le message n'existe pas, retourner une erreur 404
        return Response({"detail": "Message not found."}, status=status.HTTP_404_NOT_FOUND)

    # Mettre à jour le champ 'is_read' du message
    message.is_read = True
    message.save()

    # Retourner une réponse positive
    return Response({"detail": "Message marked as read."}, status=status.HTTP_200_OK)



# realtime/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@api_view(['POST'])
def receive_gps(request):
    lat = request.data.get('lat')
    lng = request.data.get('lng')

    if lat is not None and lng is not None:
        # Envoi en temps réel via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "gps_data",
            {
                "type": "gps_position",
                "lat": lat,
                "lng": lng,
            }
        )
        return Response({"status": "Position reçue", "lat": lat, "lng": lng})
    else:
        return Response({"error": "Latitude ou longitude manquante"}, status=400)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['POST'])
def mettre_a_jour_position(request):
    identifiant = request.data.get('identifiant')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if not all([identifiant, latitude, longitude]):
        return Response({'error': 'Champs requis : identifiant, latitude, longitude.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        capteur = Capteur.objects.get(identifiant=identifiant)
        capteur.latitude = latitude
        capteur.longitude = longitude
        capteur.save()
        return Response({'message': 'Coordonnées mises à jour avec succès.'})
    except Capteur.DoesNotExist:
        return Response({'error': 'Capteur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from capteurs.models import ZoneSecurite
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from capteurs.models import ZoneSecurite
from rest_framework.permissions import IsAuthenticated
import json

@api_view(['GET'])
def suivre_betail_api(request):
    user = request.user  # Récupère l'utilisateur authentifié via le token

    if not user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=401)

    # Par défaut : ses propres zones
    related_users = [user]

    # Si l'utilisateur est un parent (donc sans owner)
    if not user.owner:
        related_users += list(user.sub_users.all())

    # On filtre les zones selon l'utilisateur ou ses sub-users (si c’est un parent)
    zones = ZoneSecurite.objects.filter(user__in=related_users)

    zones_data = []
    for zone in zones:
        # Conversion du champ 'coins' si nécessaire
        try:
            coins = json.loads(zone.coins) if zone.coins else None
        except json.JSONDecodeError:
            coins = None

        zones_data.append({
            'id': zone.id,
            'forme': zone.forme,
            'latitude': zone.latitude,
            'longitude': zone.longitude,
            'rayon': zone.rayon,
            'coin1_lat': zone.coin1_lat,
            'coin1_lon': zone.coin1_lon,
            'coin2_lat': zone.coin2_lat,
            'coin2_lon': zone.coin2_lon,
            'coin3_lat': zone.coin3_lat,
            'coin3_lon': zone.coin3_lon,
            'coin4_lat': zone.coin4_lat,
            'coin4_lon': zone.coin4_lon,
            'coins': coins,  # Données de coins converties
        })

    return Response({'zones_data': zones_data})


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UnreadMessagesCountSerializer
from capteurs.models import Message
from rest_framework import serializers

class UnreadMessagesCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()

class UnreadMessagesCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.sub_users.exists():
            user_ids = [user.id] + list(user.sub_users.values_list('id', flat=True))
        else:
            user_ids = [user.id]

        unread_count = Message.objects.filter(user_id__in=user_ids, is_read=False).count()

        serializer = UnreadMessagesCountSerializer({'unread_count': unread_count})
        return Response(serializer.data)
