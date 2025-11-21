from datetime import date
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy, reverse
from .models import *
from django.views.generic import *
from django.db.models import Q, Sum
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from datetime import time, datetime, timedelta
from .forms import PackingForm, PanneForm
from django.contrib import messages
from broyage.models import Broyage
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import HTML
from datetime import datetime, date, timedelta
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
import json

# Create your views here.


def get_operational_date():
    now = datetime.now()
    seuil = time(7, 10)  # 10h10 du matin
    if now.time() < seuil:
        return (now - timedelta(days=1)).date()
    return now.date()


def get_operational_month():
    mois = date.today().month
    # Si on est en janvier, le mois opérationnel est décembre (12)
    return 12 if mois == 1 else mois - 1


class homeView(ListView):
    model = Packing
    template_name = 'home-page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.context_packing())
        context.update(self.context_broyage())
        return context

    def context_packing(self):

        user = self.request.user
        site = user.profil.site
        section = 'packing'
        search_date = self.request.GET.get('search')

        filters_pack = Q(site=site)
        filters_pann = Q(site=site, section=section)

        broyage_existe = Broyage.objects.filter(date=date.today(), site=site)
        packing_existe = Packing.objects.filter(date=date.today(), site=site)

        print('broyage_existe : ', broyage_existe.exists())
        print('packing_existe : ', packing_existe.exists())

        if search_date:
            try:
                search_date = datetime.strptime(search_date, '%d/%m/%Y').date()
                filters_pack &= Q(date=search_date)
                filters_pann &= Q(date=search_date)
            except ValueError:
                filters_pack &= Q(pk__isnull=True)
                filters_pann &= Q(pk__isnull=True)

        else:
            if packing_existe.exists():
                search_date = date.today()
                filters_pack &= Q(date=search_date)
                filters_pann &= Q(date=search_date)

            elif broyage_existe.exists():
                search_date = date.today()
                filters_pack &= Q(date=search_date)
                filters_pann &= Q(date=search_date)

            else:
                search_date = Packing.objects.order_by(
                    '-date').values_list('date', flat=True).first()
                filters_pack &= Q(date=search_date)
                filters_pann &= Q(date=search_date)

        object_pack = Packing.objects.filter(filters_pack)
        object_pann = Pannes.objects.filter(filters_pann)
        nbr_objet = object_pack.count()

        toat_som_liv_vrack = Decimal()
        total_ens = int()
        moyenne_rend = int()
        moyenne_tx_cas = int()
        total_temp_march = Decimal()
        total_liv = int()
        total_cas = int()
        total_vrack = Decimal()
        toat_som_liv_vrack = Decimal()

        temp_arret = Decimal()
        for obj in object_pann:
            temp_arret = object_pann.aggregate(total=Sum('duree'))[
                'total'] or timedelta()
            obj.temp_arret = (Decimal(temp_arret.total_seconds(
            ))/Decimal(3600)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        for obj in object_pack:
            temp_arret = object_pann.filter(packing=obj).aggregate(
                total=Sum('duree'))['total'] or timedelta()

            # Calcul de somme de la livraison et vrack
            som_liv_vrack = obj.livraison + obj.vrack
            obj.som_liv_vrack = som_liv_vrack

            ens = obj.livraison*20
            obj.ens = ens

            # Calcul de tau de casse
            tx_cas = Decimal(obj.casse*100)/Decimal(obj.ens -
                                                    obj.casse) if obj.casse else Decimal(0)
            obj.tx_cas = tx_cas.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de temp_marche
            temp_march = obj.post.duree_post - temp_arret
            obj.temp_march = Decimal(temp_march.total_seconds(
            )/3600).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

            # Calcul de rendement
            rend = Decimal(obj.livraison/(temp_march.total_seconds()/3600)
                           ) if obj.livraison and temp_march else Decimal(0)
            obj.rend = rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la livraison total
            total_liv = object_pack.aggregate(total=Sum('livraison'))[
                'total'] or int(0)
            total_cas = object_pack.aggregate(total=Sum('casse'))[
                'total'] or int(0)
            total_vrack = object_pack.aggregate(total=Sum('vrack'))[
                'total'] or Decimal(0)
            total_vrack = total_vrack.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)
            toat_som_liv_vrack = total_liv + total_vrack

            # Calcul de la moyenne de taux de casse
            moyenne_tx_cas = Decimal(
                total_cas*100)/Decimal((total_liv*20)-total_cas) if total_cas else Decimal(0)
            moyenne_tx_cas = moyenne_tx_cas.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de temps marche total
            total_temp_march += Decimal(temp_march.total_seconds()/3600)

            # Calcul de la mpyenne du rendement
            moyenne_rend = Decimal(
                total_liv)/total_temp_march if total_liv and total_temp_march else Decimal(0)
            moyenne_rend = moyenne_rend.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            total_temp_march = total_temp_march.quantize(
                Decimal('0.1'), rounding=ROUND_HALF_UP)

        return {
            'search_date': search_date,
            'object_pack': object_pack,
            'object_pann': object_pann.order_by('packing__post'),

            'object_post_06h': object_pack.filter(post__post='06H-14H'),
            'object_post_14h': object_pack.filter(post__post='14H-22H'),
            'object_post_22h': object_pack.filter(post__post='22H-06H'),

            'object_post_06_18h': object_pack.filter(post__post='06H-18H'),
            'object_post_18_06h': object_pack.filter(post__post='18H-06H'),

            'total_liv': total_liv,
            'total_ens': total_ens,
            'total_cas': total_cas,
            'total_rend': moyenne_rend,
            'total_tx_cas': moyenne_tx_cas,
            'total_vrack': total_vrack,
            'total_temp_march': total_temp_march,
            'toat_som_liv_vrack': toat_som_liv_vrack,
            'toat_som_liv_vrack': toat_som_liv_vrack,
        }

    def context_broyage(self):
        user = self.request.user
        site = user.profil.site
        section = 'broyage'
        search_date = self.request.GET.get('search')

        filters_broy = Q(site=site)
        filters_pann = Q(site=site, section=section)

        broyage_existe = Broyage.objects.filter(date=date.today(), site=site)
        packing_existe = Packing.objects.filter(date=date.today(), site=site)
        print('broyage_existe : ', broyage_existe.exists())
        print('packing_existe : ', packing_existe.exists())

        if search_date:
            try:
                search_date = datetime.strptime(search_date, '%d/%m/%Y').date()
                filters_broy &= Q(date=search_date)
                filters_pann &= Q(date=search_date)
            except ValueError:
                filters_broy &= Q(pk__isnull=True)
                filters_pann &= Q(pk__isnull=True)

        else:
            if broyage_existe.exists():
                search_date = date.today()
                filters_broy &= Q(date=search_date)
                filters_pann &= Q(date=search_date)

            elif packing_existe.exists():
                search_date = Packing.objects.order_by(
                    '-date').values_list('date', flat=True).first()
                print('search_date : ', search_date)
                filters_broy &= Q(date=search_date)
                filters_pann &= Q(date=search_date)

            else:
                search_date = Broyage.objects.order_by(
                    '-date').values_list('date', flat=True).first()
                filters_broy &= Q(date=search_date)
                filters_pann &= Q(date=search_date)

        object_broy = Broyage.objects.filter(filters_broy)
        object_panne = Pannes.objects.filter(filters_pann)
        nbr_objet = object_broy.count()

        total_compt = Decimal()
        total_prod = Decimal()
        moyenne_rend = Decimal()
        total_temp_march = Decimal()
        moyenne_conso = Decimal()
        _total_temp_march = Decimal()
        _total_compt = Decimal()

        temp_arret = Decimal()
        for obj in object_panne:
            temp_arret = object_panne.aggregate(total=Sum('duree'))[
                'total'] or timedelta()
            obj.temp_arret = (Decimal(temp_arret.total_seconds(
            ))/Decimal(3600)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        for obj in object_broy:

            temp_arret = object_panne.filter(broyage=obj).aggregate(
                total=Sum('duree'))['total'] or timedelta()

            # Calcul de production par post
            prod = obj.dif_clinker + obj.dif_gypse + obj.dif_dolomite
            obj.prod = prod.quantize(Decimal('0'), rounding=ROUND_HALF_UP)

            # Calcul de temps de marche par post
            temp_march = obj.post.duree_post-temp_arret
            obj.temp_march = Decimal(temp_march.total_seconds(
            )/3600).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

            # Calcul du rendement par post
            rend = Decimal(prod)/Decimal(temp_march.total_seconds() /
                                         3600) if prod and temp_march else Decimal(0)
            obj.rend = rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de consomation spécifique par post
            conso = Decimal(obj.dif_compt) / \
                Decimal(prod) if obj.dif_compt and prod else Decimal(0)
            obj.conso = conso.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la production total journalière
            total_prod += obj.prod

            # Calcul du temps de marche total journalier
            _total_temp_march += Decimal(temp_march.total_seconds()/3600)
            total_temp_march = _total_temp_march.quantize(
                Decimal('0.1'), rounding=ROUND_HALF_UP)

            # Calcul de la moyenne du rendememnt journalier
            moyenne_rend = Decimal(
                total_prod)/Decimal(_total_temp_march) if total_prod and _total_temp_march else Decimal(0)
            moyenne_rend = moyenne_rend.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la moyenne de la consommation spécifique
            _total_compt += obj.dif_compt
            moyenne_conso = Decimal(
                _total_compt)/Decimal(total_prod) if _total_compt and total_prod else Decimal(0)
            moyenne_conso = moyenne_conso.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Conversion du compteur broyeur
            dif_compt = Decimal(obj.dif_compt/1000)
            obj.dif_compt = dif_compt.quantize(
                Decimal('0.1'), rounding=ROUND_HALF_UP)

            # Conversion du compteur broyeur global
            total_compt = Decimal(
                _total_compt/1000).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

            print(total_compt)

        return {

            'object_broy': object_broy,
            'object_panne': object_panne.order_by('broyage__post'),

            'object_broy_post_06h': object_broy.filter(post__post='06H-14H'),
            'object_broy_post_14h': object_broy.filter(post__post='14H-22H'),
            'object_broy_post_22h': object_broy.filter(post__post='22H-06H'),

            'object_broy_post_06_18h': object_broy.filter(post__post='06H-18H'),
            'object_broy_post_18_06h': object_broy.filter(post__post='18H-06H'),

            'total_compt': total_compt,
            'total_prod': total_prod,
            'total_temp_march_b': total_temp_march,
            'moyenne_rend_b': moyenne_rend,
            'moyenne_conso': moyenne_conso
        }


class packingHomeList(ListView):
    model = Packing
    template_name = 'packing/packing-home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('search')
        profile = self.request.user.profil
        site = profile.site
        section = 'packing'
        filters_pack = Q(site=site)
        filters_pann = Q(site=site, section=section)

        try:
            search_date = datetime.strptime(
                search, '%d/%m/%Y').date() if search else get_operational_date()
            filters_pack &= Q(date=search_date)
            filters_pann &= Q(date=search_date)
        except:
            search_date = date.today()
            filters_pack &= Q(date=search_date)
            filters_pann &= Q(date=search_date)

        object_pack = Packing.objects.filter(filters_pack)
        object_pann = Pannes.objects.filter(filters_pann)

        for obj in object_pack:

            temp_arret = object_pann.filter(packing=obj).aggregate(
                total=Sum('duree'))['total'] or timedelta()

            # Calcul de nombre de sacs livré par post
            ens = obj.livraison*20
            obj.ens = ens

            # Calcul de tau de casse par post
            tx_cas = Decimal(obj.casse*100)/Decimal(ens -
                                                    obj.casse) if obj.livraison and obj.casse else Decimal(0)
            obj.tx_cas = tx_cas.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de temps de marche par post
            temp_march = obj.post.duree_post - temp_arret
            heure = int(temp_march.total_seconds())//3600
            minute = int(temp_march.total_seconds()) % 3600 // 60
            obj.temp_march_formate = f'{heure:02d}:{minute:02d}'

            # Calcul de rendement par post
            rend = Decimal(obj.livraison)/Decimal(temp_march.total_seconds() /
                                                  3600) if obj.livraison and temp_march else Decimal(0)
            obj.rend = rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)

        context.update({

            'packing': 'packing',
            'packing_panne': 'packing_panne',
            'search_date': search_date,

            'object_post_06h': object_pack.filter(post__post='06H-14H'),
            'object_post_14h': object_pack.filter(post__post='14H-22H'),
            'object_post_22h': object_pack.filter(post__post='22H-06H'),

            'object_post_06_18h': object_pack.filter(post__post='06H-18H'),
            'object_post_18_06h': object_pack.filter(post__post='18H-06H'),

            'object_list': object_pack,
            'object_pann': object_pann.order_by('packing__post'),

        })
        return context


