from django.contrib import admin
from django.urls import path
from . import views
from .views import *  # Importez votre vue ici
from django.contrib.auth.views import LogoutView  # Assurez-vous d'importer LogoutView
from .views import MotDePasseOublieView
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('login/', ConnexionView.as_view(), name='login'),  # URL pour la connexion
    # Vous pouvez ajouter d'autres URLs pour d'autres vues
    path('inscription/', InscriptionView.as_view(), name="inscription"),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('mot-de-passe-oublie/', MotDePasseOublieView.as_view(), name='mot_de_passe_oublie'),
    path('mot-de-passe-oublie/', MotDePasseOublieView.as_view(), name='mot_de_passe_oublie'),
     # URLs par défaut de Django pour la gestion des mots de passe
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),


    path('liste_des_utilisateurs/',UserListView.as_view(),name="liste_des_utilisateurs"),
    path('utilisateurs/ajouter_utilisateur', CreateUtilisateurView.as_view(), name="ajouter_utilisateur"),
    
    path('utilisateurs/detail_utilisateur/<int:pk>/', UserDetailView.as_view(), name='detail_utilisateur'),
    path('utilisateurs/profil_utilisateur/<int:pk>/', UserProfilView.as_view(), name='profil_utilisateur'),
    path('utilisateurs/modifier_utilisateur/<int:pk>/', ModifierUtilisateurView.as_view(), name='modifier_utilisateur'),
    path('utilisateurs/supprimer_utilisateur/<int:user_id>/', views.delete_user, name='supprimer_utilisateur'),



    path('liste_des_roles',UserRolesListView.as_view(),name="liste_des_roles"),
    path('roles/detail_role/<int:pk>/', RoleDetailView.as_view(), name='detail_role'),
    path('roles/ajouter_role/', RoleCreateView.as_view(), name='ajouter_role'),
    path('roles/modifier_role/<int:pk>/', RoleUpdateView.as_view(), name='modifier_role'),
    path('roles/supprimer_role/<int:pk>/',views.delete_role, name='supprimer_role'),
    path('roles/permissions_role/<int:id>/', views.get_role_permissions, name='role_permissions'),

]
