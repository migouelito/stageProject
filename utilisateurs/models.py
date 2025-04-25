from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=False)
    telephone = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    owner = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='sub_users')

    # Définir l'email comme identifiant principal
    USERNAME_FIELD = 'email'  # Utilise l'email pour l'authentification
    REQUIRED_FIELDS = ['username']  # L'username est toujours requis, mais pas comme identifiant principal

    def __str__(self):
        return self.username
    
  
    def get_all_related_users(self):
        users = [self]

        # Ajoute les sous-utilisateurs si l'utilisateur est un parent
        if self.sub_users.exists():
            users.extend(self.sub_users.all())

        # Ajoute le parent si l'utilisateur est un fils
        if self.owner:
            users.append(self.owner)

            # Ajoute les frères si l'utilisateur est un fils (sous-utilisateurs du même parent)
            users.extend(self.owner.sub_users.exclude(id=self.id))  # Exclut l'utilisateur actuel de la liste des frères

        # Retourne une liste de tous les utilisateurs associés
        return User.objects.filter(id__in=[u.id for u in users])
    

    