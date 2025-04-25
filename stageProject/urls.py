from django.contrib import admin
from django.urls import path,include
from .views import homePage,unread_messages_count,Parametre_view
from capteurs.views import dashboard

from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', lambda request: redirect('login'), name=''),  # Redirige vers connexion
    path('admin/', admin.site.urls),
    path('accueil',dashboard, name='homePage'),  # Accéder à la page d'accueil via l'URL racine
    path('', include('utilisateurs.urls')),  # Inclure les URLs de l'application 'stageProject'
    path('', include('api.urls')),
    path('', include('capteurs.urls')),  # Inclure les URLs de l'application 'stageProject'
    path('ajax/unread_messages_count/', unread_messages_count, name='unread_messages_count'),
    path('parametre', Parametre_view,name='parametre'),
      path('', include('realtime.urls')),

]
# Ajouter les fichiers statiques et médias en mode développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)