class ajoutPacking(CreateView):
    model = Packing
    form_class = PackingForm
    template_name = 'packing/formulaire.html'
    success_url = reverse_lazy('packing:packing-home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.site = self.request.user.profil.site

        post = form.cleaned_data.get('post')
        date = form.cleaned_data.get('date')
        site = self.request.user.profil.site

        exist = Packing.objects.filter(
            post=post, date=date, site=site).exists()
        if exist:
            messages.warning(
                self.request, "Un objet pour ce poste existe déjà aujourd’hui.")
            return redirect('packing:ajout-packing')

        messages.success(self.request, "✅ Ensachage enregistré avec succès.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ajout_packing'] = 'ajout_packing'
        return context

    # def get_success_url(self):
    #     # self.object est l’instance créée
    #     return reverse_lazy('packing-detail', kwargs={'pk': self.object.pk})


class ajoutPanne(CreateView):
    model = Pannes
    form_class = PanneForm
    template_name = 'packing/formulaire.html'

    def form_valid(self, form):
        slug = self.kwargs.get('slug')
        packing = get_object_or_404(Packing, slug=slug)
        form.instance.packing = packing
        form.instance.site = self.request.user.profil.site
        form.instance.section = self.request.user.profil.poste

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')

        packing = get_object_or_404(Packing, slug=slug)
        query_pan = Pannes.objects.filter(packing=packing)

        context.update({
            'object_pann': query_pan,
            'total_temp_arret': query_pan.aggregate(total=Sum('duree'))['total'] or timedelta()
        })
        return context

    def get_success_url(self):
        slug = self.kwargs.get('slug')
        # slug=self.object.packing.slug
        base_url = reverse('packing:ajout-packing-panne',
                           kwargs={'slug': slug})
        return f'{base_url}'


class userPackingDetail(ListView):
    model = Packing
    template_name = 'packing/packing-user-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.kwargs.get('username')
        user = get_object_or_404(User, username=user)

        search = self.request.GET.get('search')
        user = get_object_or_404(User, username=user)
        site = user.profil.site

        filter_pack = Q(user=user, site=site)
        filter_pann = Q(packing__user=user, site=site)
        existe = Packing.objects.filter(user=user, date__month=date.today(
        ).month, date__year=date.today().year).exists()

        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]

            for kw in keywords:
                try:
                    search_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filter_pack &= Q(date=search_date)
                    filter_pann &= Q(date=search_date)
                    continue
                except ValueError:
                    if kw.isdigit():
                        numb = int(kw)
                        if 1 <= numb <= 12:
                            search_date = datetime.strptime(
                                str(numb), '%m').month
                            filter_pack &= Q(date__month=search_date)
                            filter_pann &= Q(date__month=search_date)

                        elif 2000 <= numb <= date.today().year:
                            search_date = datetime.strptime(
                                str(numb), '%Y').year
                            filter_pack &= Q(date__year=search_date)
                            filter_pann &= Q(date__year=search_date)

        else:
            if existe:

                filter_pack &= Q(date__month=date.today().month,
                                 date__year=date.today().year)
                filter_pann &= Q(date__month=date.today().month,
                                 date__year=date.today().year)
            else:

                filter_pack &= Q(
                    date__month=get_operational_month(), date__year=date.today().year)
                filter_pann &= Q(
                    date__month=get_operational_month(), date__year=date.today().year)

        object_pack = Packing.objects.filter(
            filter_pack).order_by('-date', 'post__post')
        object_pann = Pannes.objects.filter(
            filter_pann).order_by('-date', 'packing__post__post')
        nbr_objet = object_pack.count()

        moyenne_tx_cas = Decimal()
        moyenne_rend = Decimal()
        total_temp_march = timedelta()
        total_liv = int()
        total_cas = int()
        total_vrack = Decimal()
        total_temp_arret = timedelta()
        total_temp_arret_formate = str()

        for obj in object_pack:

            # Temps d'arrêt par post
            temp_arret = object_pann.filter(packing=obj).aggregate(
                total=Sum('duree'))['total'] or timedelta()
            heure = int(temp_arret.total_seconds())//3600
            minute = int(temp_arret.total_seconds()) % 3600 // 60
            temp_arret_formate = f'{heure:02d}:{minute:02d}'
            obj.temp_arret_formate = temp_arret_formate

            # Calcul du temps de marche par post
            temp_march = obj.post.duree_post - temp_arret
            heure = int(temp_march.total_seconds())//3600
            minute = int(temp_march.total_seconds()) % 3600 // 60
            temp_march_formate = f'{heure:02d}:{minute:02d}'
            obj.temp_march_formate = temp_march_formate

            # Calcul du tau de casse par post
            tx_cas = Decimal(obj.casse*100)/Decimal((obj.livraison*20) -
                                                    obj.casse) if obj.livraison and obj.casse else Decimal(0)
            obj.tx_cas = tx_cas.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul du rendement par post
            rend = Decimal(obj.livraison)/(Decimal(temp_march.total_seconds()/3600)
                                           ) if obj.livraison and temp_march else Decimal(0)
            obj.rend = rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la livraison total
            total_liv = object_pack.aggregate(total=Sum('livraison'))[
                'total'] or int()

            # Calcul de casse total
            total_cas = object_pack.aggregate(total=Sum('casse'))[
                'total'] or int()

            # Calcul de la livraison vrack total
            total_vrack = object_pack.aggregate(total=Sum('vrack'))[
                'total'] or Decimal()
            total_vrack = total_vrack.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la moyenne de taux de casse
            moyenne_tx_cas = Decimal(
                total_cas*100)/Decimal((total_liv*20)-total_cas) if total_liv and total_cas else Decimal(0)
            moyenne_tx_cas = moyenne_tx_cas.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la moyenne de rendement
            total_temp_march += temp_march
            moyenne_rend = Decimal(total_liv)/Decimal(total_temp_march.total_seconds() /
                                                      3600) if total_liv and total_temp_march else Decimal(0)
            moyenne_rend = moyenne_rend.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul du temps d'arrêt total
            total_temp_arret += temp_arret
            heure = int(total_temp_arret.total_seconds())//3600
            minute = int(total_temp_arret.total_seconds()) % 3600 // 60
            total_temp_arret_formate = f'{heure:02d}:{minute:02d}'

        context.update({
            'object_pack': object_pack,
            'total_liv': total_liv,
            'total_cas': total_cas,
            'total_vrack': total_vrack,
            'moyenne_tx_cas': moyenne_tx_cas,
            'moyenne_rend': moyenne_rend,
            'total_temp_arret': total_temp_arret_formate,
            'total_temp_march': total_temp_march,
        })
        return context


class userPackingPanneDetail(ListView):
    model = Pannes
    template_name = 'packing/packing-panne-user-detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.kwargs.get('username')
        search = self.request.GET.get('search')
        user = get_object_or_404(User, username=user)
        site = self.request.user.profil.site

        filters_pann = Q(packing__user=user, site=site)
        existe = Pannes.objects.filter(
            packing__user=user,
            date__month=date.today().month,
            date__year=date.today().year
        ).exists()

        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]
            for kw in keywords:
                try:
                    full_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filters_pann &= Q(date=full_date)
                    continue
                except ValueError:
                    if kw.isdigit():
                        num = int(kw)
                        if 1 <= num <= 12:
                            filters_pann &= Q(date__month=num)
                        elif 2000 <= num <= date.today().year:
                            filters_pann &= Q(date__year=num)
                        else:
                            filters_pann &= Q(pk__isnull=True)
                    continue
        else:
            if existe:
                filters_pann &= Q(date__month=date.today().month,
                                  date__year=date.today().year)
            else:
                filters_pann &= Q(
                    date__month=get_operational_month(), date__year=date.today().year)

        object_pann = Pannes.objects.filter(
            filters_pann).order_by('-date', 'packing__post__post')

        total_temp_arret = object_pann.aggregate(total=Sum('duree'))[
            'total'] or timedelta()
        heure = int(total_temp_arret.total_seconds() // 3600)
        minute = int(total_temp_arret.total_seconds() % 3600 // 60)
        total_temp_arret_formate = f'{heure:02d}:{minute:02d}'

        context.update({
            'packing': 'packing',
            'total': 'total',
            'object_pann': object_pann,
            'total_temp_arret': total_temp_arret_formate,
            'user_detail': user,
        })
        return context


class updatePacking(UpdateView):
    model = Packing
    form_class = PackingForm
    template_name = 'packing/formulaire.html'
    context_object_name = 'object_pack'

    def get_success_url(self):
        user = self.request.user
        base_url = reverse_lazy(
            'packing:user-packing-detail', kwargs={'username': user})
        return f'{base_url}'


class deletePacking(DeleteView):
    model = Packing
    slug_field = 'slug'
    template_name = 'packing/delete.html'
    context_object_name = 'object_pack'

    def get_success_url(self):
        user = self.request.user
        base_url = reverse_lazy(
            'packing:user-packing-detail', kwargs={'username': user})
        return f'{base_url}'


class updatePackingPanne(UpdateView):
    model = Pannes
    form_class = PanneForm
    template_name = 'packing/formulaire.html'

    def get_success_url(self):
        slug = self.object.slug
        base_url = reverse_lazy(
            'packing:modifier-panne', kwargs={'slug': slug})
        return f'{base_url}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        slug = self.kwargs.get('slug')
        print(slug)

        query_pan = Pannes.objects.filter(slug=slug)

        context.update({
            'object_pann': query_pan,
            'total_temp_arret': query_pan.aggregate(total=Sum('duree'))['total'] or timedelta()
        })
        return context


class deletePackingPanne(DeleteView):
    model = Pannes
    template_name = 'packing/delete.html'

    def get_success_url(self):
        base_url = reverse('packing:user-packing-panne-detail',
                           kwargs={'username': self.request.user})
        return f'{base_url}'


class adminPackingView(ListView):
    model = Packing
    # template_name = 'packing/dashboard.html'
    template_name = 'packing/adminPacking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = self.request.user.profil.site
        section = 'packing'
        search = self.request.GET.get('search')

        filter_pack = Q(site=site)
        filter_pann = Q(site=site, section=section)
        existe = Packing.objects.filter(filter_pack, date__month=date.today(
        ).month, date__year=date.today().year).exists()

        # ✅ Filtre par date/mois/année
        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]
            for kw in keywords:
                try:
                    search_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filter_pack &= Q(date=search_date)
                    filter_pann &= Q(date=search_date)
                    continue

                except ValueError:
                    # ✅ Filtre par utilisateur
                    if kw.isalpha():
                        filter_pack &= Q(user__username__icontains=str(kw))
                        filter_pann &= Q(
                            packing__user__username__icontains=str(kw))

                    # ✅ Filtre par date/mois/année
                    elif kw.isdigit():
                        numb = int(kw)
                        if 1 <= numb <= 12:
                            search_date = datetime.strptime(
                                str(numb), '%m').month
                            filter_pack &= Q(date__month=search_date)
                            filter_pann &= Q(date__month=search_date)
                        elif 2000 <= numb <= date.today().year:
                            search_date = datetime.strptime(
                                str(numb), '%Y').year
                            filter_pack &= Q(date__year=search_date)
                            filter_pann &= Q(date__year=search_date)
                    continue

        else:
            if existe:
                search_date = date.today().year
                filter_pack &= Q(date__year=search_date)
                filter_pann &= Q(date__year=search_date)

            else:
                search_date = get_operational_month()
                filter_pack &= Q(date__month=search_date)
                filter_pann &= Q(date__month=search_date)

        object_pack = Packing.objects.filter(
            filter_pack).order_by('-date', 'post')
        object_pann = Pannes.objects.filter(
            filter_pann).order_by('-date', 'packing__post__post')
        nbr_objet = object_pack.count()

        moyenne_tx_cas = Decimal()
        moyenne_rend = Decimal()
        total_temp_march = timedelta()
        total_liv = int()
        total_cas = int()
        total_vrack = Decimal()
        total_temp_arret = timedelta()
        total_temp_arret_formate = str()

        for obj in object_pack:

            # Temps d'arrêt par post
            temp_arret = object_pann.filter(packing=obj).aggregate(
                total=Sum('duree'))['total'] or timedelta()
            heure = int(temp_arret.total_seconds())//3600
            minute = int(temp_arret.total_seconds()) % 3600 // 60
            temp_arret_formate = f'{heure:02d}:{minute:02d}'
            obj.temp_arret_formate = temp_arret_formate

            # Calcul du temps de marche par post
            temp_march = obj.post.duree_post - temp_arret
            heure = int(temp_march.total_seconds())//3600
            minute = int(temp_march.total_seconds()) % 3600 // 60
            temp_march_formate = f'{heure:02d}:{minute:02d}'
            obj.temp_march_formate = temp_march_formate

            # Calcul du tau de casse par post
            tx_cas = Decimal(obj.casse*100)/Decimal((obj.livraison*20) -
                                                    obj.casse) if obj.livraison and obj.casse else Decimal(0)
            obj.tx_cas = tx_cas.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul du rendement par post
            rend = Decimal(obj.livraison)/(Decimal(temp_march.total_seconds()/3600)
                                           ) if obj.livraison and temp_march else Decimal(0)
            obj.rend = rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la livraison total
            total_liv = object_pack.aggregate(total=Sum('livraison'))[
                'total'] or int()

            # Calcul de casse total
            total_cas = object_pack.aggregate(total=Sum('casse'))[
                'total'] or int()

            # Calcul de la livraison vrack total
            total_vrack = object_pack.aggregate(total=Sum('vrack'))[
                'total'] or Decimal()
            total_vrack = total_vrack.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la moyenne de taux de casse
            moyenne_tx_cas = Decimal(
                total_cas*100)/Decimal((total_liv*20)-total_cas) if total_liv and total_cas else Decimal(0)
            moyenne_tx_cas = moyenne_tx_cas.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul de la moyenne de rendement
            total_temp_march += temp_march
            moyenne_rend = Decimal(total_liv)/Decimal(total_temp_march.total_seconds() /
                                                      3600) if total_liv and total_temp_march else Decimal(0)
            moyenne_rend = moyenne_rend.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Calcul du temps d'arrêt total
            total_temp_arret += temp_arret
            heure = int(total_temp_arret.total_seconds())//3600
            minute = int(total_temp_arret.total_seconds()) % 3600 // 60
            total_temp_arret_formate = f'{heure:02d}:{minute:02d}'

        context.update({
            'admin': 'admin',
            'object_pack': object_pack,
            'total_livraison': total_liv,
            'total_casse': total_cas,
            'total_vrack': total_vrack,
            'moyenne_tx_casse': moyenne_tx_cas,
            'moyenne_rendement': moyenne_rend,
            'total_temp_arret': total_temp_arret_formate,
            'total_temp_march': total_temp_march,
        })
        return context


class adminPackingPanneViews(ListView):
    model = Pannes
    template_name = 'packing/adminPackingPanne.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = self.request.user
        site = current_user.profil.site
        section = "packing"

        search = self.request.GET.get('search')

        filters_pann = Q(site=site, section=section)
        existe = Pannes.objects.filter(
            filters_pann, date__month=date.today().month, date__year=date.today().year)

        # ✅ Filtre par date/mois/année
        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]
            for kw in keywords:
                try:
                    search_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filters_pann &= Q(date=search_date)
                    continue

                except ValueError:
                    # ✅ Filtre par utilisateur
                    if kw.isalpha():
                        filters_pann &= Q(
                            packing__user__username__icontains=str(kw))
                    elif kw.isdigit():
                        numb = int(kw)

                        if 1 <= numb <= 12:
                            search_date = datetime.strptime(
                                str(numb), '%m').month
                            filters_pann &= Q(date__month=search_date)

                        elif 2000 <= numb <= date.today().year:
                            search_date = datetime.strptime(
                                str(numb), '%Y').year
                            filters_pann &= Q(date__year=search_date)
                        continue
        else:
            if existe:
                search_date = date.today().month
                filters_pann &= Q(date__month=search_date)
            else:
                search_date = get_operational_month()
                filters_pann &= Q(date__month=search_date)

        object_pann = Pannes.objects.filter(
            filters_pann).order_by('-date', 'packing__post__post')

        total_temp_arret = object_pann.aggregate(total=Sum('duree'))[
            'total'] or timedelta()
        heure = int(total_temp_arret.total_seconds()//3600)
        minute = int(total_temp_arret.total_seconds() % 3600//60)
        total_temp_arret_formate = f'{heure:02d}:{minute:02d}'

        context.update({
            'admin': 'admin',
            'total': 'total',
            'packing': 'packing',
            'total': 'total',
            'object_pann': object_pann,
            'total_temp_arret': total_temp_arret_formate,

        })
        return context


class userPackingPanneDetailPdf(TemplateView):
    model = Pannes
    template_name = 'packing/packing-panne-user-pdf.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.kwargs.get('username')
        search = self.request.GET.get('search')
        user = get_object_or_404(User, username=user)
        site = self.request.user.profil.site

        filters_pann = Q(packing__user=user, site=site)
        existe = Pannes.objects.filter(
            packing__user=user,
            date__month=date.today().month,
            date__year=date.today().year
        ).exists()

        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]
            for kw in keywords:
                try:
                    full_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filters_pann &= Q(date=full_date)
                    continue
                except ValueError:
                    if kw.isdigit():
                        num = int(kw)
                        if 1 <= num <= 12:
                            filters_pann &= Q(date__month=num)
                        elif 2000 <= num <= date.today().year:
                            filters_pann &= Q(date__year=num)
                        else:
                            filters_pann &= Q(pk__isnull=True)
                    continue
        else:
            if existe:
                filters_pann &= Q(date__month=date.today().month,
                                  date__year=date.today().year)
            else:
                filters_pann &= Q(
                    date__month=get_operational_month(), date__year=date.today().year)

        object_pann = Pannes.objects.filter(
            filters_pann).order_by('-date', 'packing__post__post')
        total_temp_arret = object_pann.aggregate(total=Sum('duree'))[
            'total'] or timedelta()
        heure = int(total_temp_arret.total_seconds() // 3600)
        minute = int(total_temp_arret.total_seconds() % 3600 // 60)
        total_temp_arret_formate = f'{heure:02d}:{minute:02d}'

        context.update({
            'packing': 'packing',
            'total': 'total',
            'object_pann': object_pann,
            'total_temp_arret': total_temp_arret_formate,
            'user_detail': user,
        })
        return context

    def get(self, request, *args, **kwargs):
        # Récupérer le contexte normalement
        context = self.get_context_data(**kwargs)
        context['pdf'] = True  # Indique au template que c’est pour le PDF

        # Charger et rendre le template
        template = get_template(self.template_name)
        html_string = template.render(context)

        # Générer le PDF avec WeasyPrint
        pdf_file = HTML(string=html_string,
                        base_url=request.build_absolute_uri()).write_pdf()

        # Retourner le PDF dans le navigateur (nouvel onglet)
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="rapport.pdf"'
        return response


# def dashbord(request):
#     site = request.user.profil.site  # ✅ filtrage par site
#     packings = Packing.objects.filter(site=site)

#     total_livraison = sum(p.livraison for p in packings)
#     total_casse = sum(p.casse for p in packings)
#     total_ensachage = sum((p.livraison*20) for p in packings)
#     taux_casse = ((total_casse*100) / (total_ensachage - total_casse)) if total_casse else 0

#     context = {
#         "site": site,
#         "total_livraison": total_livraison,
#         "total_casse": total_casse,
#         "total_ensachage": total_ensachage,
#         "taux_casse": round(taux_casse, 2),
#         "packings": packings,
#     }
#     return render(request, "packing/dashboard.html", context)


class dashboard(ListView):
    model = Packing
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profil = self.request.user.profil
        section = 'packing'

        search = self.request.GET.get('search')

        filter_packing = Q(site=profil.site)
        filter_panne = Q(site=profil.site, section=section)

        packing_existe = Packing.objects.filter(
            site=profil.site, date__month=date.today().month)

        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]

            for kw in keywords:
                try:
                    search_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filter_packing &= Q(date=search_date)
                    filter_panne &= Q(date=search_date)
                    continue
                except ValueError:
                    if kw.isalpha():
                        if self.request.user.is_superuser:
                            filter_packing &= Q(user__username__icontains=str(kw))
                            filter_panne &= Q(packing__user__username__icontains=str(kw))

                        else:
                            messages.warning(self.request, "vous n'êtes pas autorisé à faire des recherches sur {}".format(kw))

                    elif kw.isdigit():
                        numb = int(kw)
                        if 1 <= len(kw) <= 2 and 1 <= numb <= 12:
                            search_date = datetime.strptime(
                                str(numb), '%m').month
                            filter_packing &= Q(date__month=search_date)
                            filter_panne &= Q(date__month=search_date)

                        elif len(kw) == 4 and 2000 <= numb <= date.today().year:
                            search_date = datetime.strptime(
                                str(numb), '%Y').year
                            filter_packing &= Q(date__year=search_date)
                            filter_panne &= Q(date__year=search_date)
                    continue

        else:
            if packing_existe.exists():
                search_date = date.today().month
                filter_packing &= Q(date__month=search_date)
                filter_panne &= Q(date__month=search_date)

            else:
                search_date = get_operational_month()
                filter_packing &= Q(date__month=search_date)
                filter_panne &= Q(date__month=search_date)

        pannes = Pannes.objects.filter(filter_panne)
        packings = Packing.objects.filter(filter_packing)

        labels, livraison, casse, tx_casse, rendement, temp_march = [], [], [], [], [], []
        total_temp_march = timedelta()
        for obj in packings:

            temp_arret = pannes.filter(packing=obj).aggregate(
                total=Sum('duree'))['total'] or timedelta()
            temp_march_val = obj.post.duree_post - temp_arret

            tx_cas = Decimal((obj.casse * 100) / ((obj.livraison * 20) -
                             obj.casse)) if obj.livraison and obj.casse else Decimal(0)
            obj.tx_casse = tx_cas.quantize(
                Decimal('.01'), rounding=ROUND_HALF_UP)

            rendement_val = Decimal(obj.livraison) / \
                Decimal(temp_march_val.total_seconds() / 3600)
            obj.rendement = rendement_val.quantize(
                Decimal('.01'), rounding=ROUND_HALF_UP)

            obj.temp_march = Decimal(temp_march_val.total_seconds(
            ) / 3600).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

            # Remplir les listes
            labels.append(obj.date.strftime("%d/%m/%Y"))
            livraison.append(float(obj.livraison))
            casse.append(float(obj.casse))
            tx_casse.append(float(obj.tx_casse))
            rendement.append(float(obj.rendement))
            temp_march.append(float(obj.temp_march))

            total_livraison = sum(p.livraison for p in packings)
            total_casse = sum(p.casse for p in packings)
            moyenne_tx_casse = (Decimal(total_casse * 100) / Decimal(
                (total_livraison * 20) - total_casse)) if total_casse else Decimal(0)

            total_temp_march += (obj.post.duree_post-temp_arret)
            moyenne_rendement = Decimal(
                total_livraison) / Decimal(total_temp_march.total_seconds()/3600) if total_livraison else Decimal(0)

        context.update({
            "packings": packings,
            "labels": json.dumps(labels),
            "livraison": json.dumps(livraison),
            "casse": json.dumps(casse),
            "tx_casse": json.dumps(tx_casse),
            "rendement": json.dumps(rendement),
            "temp_march": json.dumps(temp_march),

            "total_livraison": total_livraison,
            "total_casse": total_casse,
            "moyenne_tx_casse": moyenne_tx_casse.quantize(Decimal('.01'), rounding=ROUND_HALF_UP),
            "moyenne_rendement": moyenne_rendement.quantize(Decimal('.01'), rounding=ROUND_HALF_UP),
        })
        return context
