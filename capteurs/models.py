from django.db import models
from utilisateurs.models import User
from django.db import models
from utilisateurs.models import User

from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D  # Utilisation de GeoDjango pour les unités de distance
from math import sqrt
from django.utils import timezone
   #Methode pour les calculs
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic  # ✅ Pour le calcul réel de distance
import json
from  django.db.models import PROTECT


class ZoneSecurite(models.Model):
    FORMES_CHOICES = [
        ('cercle', 'Cercle'),
        ('triangle', 'Triangle'),
        ('carre', 'Carré'),
        ('rectangle', 'Rectangle'),  # ✅ Ajout du rectangle
        ('polygon', 'Polygone'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='zones')
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    forme = models.CharField(max_length=10, choices=FORMES_CHOICES, default='cercle')
    is_pred = models.BooleanField(default=True)  # ✅ nouvelle colonne ajoutée
    is_zone = models.BooleanField(default=True)
    active_securite=models.BooleanField(default=False)
    # Pour le cercle
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    rayon = models.FloatField(null=True, blank=True)  # En mètres

    # Pour le triangle, carré, rectangle
    coin1_lat = models.FloatField(null=True, blank=True)
    coin1_lon = models.FloatField(null=True, blank=True)
    coin2_lat = models.FloatField(null=True, blank=True)
    coin2_lon = models.FloatField(null=True, blank=True)
    coin3_lat = models.FloatField(null=True, blank=True)
    coin3_lon = models.FloatField(null=True, blank=True)
    coin4_lat = models.FloatField(null=True, blank=True)  # ✅ Pour rectangle
    coin4_lon = models.FloatField(null=True, blank=True)  # ✅ Pour rectangle


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'nom'], name='unique_nom_par_utilisateur')
        ]
    # Pour les polygones génériques
    coins = models.JSONField(null=True, blank=True)  # Liste [(lat, lon), ...]
    def __str__(self):
        return f'{self.nom}'
    
    def point_dans_zone(self, latitude, longitude):
        """
        Vérifie si un point (latitude, longitude) est dans la zone de sécurité.
        Retourne True si le point est dans la zone, False sinon.
        """
        if not all([latitude, longitude]):
            return False

        point = Point(longitude, latitude)

        if self.forme == 'cercle':
            if None in [self.latitude, self.longitude, self.rayon]:
                return False
            centre_coords = (self.latitude, self.longitude)
            point_coords = (latitude, longitude)
            distance = geodesic(centre_coords, point_coords).meters  # ✅ Distance réelle
            return distance <= self.rayon

        elif self.forme == 'triangle':
            if any(x is None for x in [self.coin1_lat, self.coin1_lon, self.coin2_lat, self.coin2_lon, self.coin3_lat, self.coin3_lon]):
                return False
            coords = [
                (self.coin1_lon, self.coin1_lat),
                (self.coin2_lon, self.coin2_lat),
                (self.coin3_lon, self.coin3_lat),
                (self.coin1_lon, self.coin1_lat),
            ]
        elif self.forme in ['carre', 'rectangle']:
            if any(x is None for x in [self.coin1_lat, self.coin1_lon, self.coin2_lat, self.coin2_lon, self.coin3_lat, self.coin3_lon, self.coin4_lat, self.coin4_lon]):
                return False
            coords = [
                (self.coin1_lon, self.coin1_lat),
                (self.coin2_lon, self.coin2_lat),
                (self.coin3_lon, self.coin3_lat),
                (self.coin4_lon, self.coin4_lat),
                (self.coin1_lon, self.coin1_lat),
            ]
        elif self.forme == 'polygon':
            if not self.coins:
                return False
            try:
                coords = [(lon, lat) for lat, lon in self.coins]
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
            except Exception:
                return False
        else:
            return False

        try:
            polygon = Polygon(coords)
            return polygon.contains(point) or polygon.touches(point)
        except Exception:
            return False

class Animal(models.Model):
    type_animal = models.CharField(max_length=20, unique=True)
    image = models.ImageField(upload_to='capteurs/', null=True, blank=True)

    def __str__(self):
        return self.type_animal

    def save(self, *args, **kwargs):
        # Nettoie et met la première lettre en majuscule, le reste en minuscule
        self.type_animal = self.type_animal.strip().capitalize()
        super().save(*args, **kwargs)



