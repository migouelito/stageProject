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

from rest_framework.permissions import AllowAny  # Importer AllowAny
from utilisateurs.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer

class UserProfileView(APIView):
    permission_classes = [AllowAny]  # Désactive l'authentification pour cette vue

    def get(self, request, username):
        try:
            # Essayer de récupérer l'utilisateur par le nom d'utilisateur
            user = User.objects.filter(username=username).first()

            if user is None:
                # Si l'utilisateur n'est pas trouvé, retourner une erreur
                return Response({"detail": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)

            # Sérialisation des données utilisateur
            serializer = UserSerializer(user)

            # Retourner les données sérialisées
            return Response(serializer.data)

        except Exception as e:
            # Si une exception est levée, renvoyer une erreur générique
            return Response({"detail": f"Une erreur est survenue: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AnimalCountSerializer

class AnimalCountView(APIView):
    def get(self, request):
        # Obtenir le comptage des capteurs par type d'animal
        count_by_animal = AnimalCountSerializer.get_animal_count()

        # Sérialiser la réponse
        serializer = AnimalCountSerializer(count_by_animal, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from capteurs.models import Capteur
from .serializers import CapteurSerializer

class CapteurListAPIView(APIView):
    def get(self, request):
        # Récupérer tous les capteurs de la base de données
        capteurs = Capteur.objects.all()
        
        # Sérialiser les capteurs
        serialized_capteurs = CapteurSerializer(capteurs, many=True).data
        
        # Retourner les capteurs sous forme de réponse JSON
        return Response(serialized_capteurs, status=status.HTTP_200_OK)


# views.py
from rest_framework import generics
from capteurs.models import Message
from .serializers import MessageSerializer

class MessageListCreateAPIView(generics.ListCreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        """
        Optionnellement filtrer les messages par un capteur spécifique
        """
        queryset = Message.objects.all()
        capteur_id = self.request.query_params.get('capteur_id', None)
        if capteur_id is not None:
            queryset = queryset.filter(identifiant_capteur__identifiant=capteur_id)
        return queryset


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
