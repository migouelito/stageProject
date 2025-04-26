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
            return redirect('homePage')  # Redirection personnalisée
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.owner:  # si c'est un sous-utilisateur
            parent = user.owner
            utilisateurs = [parent] + list(parent.sub_users.all())
        else:  # si c'est un utilisateur principal
            utilisateurs = [user] + list(user.sub_users.all())
        return Capteur.objects.filter(user__in=utilisateurs)


    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission de voir cette page.")
        return super().handle_no_permission()


from django.views.generic import FormView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages  # Importer les messages Django


import csv
from django.db import IntegrityError

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

        valid_forms = [form for form in form_list if form.is_valid()]

        if len(valid_forms) == len(form_list):
            parent_user = request.user.owner if hasattr(request.user, 'owner') and request.user.owner else request.user

            erreurs = []
            for form in valid_forms:
                try:
                    capteur = form.save(commit=False)
                    capteur.user = parent_user
                    capteur.save()
                except IntegrityError:
                    erreurs.append(f"Le capteur avec l’identifiant '{form.cleaned_data.get('identifiant')}' existe déjà.")
                except Exception as e:
                    erreurs.append(f"Erreur inconnue lors de l'enregistrement d’un capteur : {str(e)}")

            if 'csv_file' in request.FILES:
                file = request.FILES['csv_file']
                messages.info(request, f"Fichier CSV reçu : {file.name}")
                self.importer_capteurs_csv(file, parent_user)

            if erreurs:
                for err in erreurs:
                    messages.error(request, err)
                return self.form_invalid(form_list)
            else:
                messages.success(request, "Les capteurs ont été ajoutés avec succès ! ✅")
                return super().form_valid(valid_forms)
        else:
            messages.error(request, "Il y a des erreurs dans les formulaires. Veuillez les corriger. ⚠️")
            return self.form_invalid(form_list)

    def form_invalid(self, form_list):
        return self.render_to_response(self.get_context_data(form_list=form_list))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_list'] = kwargs.get('form_list', [])
        context['nombre_formulaires'] = self.request.session.get('nombre_capteurs', 1)
        return context

    def importer_capteurs_csv(self, file, user):
        try:
            import csv
            from io import TextIOWrapper
            from django.db import IntegrityError

            csv_file = TextIOWrapper(file, encoding='utf-8')
            reader = csv.reader(csv_file)
            next(reader)  # Ignore l'entête

            nb_ajoutes = 0
            erreurs = []

            for i, row in enumerate(reader, start=2):
                try:
                    if len(row) < 2:
                        erreurs.append(f"Ligne {i} : ligne incomplète.")
                        continue

                    Capteur.objects.create(
                        user=user,
                        identifiant=row[0],
                        type_animal=row[1],
                        latitude=48.8566,
                        longitude=2.3522,
                        actif=False
                    )
                    nb_ajoutes += 1
                except IntegrityError:
                    erreurs.append(f"Ligne {i} : le capteur '{row[0]}' existe déjà.")
                except Exception as e:
                    erreurs.append(f"Ligne {i} : erreur inattendue : {str(e)}")

            if nb_ajoutes:
                messages.success(self.request, f"{nb_ajoutes} capteur(s) importé(s) avec succès depuis le fichier CSV. ✅")
            for erreur in erreurs:
                messages.error(self.request, erreur)

        except Exception as e:
            messages.error(self.request, f"Erreur lors de la lecture du fichier CSV : {str(e)}")


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

        # 🔁 Détecter le parent comme dans AjoutCapteursView
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
        messages.error(self.request, "Il y a des erreurs dans le formulaire. Veuillez les corriger. ⚠️")
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

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser:
        # Statistiques générales pour l'admin (tous les utilisateurs par exemple)
        stats = {
            'capteurs_par_animal': Statistiques.nombre_capteurs_par_animal(user),
            'capteurs_actifs': Statistiques.nombre_capteurs_actifs(user),
            'capteurs_inactifs': Statistiques.nombre_capteurs_inactifs(user),
        }
        return render(request, 'base/statistiqueadmin.html', stats)
    else:
        # Statistiques pour l'utilisateur connecté uniquement
        stats = {
            'capteurs_par_animal': Statistiques.nombre_capteurs_par_animal(user),
            'capteurs_actifs': Statistiques.nombre_capteurs_actifs(user),
            'capteurs_inactifs': Statistiques.nombre_capteurs_inactifs(user),
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





#Zonne de securite

from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from .models import ZoneSecurite

class ZoneSecuriteView(ListView):
    model = ZoneSecurite
    template_name = 'capteurs/zonesecurite_list.html'
    context_object_name = 'zones'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_id'] = self.kwargs['user_id']
        context['zone_id'] = self.kwargs['zone_id']
        
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

        return context



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
            
            forme = data.get('forme')
            if not forme:
                return JsonResponse({'error': 'Forme manquante'}, status=400)
            
            # Réinitialiser les anciennes coordonnées et données de dimensions
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
            zone.coins = None  # Si vous avez des données en JSON pour les polygones

            # Mise à jour en fonction de la forme
            zone.forme = forme
            
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
            elif forme == 'carre':
                # Le carré est traité comme un rectangle avec 4 coins
                zone.coin1_lat = data.get('coin1_lat')
                zone.coin1_lon = data.get('coin1_lon')
                zone.coin2_lat = data.get('coin2_lat')
                zone.coin2_lon = data.get('coin2_lon')
                zone.coin3_lat = data.get('coin3_lat')
                zone.coin3_lon = data.get('coin3_lon')
                zone.coin4_lat = data.get('coin4_lat')
                zone.coin4_lon = data.get('coin4_lon')
            elif forme == 'rectangle':
                zone.coin1_lat = data.get('coin1_lat')
                zone.coin1_lon = data.get('coin1_lon')
                zone.coin2_lat = data.get('coin2_lat')
                zone.coin2_lon = data.get('coin2_lon')
                zone.coin3_lat = data.get('coin3_lat')
                zone.coin3_lon = data.get('coin3_lon')
                zone.coin4_lat = data.get('coin4_lat')
                zone.coin4_lon = data.get('coin4_lon')
            elif forme == 'polygon' or forme == 'polyline':
                # Assurez-vous que le champ 'coins' est un champ JSON ou TextField dans votre modèle
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


@login_required
def suivreBetail(request):
    user = request.user

    # Par défaut : ses propres zones
    related_users = [user]

    # Si l'utilisateur est un parent (donc sans owner)
    if not user.owner:
        related_users += list(user.sub_users.all())

    # On filtre les zones selon l'utilisateur ou ses sub-users (si c’est un parent)
    zones = ZoneSecurite.objects.filter(user__in=related_users)

    zones_data = []
    for zone in zones:
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
            'coins': zone.coins,
        })

    zones_data_json = json.dumps(zones_data)

    return render(request, 'capteurs/suivrebetail.html', {
        'user_id': user.id,  # ✅ toujours transmettre l'ID du user connecté
        'zones_data_json': zones_data_json
    })

