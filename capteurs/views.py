from django.shortcuts import render
from django.views.generic import ListView
from .models import Capteur
from django.contrib.auth.mixins import PermissionRequiredMixin




class CapteursListView(PermissionRequiredMixin, ListView):
    model = Capteur
    template_name = 'capteurs/liste_des_capteurs.html'
    context_object_name = 'capteurs'
    permission_required = 'capteurs.view_capteur'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_required):
            messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
            return redirect('homePage')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user

        # Cas 1 : si c’est un owner, il voit ses propres capteurs
        if not user.owner:
            return Capteur.objects.filter(user=user)

        # Cas 2 : sinon, c’est un sub-user, on affiche les capteurs dont la zone est liée à lui
        zones_utilisateur = ZoneSecurite.objects.filter(user=user)
        return Capteur.objects.filter(zone_securite__in=zones_utilisateur)

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission de voir cette page.")
        return super().handle_no_permission()



from django.views.generic import FormView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import IntegrityError
import openpyxl

class AjoutCapteursView(FormView):
    template_name = 'capteurs/ajouter_capteur.html'
    success_url = reverse_lazy('liste_des_capteurs')

    def get_form(self, form_class=None):
        nombre_formulaires = int(self.request.GET.get('nombre', 1))
        self.request.session['nombre_capteurs'] = nombre_formulaires
        form_list = [CapteurForm(user=self.request.user) for _ in range(nombre_formulaires)]
        return form_list

    def post(self, request, *args, **kwargs):
        nombre_formulaires = self.request.session.get('nombre_capteurs', 1)
        form_list = [CapteurForm(request.POST, user=request.user) for _ in range(nombre_formulaires)]

        file_uploaded = 'xlsx_file' in request.FILES
        valid_forms = [form for form in form_list if form.is_valid()]
        
        type_animal = valid_forms[0].cleaned_data.get('type_animal') if valid_forms else None
        zone_securite = valid_forms[0].cleaned_data.get('zone_securite') if valid_forms else None
        
        excel_valid = True
        excel_errors = []
        excel_data = []

        if file_uploaded:
            file = request.FILES['xlsx_file']
            excel_valid, excel_data, excel_errors = self.valider_excel(file)

        if len(valid_forms) == len(form_list) and excel_valid:
            parent_user = request.user.owner if hasattr(request.user, 'owner') and request.user.owner else request.user
            erreurs = []
            capteurs_crees = []

            for form in valid_forms:
                try:
                    capteur = form.save(commit=False)
                    capteur.user = parent_user
                    if zone_securite:
                        capteur.zone_securite = zone_securite
                    capteur.save()
                    capteurs_crees.append(capteur.identifiant)
                except IntegrityError:
                    erreurs.append(f"Le capteur avec l'identifiant '{form.cleaned_data.get('identifiant')}' existe déjà.")
                except Exception as e:
                    erreurs.append(f"Erreur lors de l'enregistrement : {str(e)}")

            if file_uploaded and type_animal:
                for identifiant in excel_data:
                    try:
                        if identifiant not in capteurs_crees:
                            Capteur.objects.create(
                                user=parent_user,
                                identifiant=identifiant,
                                type_animal=type_animal,
                                zone_securite=zone_securite,
                                actif=False
                            )
                            capteurs_crees.append(identifiant)
                    except IntegrityError:
                        erreurs.append(f"Le capteur Excel avec l'identifiant '{identifiant}' existe déjà.")
                    except Exception as e:
                        erreurs.append(f"Erreur avec le capteur Excel '{identifiant}': {str(e)}")

            if erreurs:
                for err in erreurs:
                    messages.error(request, err)
                if capteurs_crees:
                    messages.success(request, f"{len(capteurs_crees)} capteur(s) créé(s) avec succès !")
                return self.form_invalid(form_list)
            else:
                total = len(valid_forms) + len(excel_data) if file_uploaded else len(valid_forms)
                messages.success(request, f"{total} capteur(s) ajouté(s) avec succès !")
                return super().form_valid(valid_forms)
        else:
            for form in form_list:
                if not form.is_valid():
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{form.fields[field].label}: {error}")
            
            for error in excel_errors:
                messages.error(request, error)

            return self.form_invalid(form_list)

    def valider_excel(self, file):
        try:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active

            identifiants = []
            erreurs = []

            for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not row[0]:
                    erreurs.append(f"Ligne {i}: Identifiant manquant ou vide")
                    continue
                
                identifiant = str(row[0]).strip()
                if Capteur.objects.filter(identifiant=identifiant).exists():
                    erreurs.append(f"Ligne {i}: Le capteur '{identifiant}' existe déjà")
                else:
                    identifiants.append(identifiant)

            return (len(erreurs) == 0, identifiants, erreurs)

        except Exception as e:
            return (False, [], [f"Erreur de lecture du fichier Excel: {str(e)}"])

    def form_invalid(self, form_list):
        return self.render_to_response(self.get_context_data(form_list=form_list))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_list'] = kwargs.get('form_list', [])
        context['nombre_formulaires'] = self.request.session.get('nombre_capteurs', 1)
        return context


from django.views.generic.edit import UpdateView
from django.contrib import messages
from .forms import CapteurForm
from django.db import IntegrityError

class ModifierCapteurView(UpdateView):
    model = Capteur
    form_class = CapteurForm
    template_name = 'capteurs/modifier_capteur.html'
    success_url = reverse_lazy('liste_des_capteurs')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # Détecter le parent comme dans AjoutCapteursView
        user = self.request.user
        parent_user = user.owner if hasattr(user, 'owner') and user.owner else user

        kwargs['user'] = parent_user
        return kwargs

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Le capteur a été modifié avec succès ! ✅")
            return response
        except IntegrityError as e:
            form.add_error('identifiant', "Un capteur avec cet identifiant existe déjà.")
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"Une erreur est survenue : {str(e)} ❌")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Il y a des erreurs dans le formulaire. Veuillez les corriger. ")
        return super().form_invalid(form)

    

