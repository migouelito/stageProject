
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'telephone', 'password']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        # Valide le mot de passe s’il est fourni
        if password:
            try:
                validate_password(password, user=instance)
            except ValidationError as e:
                raise serializers.ValidationError({'password': e.messages})

        # Met à jour les autres champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Applique le mot de passe seulement s’il est valide
        if password:
            instance.set_password(password)

        instance.save()
        return instance



from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'telephone', 'owner']


class EmailTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email invalide")

        user = authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError("Mot de passe incorrect")

        attrs['user'] = user
        return attrs



from rest_framework import serializers
from capteurs.models import ZoneSecurite, Capteur, Animal

class ZoneSecuriteStatistiquesSerializer(serializers.ModelSerializer):
    capteurs_actifs = serializers.SerializerMethodField()
    capteurs_inactifs = serializers.SerializerMethodField()
    repartition_animaux = serializers.SerializerMethodField()
    total_capteurs = serializers.SerializerMethodField()

    class Meta:
        model = ZoneSecurite
        fields = ['id', 'nom', 'capteurs_actifs', 'capteurs_inactifs', 'repartition_animaux', 'total_capteurs']

    def get_capteurs_actifs(self, obj):
        return Capteur.objects.filter(zone_securite=obj, actif=True).count()

    def get_capteurs_inactifs(self, obj):
        return Capteur.objects.filter(zone_securite=obj, actif=False).count()

    def get_repartition_animaux(self, obj):
        repartition = []
        for animal in Animal.objects.all():  # Récupérer les types d'animaux via la base de données
            type_count = Capteur.objects.filter(zone_securite=obj, type_animal=animal).count()
            if type_count > 0:  # Ne prendre que les types avec au moins 1 capteur
                repartition.append({
                    'type_animal': animal.type_animal,
                    'nombre': type_count
                })
        return repartition

    def get_total_capteurs(self, obj):
        return Capteur.objects.filter(zone_securite=obj).count()

    @classmethod
    def from_user(cls, user):
        # Récupérer les zones de sécurité associées à l'utilisateur
        zones = ZoneSecurite.objects.filter(user=user)
        # Sérialiser les zones de sécurité
        return cls(zones, many=True).data




from rest_framework import serializers
from capteurs.models import Capteur, Animal

class CapteurSerializer(serializers.ModelSerializer):
    # Renvoyer le nom de l'animal (pas son ID)
    type_animal = serializers.CharField(source='type_animal.type_animal', read_only=True)

    class Meta:
        model = Capteur
        fields = ['id', 'identifiant', 'type_animal', 'actif']
# Inclut l'identifiant, le type d'animal (nom), et l'actif

from rest_framework import serializers
from capteurs.models import Message

class MessageSerializer(serializers.ModelSerializer):
    # Ajouter un champ qui récupère seulement le nom de la zone
    zone_name = serializers.CharField(source='zone.nom', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'user', 'zone_name', 'corps_message', 'is_read', 'date_heure']


class UnreadMessagesCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
