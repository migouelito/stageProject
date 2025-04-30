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
    path('api/user/', UserInfoView.as_view(), name='user_info'), 
    path('api/user/<str:username>/', UserProfileView.as_view(), name='user-profile'),

       # autres urls
    path('api/protected/', ProtectedView.as_view(), name='protected_view'),
    path('api/statistique/', ZoneSecuriteStatistiquesView.as_view(), name='statistique'),
    path('api/capteurs/', CapteurListAPIView.as_view(), name='liste_des_capteurs'),
    path('api/suivre-betail/', views.suivre_betail_api, name='suivre_betail_api'),
    path('api/messages/', MessageListCreateAPIView.as_view(), name='message-list-create'),
    path('api/messages/<int:pk>/read/', mark_message_as_read, name='mark-message-as-read'),
    path('api/position/', receive_gps, name='receive_gps'),
    path('api/capteur/update-position/', mettre_a_jour_position, name='update_capteur_position'),
    path('api/suivre/', views.suivre_betail_api, name='suivre_betail'),  # Pas besoin de user_id dans l'URL
      ]      