from django.views.generic import DetailView
from django.shortcuts import get_object_or_404


class DetailCapteurView(DetailView):
    model = Capteur
    template_name = 'capteurs/detail_capteur.html'
    context_object_name = 'capteur'  # Le nom de la variable qui sera utilisée dans le template

    def get_object(self):
        # Récupère le capteur par son ID (pk)
        capteur_id = self.kwargs.get('pk')  # Récupère l'ID à partir des paramètres de l'URL
        return get_object_or_404(Capteur, pk=capteur_id)  # Utilise get_object_or_404 pour éviter une erreur si le capteur n'existe pas



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Capteur

@csrf_exempt  # Désactiver CSRF pour tester, mais utiliser @csrf_protect en production
def supprimer_capteur(request, capteur_id):
    if request.method == "POST":
        try:
            capteur = Capteur.objects.get(id=capteur_id)
            capteur.delete()
            #messages.success(request,f"Zone creé avec succès.")
            return JsonResponse({"success": True})
        except Capteur.DoesNotExist:
            return JsonResponse({"success": False, "error": "Capteur introuvable"})
    return JsonResponse({"success": False, "error": "Requête invalide"})



from django.shortcuts import render
from .models import Statistiques
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser:
        # Statistiques générales pour l'admin (tous les utilisateurs par exemple)
        stats = {
        'chefs_d_elevage': User.get_chefs_d_elevage_et_nb_fils(),
        }
        return render(request, 'base/statistiqueadmin.html', stats)
    else:
        # Statistiques pour l'utilisateur connecté uniquement
        stats = {
            'capteurs_par_animal': Statistiques.nombre_capteurs_par_animal(user),
            'capteurs_actifs': Statistiques.nombre_capteurs_actifs(user),
            'capteurs_inactifs': Statistiques.nombre_capteurs_inactifs(user),
            'statistiques_zone': Statistiques.statistique_zone(user),  # Ajouter les statistiques de zone
        }
        return render(request, 'base/statistique.html', stats)


from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView
from django.contrib import messages
from django.shortcuts import redirect
from .models import Message
from utilisateurs.models import User  # Assure-toi que le chemin est correct

class MessageListView(PermissionRequiredMixin, ListView):
    model = Message
    template_name = "capteurs/message_list.html"
    context_object_name = "notifications"
    permission_required = 'capteurs.view_message'

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission d'accéder à la page des notifications.")
        return redirect('homePage')
    def get_queryset(self):
        user = self.request.user

        # Si l'utilisateur est un sous-utilisateur (il a un owner), il voit uniquement ses messages
        if user.owner:
            users_ids = [user.id]
        else:
            # Si c'est un parent, il voit ses messages + ceux de ses sub-users
            sub_user_ids = user.sub_users.values_list('id', flat=True)
            users_ids = list(sub_user_ids) + [user.id]

        return Message.objects.filter(user_id__in=users_ids).order_by('-date_heure')



from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Message

@login_required
def supprimer_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    # Vérifie si l'utilisateur est le propriétaire ou a une permission spéciale
    if request.user == message.user or request.user.has_perm('capteurs.view_message'):
        message.delete()
        messages.success(request, "Message supprimé avec succès.")
        return redirect('notifications')  # change si ta vue a un autre nom
    else:
        messages.error(request, "Vous n'avez pas la permission de supprimer ce message.")
        return redirect('notifications')  # on redirige au lieu de renvoyer une erreur brute



@login_required
def supprimer_tout_les_messages(request):
    user = request.user

    if user.owner is None:
        # ✅ Cas d’un parent : ne prendre que les zones des sous-utilisateurs
        sous_utilisateurs = user.sub_users.all()
        zones = ZoneSecurite.objects.filter(user__in=sous_utilisateurs)
    else:
        # ✅ Cas d’un sous-utilisateur : ses propres zones
        zones = ZoneSecurite.objects.filter(user=user)

    # Supprime tous les messages liés à ces zones
    messages_supprimes = Message.objects.filter(zone__in=zones)
    count = messages_supprimes.count()
    messages_supprimes.delete()

    messages.success(request, f"{count} message(s) supprimé(s) avec succès.")
    return redirect('notifications')  # Adapte selon le nom réel de ta vue


class MarquerCommeLuView(View):
    def get(self, request, message_id):
        # Récupérer le message par son ID
        message = get_object_or_404(Message, id=message_id)
        
        # Marquer le message comme lu
        message.is_read = True
        message.save()  # Sauvegarder les modifications dans la base de données
        
        # Rediriger l'utilisateur vers la liste des messages ou une autre page
        return redirect('notifications')  # Modifier 'notifications' selon le nom de ta vue


from django.views import View
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Message  # Remplace par ton modèle réel

from django.contrib import messages  # importer le module messages


class MarquerTousCommeLuView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user

        # Si l'utilisateur est un owner (il a des sub_users)
        if user.sub_users.exists():
            # Inclure l'utilisateur + tous ses sub-users
            all_users = [user] + list(user.sub_users.all())
            # Marquer comme lus les messages de toutes les zones appartenant à ces utilisateurs
            messages_non_lus = Message.objects.filter(user__in=all_users, is_read=False)
        else:
            # Sinon, marquer seulement les messages liés à ses propres zones
            messages_non_lus = Message.objects.filter(user=user, is_read=False)

        count = messages_non_lus.count()
        messages_non_lus.update(is_read=True)

        messages.success(request, f"{count} message(s) marqué(s) comme lu(s).")
        return redirect('notifications')  # Remplace 'notifications' si nécessaire




