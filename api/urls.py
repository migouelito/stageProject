# urls.py
from . import views
from .views import *
from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from .views import UserProfileView

urlpatterns = [
    # Endpoint pour obtenir un token d'accès et un token de rafraîchissement
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
 
   path('api/user/<str:username>/', UserProfileView.as_view(), name='user-profile'),

       # autres urls
    path('api/protected/', ProtectedView.as_view(), name='protected_view'),
    path('api/animal-count/', AnimalCountView.as_view(), name='animal_count'),# api pour compter le nombre d'animaux
    path('api/capteurs/', CapteurListAPIView.as_view(), name='capteur-list'),#api pour lister les capteurs 
    path('api/messages/', MessageListCreateAPIView.as_view(), name='message-list-create'),
    path('api/messages/<int:pk>/read/', mark_message_as_read, name='mark-message-as-read'),
    path('api/position/', receive_gps, name='receive_gps'),
    path('api/capteur/update-position/', mettre_a_jour_position, name='update_capteur_position'),
    ]
