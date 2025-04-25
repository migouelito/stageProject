# api/views.py (ou autre fichier de vues)

from django.shortcuts import render

def gps_map_view(request):
    return render(request, 'realtime/gps_map.html')
