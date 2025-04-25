from django.contrib import admin
from .models import User  # Ou un autre modèle


admin.site.register(User)  # Cela ajoute le modèle à l'interface admin

