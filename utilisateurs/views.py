from django.urls import reverse_lazy
from django.views.generic import CreateView

from .models import User
from django.contrib.auth.models import Group



from django.contrib.auth.views import LoginView


from django.urls import reverse_lazy
from .forms import LoginForm  # Importation du formulaire personnalisé

class ConnexionView(LoginView):
    template_name = 'login.html'
    authentication_form = LoginForm  # Utiliser le formulaire personnalisé
    redirect_authenticated_user = True
    next_page = reverse_lazy('homePage')



from django.contrib import messages

from .forms import InscriptionForm

class InscriptionView(CreateView):
    model = User
    form_class = InscriptionForm  # Formulaire personnalisé
    template_name = 'utilisateurs/creer_compte.html'  # Template pour afficher le formulaire
    success_url = reverse_lazy('login')  # Redirection après une inscription réussie

    def form_valid(self, form):
        # Si le formulaire est valide, nous le sauvegardons et envoyons un message de succès
        response = super().form_valid(form)
        messages.success(self.request, "Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.")
        return response

    def form_invalid(self, form):
        # Si le formulaire est invalide, on envoie un message d'erreur
        response = super().form_invalid(form)
        messages.error(self.request, "Erreur lors de la création du compte. Veuillez vérifier les informations.")
        return response
    
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import PasswordResetFormCustom  # Formulaire personnalisé