from django.shortcuts import render

def gps_map_view(request):
    return render(request, 'capteurs/map.html')





#Vue des definitions des differnets zones de pacturages
from django.views.generic import ListView
from .models import ZoneSecurite

from django.views.generic import ListView
from .models import ZoneSecurite
from utilisateurs.models import User  # Utilise ton modèle utilisateur personnalisé

from django.db.models import Count  # ⬅️ Ajoute cette ligne

class ListeDesZones(PermissionRequiredMixin, ListView):    
    template_name = 'capteurs/liste_des_zones.html'
    context_object_name = 'zones'
    permission_required = 'capteurs.view_zonesecurite'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_required):
            messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
            return redirect('homePage')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return ZoneSecurite.objects.none()

        # Si l'utilisateur est un owner, il peut voir ses zones + celles de ses sub-users
        if user.sub_users.exists():
            related_users = [user] + list(user.sub_users.all())
        else:
            # Sinon, uniquement ses propres zones
            related_users = [user]

        return ZoneSecurite.objects.filter(user__in=related_users)\
            .select_related('user')\
            .only('nom', 'description', 'user')\
            .annotate(nb_capteurs=Count('capteur'))


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            utilisateurs = user.get_all_related_users()
            context['utilisateurs'] = utilisateurs
            context['utilisateurs_ids'] = [utilisateur.id for utilisateur in utilisateurs]
        else:
            context['utilisateurs'] = User.objects.none()
            context['utilisateurs_ids'] = []

        return context


class ListeDesZonesAvecCapteurs(PermissionRequiredMixin, ListView):    
    template_name = 'capteurs/liste_zones_avec_capteurs.html'
    context_object_name = 'zones'
    permission_required = 'capteurs.view_zonesecurite'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_required):
            messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
            return redirect('homePage')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return ZoneSecurite.objects.none()

        if user.owner:
            parent = user.owner
            related_users = [parent] + list(parent.sub_users.all())
        else:
            related_users = [user] + list(user.sub_users.all())

        # Annotation du nombre de capteurs associés à chaque zone
        return ZoneSecurite.objects.filter(user__in=related_users)\
            .select_related('user')\
            .only('nom', 'description', 'user')\
            .annotate(nb_capteurs=Count('capteur'))  # ⬅️ Annoter ici

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            utilisateurs = user.get_all_related_users()
            context['utilisateurs'] = utilisateurs
            context['utilisateurs_ids'] = [utilisateur.id for utilisateur in utilisateurs]
        else:
            context['utilisateurs'] = User.objects.none()
            context['utilisateurs_ids'] = []

        return context


from django.shortcuts import render, get_object_or_404, redirect
from .models import ZoneSecurite
from django.contrib.auth import get_user_model

User = get_user_model()

def modifier_zone(request, pk):
  
    # Récupérer la zone de sécurité par son ID (pk)
    zone = get_object_or_404(ZoneSecurite, pk=pk)

    if request.method == 'POST':
        # Mettre à jour les champs
        zone.nom = request.POST.get('nom')
        zone.description = request.POST.get('description')
        utilisateur_id = request.POST.get('utilisateur')
        user = User.objects.get(id=utilisateur_id)
        zone.user = user

        # Enregistrer les modifications
        zone.save()
        return redirect('liste_des_zones')  # Rediriger vers la liste des zones après la modification

    # Si la méthode est GET, afficher le formulaire pré-rempli
    utilisateurs = User.objects.all()
    return render(request, 'capteurs/modifier_zone.html', {
        'zone': zone,
        'utilisateurs': utilisateurs,
    
    })




from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from .models import ZoneSecurite, User
import json


class ZoneSecuriteView(ListView):
    model = ZoneSecurite
    template_name = 'capteurs/modifier_zone.html'
    context_object_name = 'zones'

    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_id'] = self.kwargs['user_id']
        context['zone_id'] = self.kwargs['zone_id']
        
        # Récupération de la zone spécifique
        zone = get_object_or_404(ZoneSecurite, pk=context['zone_id'])
        context['zone'] = zone

        # Sérialisation des données de la zone
        zone_data = {
            'forme': zone.forme,
            'latitude': float(zone.latitude) if zone.latitude else None,
            'longitude': float(zone.longitude) if zone.longitude else None,
            'rayon': float(zone.rayon) if zone.rayon else None,
            'coin1_lat': float(zone.coin1_lat) if zone.coin1_lat else None,
            'coin1_lon': float(zone.coin1_lon) if zone.coin1_lon else None,
            'coin2_lat': float(zone.coin2_lat) if zone.coin2_lat else None,
            'coin2_lon': float(zone.coin2_lon) if zone.coin2_lon else None,
            'coin3_lat': float(zone.coin3_lat) if zone.coin3_lat else None,
            'coin3_lon': float(zone.coin3_lon) if zone.coin3_lon else None,
            'coin4_lat': float(zone.coin4_lat) if zone.coin4_lat else None,
            'coin4_lon': float(zone.coin4_lon) if zone.coin4_lon else None,
            'coins': zone.coins if isinstance(zone.coins, (list, dict)) else json.loads(zone.coins) if zone.coins else []
        }

        context['zone_data_json'] = json.dumps(zone_data)

        # Récupérer la liste des utilisateurs liés à la zone
        utilisateurs = self.request.user.get_all_related_users().exclude(id=self.request.user.id)
        context['utilisateurs'] = utilisateurs

        # Récupérer les identifiants des capteurs liés à la zone
        capteurs_ids = list(
            Capteur.objects.filter(zone_securite=zone).values_list('identifiant', flat=True)
        )
        context['capteurs_ids'] = capteurs_ids

        return context




