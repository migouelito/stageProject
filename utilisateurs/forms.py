from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.core.exceptions import ValidationError

class InscriptionForm(UserCreationForm):
    telephone = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'telephone', 'password1', 'password2')




class InscriptionForm(UserCreationForm):
    telephone = forms.CharField(
        max_length=50, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Numéro de téléphone'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'telephone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Nom d’utilisateur'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Adresse e-mail'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Mot de passe'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirmez le mot de passe'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_superuser = True
        user.is_staff = True
        if commit:
            user.save()
        return user


    # Validation de l'email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cet email est déjà utilisé.")
        return email

    # Validation du username
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    # Validation du numéro de téléphone
    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if User.objects.filter(telephone=telephone).exists():
            raise ValidationError("Ce numéro de téléphone est déjà associé à un compte.")
        return telephone

    # Validation du mot de passe
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        return password1

    # Validation de la confirmation du mot de passe
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return password2



from django import forms
from django.contrib.auth.forms import PasswordResetForm

class PasswordResetFormCustom(PasswordResetForm):
    email = forms.EmailField(
        label="",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Entrez votre e-mail"})
    )







from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'input-field', 'placeholder': 'Adresse email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': 'Mot de passe'})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Email ou mot de passe incorrect.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("Votre compte est désactivé.")

        return self.cleaned_data

    def get_user(self):
        return self.user_cache


    
from django.contrib.auth.models import Group


class CreationUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telephone = forms.CharField(max_length=50, required=True)

    groupe = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.RadioSelect,  # Affiche les groupes sous forme de boutons radio
        help_text="Sélectionnez le groupe de l'utilisateur"
    )

    class Meta:
        model = User  
        fields = [
            "username", "email", "first_name", "last_name", "telephone",
            "password1", "password2", "is_staff", "is_superuser", "is_active",
            "groupe"  # Note que le champ a été changé de 'groups' à 'groupe'
        ]
        widgets = {
            "is_staff": forms.CheckboxInput(),
            "is_superuser": forms.CheckboxInput(),
            "is_active": forms.CheckboxInput(),
        }





from django import forms
from django.contrib.auth.models import Group, Permission

class UserRoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Permissions"
    )
    
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': 'Nom du rôle',
        }


from django import forms
from django.contrib.auth.models import Group
from .models import User

class CreateOrUpdateUserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),  # Liste des groupes disponibles
        required=False,  # Permet de ne pas forcer un choix
        widget=forms.CheckboxSelectMultiple  # Affiche des cases à cocher dans le formulaire
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone', 'password', 'is_active', 'groups']
        widgets = {
            'password': forms.PasswordInput(),  # Pour sécuriser le champ du mot de passe
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:  # Si un mot de passe est fourni
            user.set_password(self.cleaned_data['password'])  # Hachage du mot de passe
        if commit:
            user.save()
            user.groups.set(self.cleaned_data['groups'])  # Assigne directement les groupes
        return user
