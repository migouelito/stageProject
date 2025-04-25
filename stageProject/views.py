from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from capteurs.models import Message

@login_required
def homePage(request):

    # Passer l'utilisateur à la page d'accueil (base.html)
    return render(request, 'base/statistique.html')




from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from capteurs.models import Message

@login_required
def unread_messages_count(request):
    user = request.user

    # Si l'utilisateur est un parent (a des sous-utilisateurs)
    if user.sub_users.exists():
        # Le parent voit ses propres messages + ceux de ses sous-utilisateurs
        user_ids = [user.id] + list(user.sub_users.values_list('id', flat=True))
    else:
        # Si l'utilisateur n'a pas de sous-utilisateurs (sous-utilisateur ou utilisateur sans parent)
        user_ids = [user.id]

    # Filtrer les messages non lus pour ces utilisateurs
    unread_count = Message.objects.filter(user_id__in=user_ids, is_read=False).count()

    return JsonResponse({'unread_count': unread_count})




# views.py
from django.views.generic import TemplateView

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import translation

from django.shortcuts import render, redirect
from django.utils import translation
from django.contrib import messages

def Parametre_view(request):
    if request.method == 'POST':
        lang = request.POST.get('language')
        if lang:
            request.session['language'] = lang
            translation.activate(lang)
            messages.success(request, "Langue changée avec succès.")
            return redirect('parametre')

    # Récupère la langue actuelle à partir de la session
    current_language = request.session.get('language', translation.get_language())

    # 👇 Sélection du template selon le type d'utilisateur
    if request.user.is_superuser:
        template = 'base/parametreadmin.html'
    else:
        template = 'base/parametre.html'

    return render(request, template, {'language_code': current_language})
