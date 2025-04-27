# capteur/context_processors.py
from django.conf import settings

def global_variables(request):
    return {
        'MY_GLOBAL_VARIABLE': settings.MY_GLOBAL_VARIABLE  # ici, tu utilises ta variable du settings.py
    }