from django.shortcuts import render, redirect
from .models import ZoneSecurite
from django.contrib.auth import get_user_model

User = get_user_model()
import json
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import ZoneSecurite, User

@login_required
def creer_zone(request):
    # Récupération des utilisateurs liés à l'utilisateur connecté (hors lui-même)
    utilisateurs = request.user.get_all_related_users().exclude(id=request.user.id)
    
    # Récupération des IDs des capteurs liés à l'utilisateur qui ont une zone
    capteurs_ids = list(
        Capteur.objects.filter(
            user=request.user,
            zone_securite__isnull=False
        ).values_list('identifiant', flat=True)
    )
    
    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            description = request.POST.get('description')
            forme = request.POST.get('forme')
            utilisateur_id = request.POST.get('utilisateur')
            
            # Vérification des champs obligatoires
            if not all([nom, description, forme, utilisateur_id]):
                return JsonResponse({'error': 'Tous les champs obligatoires doivent être remplis'}, status=400)
            
            # Vérifier que l'utilisateur sélectionné est bien autorisé
            user = User.objects.get(id=utilisateur_id)
            if user not in utilisateurs:
                return JsonResponse({'error': 'Utilisateur non autorisé'}, status=403)
            
            zone = ZoneSecurite(
                nom=nom,
                description=description,
                forme=forme,
                user=user,
            )

            # Selon la forme, récupérer les coordonnées
            if forme == 'cercle':
                zone.latitude = request.POST.get('latitude')
                zone.longitude = request.POST.get('longitude')
                zone.rayon = request.POST.get('rayon')
                if None in [zone.latitude, zone.longitude, zone.rayon]:
                    return JsonResponse({'error': 'Données manquantes pour le cercle'}, status=400)

            elif forme == 'triangle':
                required_fields = ['coin1_lat', 'coin1_lon', 'coin2_lat', 'coin2_lon', 'coin3_lat', 'coin3_lon']
                for field in required_fields:
                    setattr(zone, field, request.POST.get(field))
                if None in [getattr(zone, f) for f in required_fields]:
                    return JsonResponse({'error': 'Données manquantes pour le triangle'}, status=400)

            elif forme == 'rectangle':
                required_fields = ['coin1_lat', 'coin1_lon', 'coin2_lat', 'coin2_lon', 
                                   'coin3_lat', 'coin3_lon', 'coin4_lat', 'coin4_lon']
                for field in required_fields:
                    setattr(zone, field, request.POST.get(field))
                if None in [getattr(zone, f) for f in required_fields]:
                    return JsonResponse({'error': 'Données manquantes pour le rectangle'}, status=400)

            elif forme == 'polygon':
                coins = request.POST.get('coins')
                if not coins:
                    return JsonResponse({'error': 'Coordonnées du polygone manquantes'}, status=400)
                try:
                    coins_list = json.loads(coins)
                    if not isinstance(coins_list, list):
                        return JsonResponse({'error': 'Format des coordonnées invalide'}, status=400)
                    zone.coins = coins
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Erreur de décodage JSON'}, status=400)

            elif forme == 'marker':
                zone.latitude = request.POST.get('latitude')
                zone.longitude = request.POST.get('longitude')
                if None in [zone.latitude, zone.longitude]:
                    return JsonResponse({'error': 'Coordonnées du marqueur manquantes'}, status=400)

            else:
                return JsonResponse({'error': 'Type de forme non supporté'}, status=400)

            zone.save()
            return redirect('liste_des_zones')

        except User.DoesNotExist:
            return JsonResponse({'error': 'Utilisateur introuvable'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Rendu du template avec les données nécessaires
    return render(request, 'capteurs/creer_zone.html', {
        'utilisateurs': utilisateurs,
        'user_id': request.user.id,
        'capteurs_ids': capteurs_ids,  # Liste d'IDs prête à être utilisée dans JS
    })


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .models import ZoneSecurite
import json

@csrf_exempt
def update_position(request, zone_id):

    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            zone = get_object_or_404(ZoneSecurite, id=zone_id)
            
            # Déboguer les données reçues
            print("Données reçues:", data)

            # Validation des champs du formulaire
            nom = data.get('nom')
            description = data.get('description')
            user_id = data.get('user')
            forme = data.get('forme')

            if not nom or not description or not user_id or not forme:
                return JsonResponse({'error': 'Champs manquants'}, status=400)

            # Mettre à jour les informations générales de la zone
            zone.nom = nom
            zone.description = description
            zone.user_id = user_id
            zone.forme = forme

            # Nouveau : Mise à jour du statut sécurité
            active_securite = data.get('active_securite')
            if active_securite is not None:
                zone.active_securite = active_securite in ['True', True, 'true', 1]

            # Réinitialiser les anciennes coordonnées
            zone.latitude = None
            zone.longitude = None
            zone.rayon = None
            zone.coin1_lat = None
            zone.coin1_lon = None
            zone.coin2_lat = None
            zone.coin2_lon = None
            zone.coin3_lat = None
            zone.coin3_lon = None
            zone.coin4_lat = None
            zone.coin4_lon = None
            zone.coins = None

            # Mise à jour en fonction de la forme
            if forme == 'cercle':
                zone.latitude = data.get('latitude')
                zone.longitude = data.get('longitude')
                zone.rayon = data.get('rayon')
            elif forme == 'triangle':
                zone.coin1_lat = data.get('coin1_lat')
                zone.coin1_lon = data.get('coin1_lon')
                zone.coin2_lat = data.get('coin2_lat')
                zone.coin2_lon = data.get('coin2_lon')
                zone.coin3_lat = data.get('coin3_lat')
                zone.coin3_lon = data.get('coin3_lon')
            elif forme == 'carre' or forme == 'rectangle':
                zone.coin1_lat = data.get('coin1_lat')
                zone.coin1_lon = data.get('coin1_lon')
                zone.coin2_lat = data.get('coin2_lat')
                zone.coin2_lon = data.get('coin2_lon')
                zone.coin3_lat = data.get('coin3_lat')
                zone.coin3_lon = data.get('coin3_lon')
                zone.coin4_lat = data.get('coin4_lat')
                zone.coin4_lon = data.get('coin4_lon')
            elif forme == 'polygon' or forme == 'polyline':
                zone.coins = json.dumps(data.get('coins'))
            elif forme == 'marker':
                zone.latitude = data.get('latitude')
                zone.longitude = data.get('longitude')
            
            zone.save()
            messages.success(request, f"Zone modifiée avec succès.")
            return JsonResponse({'message': 'Zone mise à jour avec succès !'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Erreur: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def supprimer_zone(request, zone_id):
    zone = get_object_or_404(ZoneSecurite, id=zone_id)
    zone.delete()
    messages.success(request, f"Zone supprimé avec succès.")
    return redirect('liste_des_zones')


#Suppression des capteurs lié à la zone
@login_required
def supprimer_capteurs_zone(request, zone_id):
    zone = get_object_or_404(ZoneSecurite, id=zone_id)

    # Supprimer uniquement les capteurs liés à cette zone
    capteurs_associes = Capteur.objects.filter(zone_securite=zone)
    nb = capteurs_associes.count()
    capteurs_associes.delete()

    messages.success(request, f"{nb} capteur(s) associés à la zone {zone.nom} ont été supprimés.")
    return redirect('zonesaveccapteurs')

#methode pour activer et desactiver la zone
@login_required
def changer_etat_zone(request, zone_id):
    zone = get_object_or_404(ZoneSecurite, id=zone_id)
    zone.active_securite = not zone.active_securite
    zone.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))


from django.db import transaction

def get_related_users(user):
    """Retourne l'utilisateur + ses sub-users (ou owner et ses sub-users)."""
    if user.owner:
        parent = user.owner
        return [parent] + list(parent.sub_users.all())
    else:
        return [user] + list(user.sub_users.all())

@login_required
def transferer_zone_capteurs(request):
    related_users = get_related_users(request.user)
    zones = ZoneSecurite.objects.filter(user__in=related_users)

    if request.method == "POST":
        ancienne_zone_id = request.POST.get("ancienne_zone_id")
        nouvelle_zone_id = request.POST.get("nouvelle_zone_id")

        if not ancienne_zone_id or not nouvelle_zone_id:
            messages.error(request, "Veuillez sélectionner les deux zones.")
            return redirect("zonesaveccapteurs")

        if ancienne_zone_id == nouvelle_zone_id:
            messages.error(request, "La zone source et la zone destination doivent être différentes.")
            return redirect("zonesaveccapteurs")

        try:
            ancienne_zone = get_object_or_404(ZoneSecurite, id=int(ancienne_zone_id), user__in=related_users)
            nouvelle_zone = get_object_or_404(ZoneSecurite, id=int(nouvelle_zone_id), user__in=related_users)

            capteurs = Capteur.objects.filter(zone_securite=ancienne_zone, user__in=related_users)
            nb_capteurs = capteurs.count()

            if nb_capteurs == 0:
                messages.error(request, f"Aucun capteur trouvé dans la zone '{ancienne_zone.nom}'.")
                return redirect("zonesaveccapteurs")

            with transaction.atomic():
                capteurs.update(zone_securite=nouvelle_zone)
                # Pas besoin de mettre à jour `nb_capteurs` si c’est juste pour le front, car annoté dynamiquement

            messages.success(
                request,
                f"{nb_capteurs} capteur(s) transféré(s) de la zone {ancienne_zone.nom} vers '{nouvelle_zone.nom}'."
            )

        except ZoneSecurite.DoesNotExist:
            messages.error(request, "Une des zones sélectionnées n'existe pas ou ne vous appartient pas.")
        except Exception as e:
            messages.error(request, f"Erreur lors du transfert : {str(e)}")

        return redirect("zonesaveccapteurs")

    return render(request, "capteurs/liste_zones_avec_capteurs.html", {"zones": zones})


from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import ZoneSecurite, Capteur
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .models import ZoneSecurite, Capteur

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from .models import ZoneSecurite, Capteur

class ElegantHeaderCanvas(canvas.Canvas):
    """Canvas personnalisé pour ajouter un en-tête et pied de page élégant"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
        
    def save(self):
        page_count = len(self.pages)
        for page_num, page in enumerate(self.pages, 1):
            self.__dict__.update(page)
            self.draw_page_template(page_num, page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_page_template(self, page_num, page_count):
        """Dessine l'en-tête et le pied de page"""
        # En-tête avec dégradé simulé
        self.setFillColor(colors.HexColor("#2C3E50"))
        self.rect(0, A4[1] - 80, A4[0], 80, fill=1, stroke=0)
        
        # Ligne décorative
        self.setFillColor(colors.HexColor("#3498DB"))
        self.rect(0, A4[1] - 85, A4[0], 5, fill=1, stroke=0)
        
        # Titre dans l'en-tête
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 20)
        self.drawCentredText(A4[0]/2, A4[1] - 40, "RAPPORT DE CAPTEURS PAR ZONE")
        
        # Date et heure
        self.setFont("Helvetica", 10)
        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y à %H:%M")
        self.drawRightString(A4[0] - 30, A4[1] - 60, f"Généré le {date_str}")
        
        # Pied de page
        self.setFillColor(colors.HexColor("#34495E"))
        self.rect(0, 0, A4[0], 30, fill=1, stroke=0)
        
        # Numéro de page
        self.setFillColor(colors.white)
        self.setFont("Helvetica", 9)
        self.drawCentredText(A4[0]/2, 15, f"Page {page_num} sur {page_count}")
        
        # Ligne décorative en bas
        self.setFillColor(colors.HexColor("#3498DB"))
        self.rect(0, 30, A4[0], 3, fill=1, stroke=0)
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from .models import ZoneSecurite, Capteur

class ElegantHeaderCanvas(canvas.Canvas):
    """Canvas personnalisé pour ajouter un en-tête et pied de page élégant"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
        
    def save(self):
        page_count = len(self.pages)
        for page_num, page in enumerate(self.pages, 1):
            self.__dict__.update(page)
            self.draw_page_template(page_num, page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_page_template(self, page_num, page_count):
        """Dessine l'en-tête et le pied de page"""
        # En-tête avec couleur verte
        self.setFillColor(colors.HexColor("#2E7D32"))  # Vert foncé
        self.rect(0, A4[1] - 80, A4[0], 80, fill=1, stroke=0)
        
        # Ligne décorative verte
        self.setFillColor(colors.HexColor("#4CAF50"))  # Vert plus clair
        self.rect(0, A4[1] - 85, A4[0], 5, fill=1, stroke=0)
        
        # Titre dans l'en-tête
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 20)
        self.drawCentredText(A4[0]/2, A4[1] - 40, "RAPPORT DE CAPTEURS PAR ZONE")
        
        # Pied de page avec couleur verte
        self.setFillColor(colors.HexColor("#388E3C"))  # Vert moyen
        self.rect(0, 0, A4[0], 50, fill=1, stroke=0)
        
        # Date et heure en bas
        self.setFillColor(colors.white)
        self.setFont("Helvetica", 10)
        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y à %H:%M")
        self.drawCentredText(A4[0]/2, 35, f"Généré le {date_str}")
        
        # Numéro de page en bas
        self.setFont("Helvetica", 9)
        self.drawCentredText(A4[0]/2, 20, f"Page {page_num} sur {page_count}")
        
        # Ligne décorative en bas
        self.setFillColor(colors.HexColor("#4CAF50"))
        self.rect(0, 50, A4[0], 3, fill=1, stroke=0)

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from .models import ZoneSecurite, Capteur

