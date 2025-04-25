from django.contrib import admin
from .models import Capteur,ZoneSecurite


admin.site.register(Capteur)  # Cela ajoute le modèle à l'interface admin


admin.site.register(ZoneSecurite)  # Cela ajoute le modèle à l'interface admin

# Register your models here.
