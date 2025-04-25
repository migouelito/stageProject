from django.urls import path
from .views import gps_map_view

urlpatterns = [
    path('map/', gps_map_view, name='gps-map'),
]
