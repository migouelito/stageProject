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
    
    
    @staticmethod
    def get_chefs_d_elevage_et_nb_fils():
        """
        Retourne une liste de dictionnaires contenant les utilisateurs qui :
        - ne sont pas superutilisateurs
        - ne sont pas des sous-utilisateurs (owner=None)
        Pour chaque utilisateur, on retourne :
        - son prénom
        - son nom
        - le nombre de sous-utilisateurs (fils) associés
        """
        users = User.objects.filter(is_superuser=False, owner__isnull=True)
        resultats = []

        for user in users:
            resultats.append({
                "prenom": user.first_name,
                "nom": user.last_name,
                "nombre_fils": user.sub_users.count()
            })

        return resultats

    