class MotDePasseOublieView(PasswordResetView):
    template_name = 'utilisateurs/mot_de_passe_oublie.html'  # Page du formulaire
    form_class = PasswordResetFormCustom  # Formulaire personnalisé
    success_url = reverse_lazy('login')  # Redirection après validation

    def form_valid(self, form):
        """Affiche un message de succès après l'envoi du mail."""
        messages.success(self.request, "Un e-mail de réinitialisation a été envoyé.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Affiche un message d'erreur si l'email est introuvable."""
        messages.error(self.request, "Adresse e-mail introuvable. Veuillez réessayer.")
        return super().form_invalid(form)



from django.contrib.auth.views import LogoutView

from django.shortcuts import redirect
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')  # Redirection après déconnexion

    def dispatch(self, request, *args, **kwargs):
        # Affiche un message de confirmation de déconnexion
        messages.info(request, "Vous êtes maintenant déconnecté.")
        # Redirige manuellement si nécessaire
        return redirect(self.next_page)


from django.views.generic import ListView


from django.contrib.auth.mixins import PermissionRequiredMixin

from .forms import UserRoleForm



class UserRolesListView(PermissionRequiredMixin, ListView):
    """Affiche la liste des rôles des utilisateurs liés à l'utilisateur connecté"""
    model = Group
    context_object_name = 'roles'
    permission_required = 'auth.view_group'

    def get_queryset(self):
        # Retourne tous les rôles sans filtrer par utilisateur
        return Group.objects.all()

    def get_template_names(self):
        """Choisir dynamiquement le template selon que l'utilisateur est superuser ou non"""
        if self.request.user.is_superuser:
            return ['utilisateurs/liste_des_roles_admin.html']
        return ['utilisateurs/liste_des_roles.html']

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "Vous devez être connecté pour accéder à cette page.")
            return redirect('login')
        messages.error(self.request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect('homePage')


from django.views.generic import DetailView





from django.views.generic.edit import CreateView, UpdateView


from django.contrib.auth.models import Permission



from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404

from django.contrib import messages
from .forms import UserRoleForm

class RoleDetailView(PermissionRequiredMixin, DetailView):
    model = Group
    template_name = 'utilisateurs/detail_role.html'  # Remplace par le bon chemin
    context_object_name = 'role'
    permission_required = 'utilisateurs.view.user'  # Vérifie si l'utilisateur peut voir les rôles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = self.object.permissions.all()  # Récupère les permissions du groupe
        return context


class RoleCreateView(PermissionRequiredMixin, CreateView):
    model = Group
    form_class = UserRoleForm
    template_name = 'utilisateurs/ajouter_role.html'
    context_object_name = 'role'
    permission_required = 'auth.add_group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = Permission.objects.all()
        context['roles'] = Group.objects.all()
        context['edit_mode'] = False  # Mode ajout
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        # Message de succès
        messages.success(self.request, f"Le rôle '{self.object.name}' a été créé avec succès.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Il y a des erreurs dans le formulaire.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('liste_des_roles')




class RoleUpdateView(PermissionRequiredMixin, UpdateView):
    model = Group
    form_class = UserRoleForm
    template_name = 'utilisateurs/modifier_role.html'
    context_object_name = 'role'
    permission_required = 'auth.change_group'  
    raise_exception = False  

    def handle_no_permission(self):
        """Affiche un message d'erreur si l'utilisateur n'a pas les droits"""
        messages.error(self.request, "Vous n'avez pas la permission de modifier un rôle.")
        return redirect('liste_des_roles')  

    def form_valid(self, form):
        """Affiche un message de succès après modification"""
        messages.success(self.request, "Le rôle a été mis à jour avec succès !")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = self.get_object()
        context['permissions'] = Permission.objects.all()
        context['roles'] = Group.objects.all()
        context['current_permissions'] = role.permissions.all()
        context['edit_mode'] = True
        return context

    def get_success_url(self):
        return reverse_lazy('liste_des_roles')

    def get_object(self, queryset=None):
        # Pour UpdateView
        if self.kwargs.get('pk'):
            return get_object_or_404(Group, pk=self.kwargs.get('pk'))
        return None
    
    def form_valid(self, form):
        # Détermine si nous créons ou modifions
        is_new = not form.instance.pk
        
        # Sauvegarde du rôle
        response = super().form_valid(form)
        
        # Gestion des permissions
        if 'permissions' in form.cleaned_data:
            self.object.permissions.set(form.cleaned_data['permissions'])
        
        # Message de confirmation
        if is_new:
            messages.success(self.request, f"Le rôle '{form.instance.name}' a été créé avec succès.")
        else:
            messages.success(self.request, f"Le rôle '{form.instance.name}' a été modifié avec succès.")
            
        return response
    
    def get_success_url(self):
        return reverse_lazy('liste_des_roles')


from django.db import models



class UserListView(PermissionRequiredMixin, ListView):
    """Affiche la liste des utilisateurs liés à l'utilisateur connecté"""
    model = User
    context_object_name = 'users'
    permission_required = 'utilisateurs.view_user'

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            if user.is_superuser:
                # Superuser : tous les utilisateurs parents, sauf lui-même
                return User.objects.filter(owner__isnull=True).exclude(id=user.id)

            if user.owner is None:
                # Utilisateur parent : lui-même + ses enfants
                return User.objects.filter(models.Q(id=user.id) | models.Q(owner=user))
            else:
                # Utilisateur fils : son parent + tous les enfants du parent
                return User.objects.filter(models.Q(id=user.owner.id) | models.Q(owner=user.owner))

        return User.objects.none()

    def get_template_names(self):
        if self.request.user.is_superuser:
            return ['utilisateurs/liste_des_utilisateurs_admin.html']
        return ['utilisateurs/liste_des_utilisateurs.html']

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "Vous devez être connecté pour accéder à cette page.")
            return redirect('login')
        messages.warning(self.request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect('homePage')





from .forms import CreateOrUpdateUserForm

class CreateUtilisateurView(PermissionRequiredMixin, CreateView):
    model = User
    form_class = CreateOrUpdateUserForm
    template_name = 'utilisateurs/create_utilisateur.html'  # Par défaut
    success_url = reverse_lazy('liste_des_utilisateurs')
    permission_required = 'utilisateurs.view_user'

    def dispatch(self, request, *args, **kwargs):
        # Choisir le template dynamiquement selon le type d'utilisateur
        if request.user.is_superuser:
            self.template_name = 'utilisateurs/create_utilisateuradmin.html'
        else:
            self.template_name = 'utilisateurs/create_utilisateur.html'
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        current_user = self.request.user

        if current_user.is_superuser:
            form.instance.owner = None
        else:
            form.instance.owner = current_user.owner if current_user.owner else current_user

        messages.success(self.request, "L'utilisateur a été ajouté avec succès !")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Il y a des erreurs dans le formulaire. Veuillez les corriger.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = 'Créer un utilisateur'
        return context


    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "Vous devez être connecté pour accéder à cette page.")
            return redirect('login')  # Redirige vers la page de connexion
        messages.error(self.request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect('homePage')  # Redirige vers le tableau de bord ou une autre page



class ModifierUtilisateurView(UpdateView):
    model = User
    form_class =CreateOrUpdateUserForm
    template_name = 'utilisateurs/modifier_utilisateur.html'  # Le template pour afficher le formulaire de modification
    success_url = reverse_lazy('liste_des_utilisateurs')  # Redirection après succès

    def form_valid(self, form):
        # Si le formulaire est valide, on affiche un message de succès
        messages.success(self.request, "L'utilisateur a été modifié avec succès ! ")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Si le formulaire est invalide, on affiche un message d'erreur
        messages.error(self.request, "Il y a des erreurs dans le formulaire. Veuillez les corriger.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = 'Modifier l\'utilisateur'  # Titre personnalisé dans le template
        return context



from django.views.generic import DetailView


class UserDetailView(DetailView):
    model = User
    template_name = 'utilisateurs/detail_utilisateur.html'  # Assurez-vous que le template est correct
    context_object_name = 'utilisateur'  # Assurez-vous que l'objet utilisateur est bien passé dans le contexte
 



# Vue pour supprimer un rôle
def delete_role(request, pk):
    role = get_object_or_404(Group, pk=pk)
    role_name = role.name
    role.delete()
    messages.success(request, f"Le rôle {role_name} a été supprimé avec succès.")
    return redirect('liste_des_roles')

from django.http import JsonResponse

# Vue pour récupérer les permissions d'un rôle (AJAX)
def get_role_permissions(request, pk):
    role = get_object_or_404(Group, pk=pk)
    permissions = list(role.permissions.values_list('id', flat=True))
    return JsonResponse({'permissions': permissions})


def delete_user(request, user_id):
    # Vérifie si l'utilisateur a la permission de supprimer un utilisateur
    if not request.user.has_perm('utilisateurs.delete_user'):
        messages.error(request, "Vous n'avez pas la permission de supprimer un utilisateur.")
        return redirect('liste_des_utilisateurs')

    # Récupérer l'utilisateur à supprimer
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.delete()
        messages.success(request, "L'utilisateur a été supprimé avec succès.")
        return redirect('liste_des_utilisateurs')

    return redirect('liste_des_utilisateurs')  # Redirection en cas d'accès direct

#Profil
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import User
from django.views import View
class UserProfilView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return JsonResponse({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'telephone': user.telephone,  # ← ici
        })