class Capteur(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='capteurs')
    identifiant = models.IntegerField(unique=True)
    type_animal = models.ForeignKey(Animal, on_delete=PROTECT)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_zone = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)
    zone_securite = models.ForeignKey(ZoneSecurite, on_delete=models.SET_NULL, null=True, blank=True)

  

    def __str__(self):
        return f"Capteur {self.identifiant} - {self.type_animal} - Utilisateur: {self.user.username}"

    @classmethod
    def get_capteurs_for_user(cls, user: User):
        """
        - Si parent (user.owner is None)   : retourne **tous** les capteurs de user.
        - Si sous‑utilisateur (user.owner) : retourne uniquement les capteurs
          dont zone_securite est dans user.zones.all()
        """
        if not user.is_authenticated:
            return cls.objects.none()

        # Sous‑utilisateur → ne voir **que** les capteurs assignés à SES zones
        if user.owner is not None:
            return cls.objects.filter(
                zone_securite__in=user.zones.all(),
                zone_securite__isnull=False
            )
        # Parent → tous ses capteurs
        return cls.objects.filter(user=user)
   

 



    @classmethod
    def is_capteur_in_zone(cls, identifiant, lat_capteur, lon_capteur):
        try:
            capteur = cls.objects.get(identifiant=identifiant)
            zone = capteur.zone_securite

            print(f"📍 Capteur {identifiant} - Position fournie : ({lat_capteur}, {lon_capteur})")

            if not zone:
                print("❗ Ce capteur n'a pas de zone de sécurité assignée.")
                return False

            if not zone.active_securite:
                print("❗ La zone de sécurité n'est pas activée.")
                return False
        
            print(f"📌 Zone de sécurité '{zone.nom}' - Forme : {zone.forme}")

            # Si la forme de la zone est 'cercle'
            if zone.forme == 'cercle':
                print(f" ➤ Centre : ({zone.latitude}, {zone.longitude}), Rayon : {zone.rayon}m")
                centre_coords = (zone.latitude, zone.longitude)
                point_coords = (lat_capteur, lon_capteur)
                distance = geodesic(centre_coords, point_coords).meters  # ✅ Précis
                in_zone = distance <= zone.rayon

            # Si la forme est un rectangle, carré ou triangle
            elif zone.forme in ['triangle', 'carre', 'rectangle']:
                print(" ➤ Coins :")
                coords = [
                    (zone.coin1_lat, zone.coin1_lon),
                    (zone.coin2_lat, zone.coin2_lon),
                    (zone.coin3_lat, zone.coin3_lon)
                ]
                if zone.forme in ['carre', 'rectangle']:
                    coords.append((zone.coin4_lat, zone.coin4_lon))
                coords.append(coords[0])  # Fermeture du polygone pour le calcul
                print(f" ➤ Coordonnées des coins : {coords}")
                polygon = Polygon(coords)
                point = Point(lon_capteur, lat_capteur)
                in_zone = polygon.contains(point)

            # Si la forme est un polygone
            elif zone.forme == 'polygon':
                print(" ➤ Points du polygone :")
                # Conversion de la chaîne JSON en une liste Python
                coins = json.loads(zone.coins)  # Transformation de la chaîne en liste de coordonnées
                print(f" ➤ Coins après conversion : {coins}")
                
                # Transformer les coordonnées pour le polygone
                coords = [(lon, lat) for lat, lon in coins]
                if coords[0] != coords[-1]:
                    coords.append(coords[0])  # Fermeture du polygone
                print(f" ➤ Coordonnées du polygone : {coords}")
                polygon = Polygon(coords)
                point = Point(lon_capteur, lat_capteur)
                in_zone = polygon.contains(point)

            else:
                print("❌ Forme de zone non gérée.")
                return False

            print("✅ Résultat : Le capteur est **dans** la zone." if in_zone else "❌ Résultat : Le capteur est **hors** de la zone.")

            capteur.last_seen = timezone.now()
            capteur.is_zone = in_zone
            capteur.save()
            return in_zone

        except cls.DoesNotExist:
            print(f"❌ Aucun capteur avec l'identifiant {identifiant} trouvé.")
            return False

            
    @classmethod
    def get_zone_info_for_capteur(cls, identifiant):
        """
        Retourne un dictionnaire contenant la forme et les coordonnées de la zone de sécurité
        associée à un capteur donné. Sinon retourne None.
        """
        try:
            capteur = cls.objects.get(identifiant=identifiant)
            zone = capteur.zone_securite
            if not zone:
                return None

            info = {'forme': zone.forme}

            if zone.forme == 'cercle':
                info['centre'] = {'lat': zone.latitude, 'lon': zone.longitude}
                info['rayon'] = zone.rayon

            elif zone.forme in ['triangle', 'carre', 'rectangle']:
                coords = [
                    {'lat': zone.coin1_lat, 'lon': zone.coin1_lon},
                    {'lat': zone.coin2_lat, 'lon': zone.coin2_lon},
                    {'lat': zone.coin3_lat, 'lon': zone.coin3_lon}
                ]
                if zone.forme in ['carre', 'rectangle']:
                    coords.append({'lat': zone.coin4_lat, 'lon': zone.coin4_lon})
                info['coins'] = coords

            elif zone.forme == 'polygon':
                info['coins'] = [{'lat': lat, 'lon': lon} for lat, lon in zone.coins]

            return info
        except cls.DoesNotExist:
            return None
        except Exception as e:
            return None
    #Methode ppur vefier l'objet est dans sa zone de securite

   


