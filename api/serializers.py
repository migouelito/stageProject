
from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


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
from django.db.models import Count, Q
from capteurs.models import Capteur

class AnimalCountSerializer(serializers.Serializer):
    type_animal = serializers.CharField()
    total = serializers.IntegerField()
    actifs = serializers.IntegerField()
    inactifs = serializers.IntegerField()

    @staticmethod
    def get_animal_count():
        animal_counts = (
            Capteur.objects
            .values('type_animal')
            .annotate(
                total=Count('id'),
                actifs=Count('id', filter=Q(actif=True)),
                inactifs=Count('id', filter=Q(actif=False))
            )
            .order_by('type_animal')
        )
        return animal_counts




from rest_framework import serializers
from capteurs.models import Capteur

class CapteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capteur
        fields = ['id','identifiant', 'type_animal', 'actif']  # Inclut l'identifiant et le type d'animal


# serializers.py
from rest_framework import serializers
from capteurs.models import Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id','identifiant_capteur', 'corps_message', 'is_read', 'date_heure']



