
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *  

urlpatterns = [
     path('capteurs/animaux/', AnimalListView.as_view(), name='liste_des_animaux'),  # URL pour la vue de la liste des animaux
     path('capteurs/ajouter_animal/', ajouter_animal, name='ajouter_animal'),  # URL pour la vue de la liste des animaux
    path('capteurs/modifier_animal/<int:animal_id>/', modifier_animal, name='modifier_animal'),
    path('capteurs/supprimer_animal/<int:animal_id>/',supprimer_animal, name='supprimer_animal'),
    path('capteurs/liste_des_capteurs/', CapteursListView.as_view(), name='liste_des_capteurs'),  # URL correcte
    path('capteurs/ajouter_capteur/', AjoutCapteursView.as_view(), name='ajouter_capteur'),
    path('capteurs/supprimer_capteur/', AjoutCapteursView.as_view(), name='supprimer_capteur'),
    path('supprimer-capteur/<int:capteur_id>/', supprimer_capteur, name='supprimer_capteur'),
    path('capteurs/modifier_capteur/<int:pk>/', ModifierCapteurView.as_view(), name='modifier_capteur'),
    path('capteurs/detail_capteur/<int:pk>/', DetailCapteurView.as_view(), name='detail_capteur'),
    path('statistique/', dashboard, name='Statistique'),

    path('capteurs/message', MessageListView.as_view(), name="notifications"),
    path('capteurs/marquer_comme_lu/<int:message_id>/', MarquerCommeLuView.as_view(), name='marquer_comme_lu'),
    path('capteurs/delete_message/<int:message_id>/',supprimer_message, name='supprimer_message'),

    path('zone/liste_des_zones', ListeDesZones.as_view(),name="liste_des_zones"),
    path("zone/creer_zone", creer_zone, name="creer_zone"),
      path('zones/modifier_zone/<int:pk>/', modifier_zone, name='modifier_zone'),
    path('zones/supprimer/<int:zone_id>/', supprimer_zone, name='supprimer_zone'),


     # urls.py
    path('zone/securite/<int:user_id>/<int:zone_id>/', ZoneSecuriteView.as_view(), name="zone_securite"),
    path('zone/localisation_betail', ZoneSecuriteView.as_view(),name="localisation_betail"),
    path('zones/updateposition/<int:zone_id>/', update_position, name='update_position'),

    #route api
    path('api/position/', recevoir_position, name='recevoir_position'),
    path('suivrebetail/<int:user_id>/', suivreBetail, name='suivrebetail'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    