class Message(models.Model):
    """Message d’alerte lié à une zone (pas directement au capteur)"""
    
    zone = models.ForeignKey(ZoneSecurite, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    
    corps_message = models.TextField()
    is_read = models.BooleanField(default=False)
    date_heure = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message pour zone {self.zone.nom} ({self.zone.user.username}) à {self.date_heure}"

from django.db.models import Count
from .models import Animal, Capteur
from django.db.models import Count

from django.db.models import Count
from django.db.models import Count
from .models import Animal, Capteur, ZoneSecurite

class Statistiques:
    @staticmethod
    def nombre_capteurs_par_animal(user):
        animaux = Animal.objects.all()
        animal_dict = {animal.id: animal.type_animal for animal in animaux}

        if user.owner is None:
            # Cas propriétaire : récupérer ses capteurs + ceux de ses sub-users
            utilisateurs = user.get_all_related_users()
            capteurs = Capteur.objects.filter(user__in=utilisateurs)
        else:
            # Cas sous-utilisateur : capteurs liés à ses zones uniquement (peu importe le propriétaire)
            zones_utilisateur = ZoneSecurite.objects.filter(user=user)
            capteurs = Capteur.objects.filter(zone_securite__in=zones_utilisateur)

        stats = (
            capteurs
            .values('type_animal_id')
            .annotate(total=Count('id'))
        )

        resultat = {animal_name: 0 for animal_name in animal_dict.values()}
        for stat in stats:
            animal_id = stat['type_animal_id']
            animal_nom = animal_dict.get(animal_id)
            if animal_nom:
                resultat[animal_nom] = stat['total']

        return resultat

    @staticmethod
    def nombre_capteurs_actifs(user):
        if user.owner is None:
            # Propriétaire - tous les capteurs de son groupe
            utilisateurs = user.get_all_related_users()
            return Capteur.objects.filter(user__in=utilisateurs, actif=True).count()
        else:
            # Sous-utilisateur - capteurs dans ses zones (peu importe le propriétaire)
            zones_utilisateur = ZoneSecurite.objects.filter(user=user)
            return Capteur.objects.filter(zone_securite__in=zones_utilisateur, actif=True).count()

    @staticmethod
    def nombre_capteurs_inactifs(user):
        if user.owner is None:
            # Propriétaire - tous les capteurs de son groupe
            utilisateurs = user.get_all_related_users()
            return Capteur.objects.filter(user__in=utilisateurs, actif=False).count()
        else:
            # Sous-utilisateur - capteurs dans ses zones (peu importe le propriétaire)
            zones_utilisateur = ZoneSecurite.objects.filter(user=user)
            return Capteur.objects.filter(zone_securite__in=zones_utilisateur, actif=False).count()
        
   
    @staticmethod
    def statistique_zone(user):
        """
        Récupère le nombre de capteurs actifs, inactifs et le nombre total d'animaux
        pour chaque zone de sécurité associée à un utilisateur (propriétaire ou sous-utilisateur).
        """
        if user.owner is None:
            # Cas propriétaire : récupérer les zones de sécurité des sub-utilisateurs
            utilisateurs = user.get_all_related_users()
            zones_utilisateur = ZoneSecurite.objects.filter(user__in=utilisateurs)
        else:
            # Cas sous-utilisateur : récupérer uniquement ses zones de sécurité
            zones_utilisateur = ZoneSecurite.objects.filter(user=user)

        statistiques = {}

        for zone in zones_utilisateur:
            # Compter les capteurs actifs et inactifs pour cette zone
            capteurs_actifs = Capteur.objects.filter(zone_securite=zone, actif=True).count()
            capteurs_inactifs = Capteur.objects.filter(zone_securite=zone, actif=False).count()

            # Compter le nombre total d'animaux (capteurs) pour cette zone
            total_animaux = Capteur.objects.filter(zone_securite=zone).count()

            # Ajouter les statistiques de cette zone dans le dictionnaire
            statistiques[zone.nom] = {
                "actifs": capteurs_actifs,
                "inactifs": capteurs_inactifs,
                "total_animaux": total_animaux  # Ajout du nombre total d'animaux
            }

        return statistiques
