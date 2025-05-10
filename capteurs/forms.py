from django import forms
from django.forms import modelformset_factory
from .models import Capteur


from django import forms
from .models import Capteur, ZoneSecurite

class CapteurForm(forms.ModelForm):
    class Meta:
        model = Capteur
        fields = ['identifiant', 'type_animal', 'zone_securite']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            try:
                utilisateurs_ids = set()

                # Ajouter l'utilisateur connecté
                utilisateurs_ids.add(self.user.id)

                # Ajouter le parent s'il existe
                if hasattr(self.user, 'owner') and self.user.owner:
                    utilisateurs_ids.add(self.user.owner.id)

                # Ajouter les sous-utilisateurs si l'utilisateur est un parent
                if hasattr(self.user, 'sub_users'):
                    sub_users = self.user.sub_users.all()
                    utilisateurs_ids.update([u.id for u in sub_users])

                # Filtrer les zones de sécurité liées à tous ces utilisateurs
                self.fields['zone_securite'].queryset = ZoneSecurite.objects.filter(user__id__in=utilisateurs_ids)

            except Exception as e:
                # Fallback en cas d'erreur
                self.fields['zone_securite'].queryset = ZoneSecurite.objects.filter(user=self.user)

    def save(self, commit=True):
        capteur = super().save(commit=False)

        if self.instance.pk is None:
            capteur.actif = False

        if self.user:
            capteur.user = self.user

        if commit:
            capteur.save()
        return capteur





from django import forms
from .models import ZoneSecurite
from django.contrib.auth import get_user_model

User = get_user_model()

class ZoneSecuriteForm(forms.ModelForm):
    utilisateur = forms.ModelChoiceField(
        queryset=User.objects.none(),  # vide par défaut, rempli dynamiquement
        label='Utilisateur',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ZoneSecurite
        fields = ['utilisateur', 'nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Renseigner la liste des sub-users de l'utilisateur connecté
            self.fields['utilisateur'].queryset = user.get_all_related_users()
