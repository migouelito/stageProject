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

class ListeDesZones(PermissionRequiredMixin, ListView):    
    template_name = 'capteurs/liste_des_zones.html'
    context_object_name = 'zones'
    permission_required = 'capteurs.view_zonesecurite'  # Spécifie la permission requise

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.permission_required):
            messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
            return redirect('homePage')  # Redirection personnalisée
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return ZoneSecurite.objects.none()

        # Si c'est un fils, récupérer son parent et les frères
        if user.owner:
            parent = user.owner
            related_users = [parent] + list(parent.sub_users.all())
        else:
            # Si c'est un parent, lui et ses fils
            related_users = [user] + list(user.sub_users.all())

        return ZoneSecurite.objects.filter(user__in=related_users).select_related('user').only('nom', 'description', 'user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            # On peut aussi afficher les utilisateurs liés
            utilisateurs = user.get_all_related_users()
            context['utilisateurs'] = utilisateurs
            context['utilisateurs_ids'] = [utilisateur.id for utilisateur in utilisateurs]  # Récupère les IDs
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
        'utilisateurs': utilisateurs
    })

from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from .models import ZoneSecurite

class ZoneSecuriteView(ListView):
    model = ZoneSecurite
    template_name = 'capteurs/modifier_zone.html'
    context_object_name = 'zones'



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

        # Convertir en JSON pour l'utiliser dans le template
        context['zone_data_json'] = json.dumps(zone_data)

        # Récupérer la liste des utilisateurs liés à la zone (ajuster selon ton modèle)
        utilisateurs = self.request.user.get_all_related_users()
        context['utilisateurs'] = utilisateurs

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
    # Récupération des utilisateurs liés à l'utilisateur connecté
    utilisateurs = request.user.get_all_related_users()
    
    if request.method == 'POST':
        try:
            # Validation des données obligatoires
            nom = request.POST.get('nom')
            description = request.POST.get('description')
            forme = request.POST.get('forme')
            utilisateur_id = request.POST.get('utilisateur')
            
            if not all([nom, description, forme, utilisateur_id]):
                return JsonResponse({'error': 'Tous les champs obligatoires doivent être remplis'}, status=400)
            
            # Vérification que l'utilisateur cible fait bien partie des relations autorisées
            user = User.objects.get(id=utilisateur_id)
            if user not in utilisateurs:
                return JsonResponse({'error': 'Utilisateur non autorisé'}, status=403)
            
            zone = ZoneSecurite(
                nom=nom,
                description=description,
                forme=forme,
                user=user,
            )

            # Gestion des différentes formes
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

    return render(request, 'capteurs/creer_zone.html', {'utilisateurs': utilisateurs})


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
    return redirect('liste_des_zones')



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
def suivreBetail(request, user_id=None):
    try:
        if user_id:
            user = User.objects.get(id=user_id)
        else:
            user = request.user
    except User.DoesNotExist:
        raise Http404("Utilisateur non trouvé")

    # 🔒 Ne récupérer que les zones de CET utilisateur
    zones = ZoneSecurite.objects.filter(user=user)

    zones_data = []
    for zone in zones:
        try:
            coins = json.loads(zone.coins) if zone.coins else None
        except json.JSONDecodeError:
            coins = None

        zones_data.append({
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
        })

    zones_data_json = json.dumps(zones_data)

    return render(request, 'capteurs/suivrebetail.html', {
        'user_id': user.id,
        'zones_data_json': zones_data_json
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