class ElegantHeaderCanvas(canvas.Canvas):
    """Canvas personnalisé pour ajouter un en-tête et pied de page élégant"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
        
    def save(self):
        page_count = len(self.pages)
        for page_num, page in enumerate(self.pages, 1):
            self.__dict__.update(page)
            self.draw_page_template(page_num, page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_page_template(self, page_num, page_count):
        """Dessine l'en-tête et le pied de page"""
        # En-tête avec couleur verte
        self.setFillColor(colors.HexColor("#2E7D32"))  # Vert foncé
        self.rect(0, A4[1] - 80, A4[0], 80, fill=1, stroke=0)
        
        # Ligne décorative verte
        self.setFillColor(colors.HexColor("#4CAF50"))  # Vert plus clair
        self.rect(0, A4[1] - 85, A4[0], 5, fill=1, stroke=0)
        
        # Titre dans l'en-tête
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 20)
        self.drawCentredText(A4[0]/2, A4[1] - 40, "RAPPORT DE CAPTEURS PAR ZONE")
        
        # Pied de page avec couleur verte
        self.setFillColor(colors.HexColor("#388E3C"))  # Vert moyen
        self.rect(0, 0, A4[0], 50, fill=1, stroke=0)
        
        # Date et heure d'impression en bas
        self.setFillColor(colors.white)
        self.setFont("Helvetica", 10)
        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        heure_str = now.strftime("%H:%M:%S")
        self.drawCentredText(A4[0]/2, 35, f"Imprimé le {date_str} à {heure_str}")
        
        # Numéro de page en bas
        self.setFont("Helvetica", 9)
        self.drawCentredText(A4[0]/2, 20, f"Page {page_num} sur {page_count}")
        
        # Ligne décorative en bas
        self.setFillColor(colors.HexColor("#4CAF50"))
        self.rect(0, 50, A4[0], 3, fill=1, stroke=0)



@login_required
def exporter_capteurs_par_zone_pdf(request):
    """Export PDF élégant des capteurs par zone sans la colonne 'Statut'"""
    
    related_users = get_related_users(request.user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="capteurs_par_zone_rapport.pdf"'
    
    doc = SimpleDocTemplate(
        response, 
        pagesize=A4,
        topMargin=100,
        bottomMargin=60,
        leftMargin=50,
        rightMargin=50,
        canvasmaker=ElegantHeaderCanvas
    )
    
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor("#2E7D32"),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    zone_title_style = ParagraphStyle(
        'ZoneTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#1B5E20"),
        spaceAfter=15,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor("#4CAF50"),
        borderPadding=10,
        backColor=colors.HexColor("#E8F5E8"),
        borderRadius=5
    )
    
    stats_style = ParagraphStyle(
        'Stats',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor("#7F8C8D"),
        spaceAfter=10,
        alignment=TA_RIGHT,
        fontName='Helvetica-Oblique'
    )
    
    no_data_style = ParagraphStyle(
        'NoData',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor("#E74C3C"),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        backColor=colors.HexColor("#FADBD8"),
        borderWidth=1,
        borderColor=colors.HexColor("#E74C3C"),
        borderPadding=8
    )
    
    elements = []
    zones = ZoneSecurite.objects.select_related('user').filter(user__in=related_users)
    total_zones = zones.count()
    total_capteurs = sum(Capteur.objects.filter(zone_securite=zone).count() for zone in zones)

    elements.append(Spacer(1, 20))
    stats_text = f"<b>Résumé :</b> {total_zones} zone(s) • {total_capteurs} capteur(s) au total"
    elements.append(Paragraph(stats_text, stats_style))
    elements.append(Spacer(1, 30))

    for zone_index, zone in enumerate(zones, 1):
        zone_info = f"""
        <b>🏢 Zone {zone_index}/{total_zones} :</b> {zone.nom}<br/>
        <font size="10" color="#7F8C8D">👤 Utilisateur : {zone.user.username}</font>
        """
        elements.append(Paragraph(zone_info, zone_title_style))
        elements.append(Spacer(1, 10))
        
        capteurs = Capteur.objects.filter(zone_securite=zone)
        nb_capteurs = capteurs.count()

        if capteurs.exists():
            types_animals = capteurs.values_list('type_animal__type_animal', flat=True).distinct()
            stats_zone = f"📊 {nb_capteurs} capteur(s) • {len(types_animals)} type(s) d'animaux différents"
            elements.append(Paragraph(stats_zone, stats_style))
            elements.append(Spacer(1, 8))
            
            data = [['🔍 Identifiant', '🐾 Type d\'animal']]

            for capteur in capteurs:
                data.append([
                    str(capteur.identifiant),
                    capteur.type_animal.type_animal
                ])

            table = Table(data, colWidths=[180, 220])
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#81C784")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#F1F8E9")]),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#E8F5E8")),
            ])

            for i in range(1, len(data)):
                bg_color = "#F1F8E9" if i % 2 == 0 else "#FFFFFF"
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(bg_color))

            table.setStyle(table_style)
            elements.append(table)
            elements.append(Spacer(1, 20))
        else:
            no_data_msg = "⚠️ Aucun capteur n'est associé à cette zone"
            elements.append(Paragraph(no_data_msg, no_data_style))
            elements.append(Spacer(1, 15))

        if zone_index < total_zones:
            elements.append(Spacer(1, 10))
            separator = Table([['']], colWidths=[500])
            separator.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor("#4CAF50")),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(separator)
            elements.append(Spacer(1, 20))

    elements.append(Spacer(1, 30))
    footer_text = """
    <font size="9" color="#7F8C8D">
    <i>Ce rapport a été généré automatiquement par le système de gestion des capteurs.<br/>
    Pour toute question, veuillez contacter l'administrateur système.</i>
    </font>
    """
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        spaceAfter=20
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    doc.build(elements)
    return response



@login_required
def exporter_capteurs_zone_pdf(request, zone_id):
    """Export PDF élégant des capteurs d'une zone de sécurité précise identifiée par zone_id"""

    # Vérifier que la zone appartient à un utilisateur accessible par le user connecté
    zone = get_object_or_404(ZoneSecurite, id=zone_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="capteurs_zone_{zone.nom}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        topMargin=100,
        bottomMargin=60,
        leftMargin=50,
        rightMargin=50,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor("#2E7D32"),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    zone_title_style = ParagraphStyle(
        'ZoneTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#1B5E20"),
        spaceAfter=15,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor("#4CAF50"),
        borderPadding=10,
        backColor=colors.HexColor("#E8F5E8"),
        borderRadius=5
    )

    stats_style = ParagraphStyle(
        'Stats',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor("#7F8C8D"),
        spaceAfter=10,
        alignment=TA_RIGHT,
        fontName='Helvetica-Oblique'
    )

    no_data_style = ParagraphStyle(
        'NoData',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor("#E74C3C"),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        backColor=colors.HexColor("#FADBD8"),
        borderWidth=1,
        borderColor=colors.HexColor("#E74C3C"),
        borderPadding=8
    )

    elements = []
    elements.append(Spacer(1, 20))

    # Titre
    elements.append(Paragraph(f"Rapport des capteurs - Zone : {zone.nom}", title_style))
    elements.append(Spacer(1, 20))

    capteurs = Capteur.objects.filter(zone_securite=zone)
    nb_capteurs = capteurs.count()

    if capteurs.exists():
        types_animals = capteurs.values_list('type_animal__type_animal', flat=True).distinct()
        stats_zone = f"📊 {nb_capteurs} capteur(s) • {len(types_animals)} type(s) d'animaux différents"
        elements.append(Paragraph(stats_zone, stats_style))
        elements.append(Spacer(1, 8))

        data = [['🔍 Identifiant', '🐾 Type d\'animal']]

        for capteur in capteurs:
            data.append([
                str(capteur.identifiant),
                capteur.type_animal.type_animal
            ])

        table = Table(data, colWidths=[180, 220])
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#81C784")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F1F8E9")]),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#E8F5E8")),
        ])

        for i in range(1, len(data)):
            bg_color = "#F1F8E9" if i % 2 == 0 else "#FFFFFF"
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(bg_color))

        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        no_data_msg = "⚠️ Aucun capteur n'est associé à cette zone"
        elements.append(Paragraph(no_data_msg, no_data_style))
        elements.append(Spacer(1, 15))

    footer_text = """
    <font size="9" color="#7F8C8D">
    <i>Ce rapport a été généré automatiquement par le système de gestion des capteurs.<br/>
    Pour toute question, veuillez contacter l'administrateur système.</i>
    </font>
    """
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        spaceAfter=20
    )
    elements.append(Paragraph(footer_text, footer_style))

    doc.build(elements)
    return response



#API pour envoyer les donnees en direct 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt  # Exempte cette vue de la vérification CSRF (utile pour l'API)
def recevoir_position(request):
    if request.method == 'POST':
        try:
            # Récupérer les données envoyées par le client (latitude et longitude)
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            # Si les données sont valides
            if latitude and longitude:
                # Ici tu peux traiter les données, comme les enregistrer dans la base de données
                # Mais comme tu veux juste les envoyer en direct, on peut directement les envoyer via WebSocket
                return JsonResponse({'status': 'success', 'message': 'Position reçue'}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': 'Données GPS manquantes'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Erreur dans les données'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Méthode HTTP non autorisée'}, status=405)


import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ZoneSecurite
from django.http import Http404





@login_required
def suivreBetail(request, user_id, zone_id):
    # Vérifie si l'utilisateur existe
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404("Utilisateur non trouvé")

    # Recherche la zone qui correspond à l'utilisateur ET à la zone demandée
    try:
        zone = ZoneSecurite.objects.get(user=user, id=zone_id)
    except ZoneSecurite.DoesNotExist:
        raise Http404("Zone non trouvée pour cet utilisateur")

    # Conversion des coordonnées "coins"
    try:
        coins = json.loads(zone.coins) if zone.coins else None
    except json.JSONDecodeError:
        coins = None

    # Zone au format JSON
    zone_data = {
        'id': zone.id,
        'forme': zone.forme,
        'latitude': zone.latitude,
        'longitude': zone.longitude,
        'rayon': zone.rayon,
        'coin1_lat': zone.coin1_lat,
        'coin1_lon': zone.coin1_lon,
        'coin2_lat': zone.coin2_lat,
        'coin2_lon': zone.coin2_lon,
        'coin3_lat': zone.coin3_lat,
        'coin3_lon': zone.coin3_lon,
        'coin4_lat': zone.coin4_lat,
        'coin4_lon': zone.coin4_lon,
        'coins': coins,
    }
    zone_data_json = json.dumps([zone_data])

    # Capteurs liés à cette zone
    capteurs = Capteur.objects.filter(zone_securite=zone)
    capteurs_ids = list(capteurs.values_list('identifiant', flat=True))

    return render(request, 'capteurs/suivrebetail.html', {
        'user_id': user.id,
        'zones_data_json': zone_data_json,
        'capteurs_avec_zone': capteurs_ids,  # <- Ajout au contexte
        'zone_nom':zone.nom,
    })




#gestion des animaux partie enregistrement des animaux par l'admin
from .models import Animal

class AnimalListView(ListView):
    model = Animal  # Le modèle que nous voulons afficher
    template_name = 'capteurs/liste_des_animaux.html'  # Le template à utiliser pour afficher la liste
    context_object_name = 'animaux'  # Le nom de la variable dans le template contenant la liste des animaux

from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .models import Animal
from django.core.files.storage import FileSystemStorage


from django.db import IntegrityError
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .models import Animal

def ajouter_animal(request):
    if request.method == 'POST':
        type_animal = request.POST.get('type_animal')
        image = request.FILES.get('image')

        try:
            if not type_animal:
                raise ValidationError("Le type d'animal est requis.")

            # Créer l'animal et essayer de le sauvegarder
            animal = Animal(type_animal=type_animal, image=image)
            animal.save()

            # Ajouter un message de succès après l'ajout de l'animal
            messages.success(request, "Animal ajouté avec succès !")

        except IntegrityError:
            # Si un doublon existe (violant la contrainte d'unicité), afficher un message d'erreur
            messages.error(request, f"Un animal du type '{type_animal}' existe déjà.")
            return redirect('liste_des_animaux')

        except ValidationError:
            # Si la validation échoue, afficher un message d'erreur
            messages.error(request, "Le type d'animal est requis.")
            return redirect('liste_des_animaux')

        # Rediriger vers la liste des animaux après l'ajout avec un message de succès
        return redirect('liste_des_animaux')

    return render(request, 'animaux/ajouter_animal.html')


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Animal

def modifier_animal(request, animal_id):
    # Récupérer l'animal à modifier
    animal = get_object_or_404(Animal, id=animal_id)

    # Vérifier si la requête est en méthode POST (lors de la soumission du formulaire)
    if request.method == 'POST':
        # Mettre à jour le type d'animal uniquement si le type a changé
        type_animal = request.POST.get('type_animal', animal.type_animal)

        # Vérifier si un autre animal avec le même type existe déjà
        if Animal.objects.filter(type_animal=type_animal).exclude(id=animal.id).exists():
            # Ajouter un message d'erreur avec Django messages
            messages.error(request, f"Un animal du type '{type_animal}' existe déjà.")
            return redirect('modifier_animal', animal_id=animal.id)  # Rediriger vers la page de modification de l'animal

        # Si le type d'animal a changé, on l'actualise
        if type_animal != animal.type_animal:
            animal.type_animal = type_animal

        # Gérer l'image (si une nouvelle image est téléchargée)
        if 'image' in request.FILES:
            animal.image = request.FILES['image']

        # Sauvegarder les changements dans la base de données
        try:
            animal.save()

            # Ajouter un message de succès avec Django messages
            messages.success(request, "Animal mis à jour avec succès !")

        except Exception as e:
            # Ajouter un message d'erreur avec Django messages
            messages.error(request, f"Erreur lors de la mise à jour de l'animal : {str(e)}")

        # Rediriger vers la page de liste des animaux
        return redirect('liste_des_animaux')  # Remplace 'liste_des_animaux' par le nom de ta vue

    # Si la requête n'est pas en POST, retourner les informations actuelles de l'animal en JSON (seulement ici)
    image_url = request.build_absolute_uri(animal.image.url) if animal.image else None
    image_name = animal.image.name.split('/')[-1] if animal.image else None

    response_data = {
        'id': animal.id,
        'type_animal': animal.type_animal,
        'image_url': image_url,
        'image_name': image_name,
    }

    return JsonResponse(response_data)



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Animal

from django.db.models import ProtectedError

def supprimer_animal(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)

    if request.method == 'POST':
        try:
            animal.delete()
            messages.success(request, "Animal supprimé avec succès !")
        except ProtectedError:
            messages.error(request, "Impossible de supprimer cet animal : il est encore lié à un capteur.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression de l'animal : {str(e)}")
        return redirect('liste_des_animaux')


