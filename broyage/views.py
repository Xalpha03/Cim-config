from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from.models import *
from packing.models import Pannes
from django.views.generic import *
from django.db.models import Q, Sum
from datetime import date, datetime, timedelta
from packing.views import get_operational_date, get_operational_month
from decimal import Decimal, ROUND_HALF_UP
from .forms import totaliForm, broyageForm
from django.contrib import messages
from packing.forms import PanneForm

# Create your views here.
    

class broyageHomeList(ListView):
    model = Broyage
    template_name = 'broyage/broyage-home.html'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = self.request.user.profil.site
        section = 'broyage'
        search = self.request.GET.get('search')
        
        filters_broy = Q(site=site)
        filters_tota = Q(site=site)
        filters_pann = Q(site=site, section=section)
        
        try:
            search_date = datetime.strptime(search, '%d/%m/%Y').date() if search else get_operational_date()
            filters_broy &= Q(date=search_date)
            filters_tota &= Q(date=search_date)
            filters_pann &= Q(date=search_date)
            
        except:
            search_date = date.today()
            filters_broy &= Q(date=search_date)
            filters_tota &= Q(date=search_date)     
            filters_pann &= Q(date=search_date)
        
        object_broy = Broyage.objects.filter(filters_broy)     
        object_pann = Pannes.objects.filter(filters_pann)
        object_tota = Totaliseur.objects.filter(filters_tota)
        
        total_temp_arret = timedelta() 
        total_temp_arret_formate = str()    
        
        for obj in object_broy:
            
            temp_arret = object_pann.filter(broyage=obj).aggregate(total=Sum('duree'))['total'] or timedelta()
            
            # Calcul de production par post
            prod = obj.dif_clinker + obj.dif_gypse + obj.dif_dolomite
            obj.prod = prod.quantize(Decimal('0'), rounding=ROUND_HALF_UP)
            
            # Calcul du temps de marche par post
            temp_march = obj.post.duree_post-temp_arret
            obj.temp_march = Decimal(temp_march.total_seconds()/3600).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            
            # Calcul du rendement par post
            rend = Decimal(prod)/Decimal(temp_march.total_seconds()/3600) if prod and temp_march else Decimal(0)
            obj.rend = rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Calcul de la consommation spécifique
            cons = Decimal(obj.dif_compt)/Decimal(prod) if prod and obj.dif_compt else Decimal(0)
            obj.cons = cons.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            print(temp_march)


        context.update({
            'broyage': 'broyage',
            'broyage_panne': 'broyage_panne',
            'search_date': search_date,
            
            'object_broy': object_broy,
            'object_pann': object_pann,
            'object_tota': object_tota,
            
            'total_temp_arret': total_temp_arret_formate,
            
            'object_post_06h': object_broy.filter(post__post='06H-14H'),
            'object_post_14h': object_broy.filter(post__post='14H-22H'),
            'object_post_22h': object_broy.filter(post__post='22H-06H'),
            
            'object_post_06_18h': object_broy.filter(post__post='06H-18H'),
            'object_post_18_06h': object_broy.filter(post__post='18H-06H'),
            
            'totalis_post_06h': object_tota.filter(post__post='06H-14H'),
            'totalis_post_14h': object_tota.filter(post__post='14H-22H'),
            'totalis_post_22h': object_tota.filter(post__post='22H-06H'),
            
            'totalis_post_06_18h': object_tota.filter(post__post='06H-18H'),
            'totalis_post_18_06h': object_tota.filter(post__post='18H-06H'),
        }) 
        return context

class ajouTotali(CreateView):
    model = Totaliseur
    form_class = totaliForm
    template_name = 'broyage/formulaire.html'
    success_url = reverse_lazy('broyage:broyage-home')
    
    def form_valid(self, form):

        form.instance.site=self.request.user.profil.site
        
        post = form.cleaned_data.get('post')
        site = self.request.user.profil.site
        date = form.cleaned_data.get('date')
        
        existe = Totaliseur.objects.filter(post=post, date=date, site=site).exists()
        if existe:
            messages.warning(self.request, "⚠️ Un totaliseur pour ce poste existe déjà aujourd’hui.")
            return redirect('broyage:ajout-totalisuer')

        messages.success(self.request, "✅ Totaliseur ajouté avec succès.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ajout_total']= 'ajout_total'
        return context
            
class ajoutBroyage(CreateView):
    model = Broyage
    form_class = broyageForm
    template_name = 'broyage/formulaire.html'
    success_url = reverse_lazy('broyage:broyage-home')
    
    def form_valid(self, form):
        slug = self.kwargs.get('slug')
        totaliseur = get_object_or_404(Totaliseur, slug=slug)
        form.instance.totaliseur=totaliseur
        form.instance.user=self.request.user
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ajout_broy']= 'ajout_broy'
        return context
    
class ajoutPanne(CreateView):
    model = Pannes
    form_class = PanneForm
    template_name = 'broyage/formulaire.html'
    
    def form_valid(self, form):
        slug = self.kwargs.get('slug')
        broyage = get_object_or_404(Broyage, slug=slug)
        profils = self.request.user.profil
        form.instance.broyage=broyage
        form.instance.site=profils.site
        form.instance.section=profils.poste
        return super().form_valid(form)
    
    def get_success_url(self):
        slug = self.kwargs.get('slug')
        base_url = reverse_lazy('broyage:ajout-broyage-panne', kwargs={'slug': slug})
        return f'{base_url}'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        slug = self.kwargs.get('slug')
        broyeur = get_object_or_404(Broyage, slug=slug)
        object_pann = Pannes.objects.filter(broyage=broyeur)
        
        context.update({
            'object_pann': object_pann,
        })
        return context

class updateTotali(UpdateView):
    model = Totaliseur
    form_class = totaliForm
    template_name = 'broyage/formulaire.html'
    slug_field = 'slug'
    success_url = reverse_lazy('broyage:broyage-home')
    context_object_name = 'update_totali'
    
class updateBroyage(UpdateView):
    model = Broyage
    form_class = broyageForm
    slug_field = 'slug'
    template_name = 'broyage/formulaire.html'
    success_url = reverse_lazy('broyage:broyage-home')
    context_object_name = 'update_broy'
          
class updatePanne(UpdateView):
    model = Pannes
    form_class = PanneForm
    template_name = 'broyage/formulaire.html'
    slug_field = 'slug'
    success_url = reverse_lazy('broyage:broyage-home')
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        
        object_pann = Pannes.objects.filter(slug=slug)
        
        context.update({
            'update_pann': 'update_pann',
            'object_pann': object_pann,
            'total_temp_arret': object_pann.aggregate(total=Sum('duree'))['total'] or timedelta()
        })
        
        return context

class broyageUserView(ListView):
    model = Broyage
    template_name = 'broyage/broyage-user-view.html'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.kwargs.get('username')
        user = get_object_or_404(User, username=user)
        search = self.request.GET.get('search')
        
        filter_broy = Q(user=user)
        filter_pann = Q(broyage__user=user)
        existe = Broyage.objects.filter(
            user=user, date__month=date.today().month,
            date__year = date.today().year
        ).exists()
        
        
        
        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]
            for kw in keywords:
                try:
                    # Essaye de convertir en date complète
                    full_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filter_broy &= Q(date=full_date)
                    filter_pann &= Q(date=full_date)
                except ValueError:
                    # Si ce n'est pas une date, on teste si c'est un entier valide
                    if kw.isdigit():
                        kw_int = int(kw)
                        if 1 <= kw_int <= 12:
                            filter_broy &= Q(date__month=kw_int)
                            filter_pann &= Q(date__month=kw_int)
                        elif 2000 <= kw_int <= datetime.now().year:
                            filter_broy &= Q(date__year=kw_int)
                            filter_pann &= Q(date__year=kw_int)
                    # Sinon, on ignore ce mot-clé
                    continue  
        
        else:
            if existe:
                search_date = date.today().month
                filter_broy &= Q(date__month=search_date, date__year=date.today().year) 
                filter_pann &= Q(date__month=search_date, date__year=date.today().year)
            else:
                search_date = get_operational_month()
                filter_broy &= Q(date__month=search_date, date__year=date.today().year)
                filter_pann &= Q(date__month=search_date, date__year=date.today().year)
            
                    
            
        object_broy = Broyage.objects.filter(filter_broy).order_by('-date', 'post')
        object_pann = Pannes.objects.filter(filter_pann).order_by('-date', 'broyage__post')
        nbr_obj = object_broy.count()
        
        search_date = ""
        total_prod = int()
        moyenne_rend = Decimal()
        moyenne_conso = Decimal()
        
        total_temp_arret = timedelta()
        total_temp_march = timedelta()
        total_compt = Decimal()
        total_temp_arret_formate = str()
        
        for obj in object_broy:
            temp_arret = object_pann.filter(broyage=obj).aggregate(total=Sum('duree'))['total'] or timedelta()
            heure = int(temp_arret.total_seconds())//3600
            minute = int(temp_arret.total_seconds())%3600 // 60
            temp_arret_formate = f'{heure:02d}:{minute:02d}'
            obj.temp_arret_formate = temp_arret_formate
            
            # Calcul de production
            prod = obj.dif_clinker + obj.dif_gypse + obj.dif_dolomite
            obj.prod = prod.quantize(Decimal('0'), rounding=ROUND_HALF_UP)
            
            # Calcul de temps de marche
            temp_march = obj.post.duree_post - temp_arret
            heure = int(temp_march.total_seconds())//3600
            minute = int(temp_march.total_seconds())%3600 // 60
            temp_march_formate = f'{heure:02d}:{minute:02d}'
            obj.temp_march_formate = temp_march_formate
            
            # Calcul du rendement
            rend = Decimal(prod)/Decimal(temp_march.total_seconds()/3600) if prod and temp_march else Decimal(0)
            obj.rend = rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Calcul de la consommtion spécifique
            conso = Decimal(obj.dif_compt)/Decimal(prod) if obj.dif_compt and prod else Decimal(0)
            obj.conso = conso.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            
            # Calcul de la production mensuelle
            total_prod += prod.quantize(Decimal('0'), rounding=ROUND_HALF_UP)
            
            # Calcul du temps de marche total
            total_temp_march += temp_march
            
            # Calcul de la moyenne du rendement
            moyenne_rend = Decimal(total_prod)/Decimal(total_temp_march.total_seconds()/3600) if total_prod and total_temp_march else Decimal(0)
            moyenne_rend = moyenne_rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) 
            
            # Calcul de la consomation spécifique moyenne
            total_compt += obj.dif_compt
            moyenne_conso = Decimal(total_compt)/Decimal(total_prod) if total_compt and total_prod else Decimal(0)
            moyenne_conso = moyenne_conso.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) 
            
            # Calcul de temps d'arrêt total
            total_temp_arret += temp_arret
            heure = int(total_temp_arret.total_seconds())//3600
            minute = int(total_temp_arret.total_seconds())%3600 // 60
            total_temp_arret_formate = f'{heure:02d}:{minute:02d}'
            total_temp_arret_formate = total_temp_arret_formate
            
            
        context.update({
            'search_date': search_date,
            'object_broy': object_broy,
            
            'total_prod': total_prod,
            'total_rend': moyenne_rend, 
            'total_conso': moyenne_conso,
            
            'total_temp_arret': total_temp_arret_formate,
            'total_temp_march': total_temp_march,
        })
        return context
        
class broyeurPanneUserView(ListView):
    model = Pannes
    template_name = 'broyage/broyage-panne-user-view.html'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.kwargs.get('username')
        user = get_object_or_404(User, username=user)
        site = user.profil.site
        section = user.profil.poste
        search = self.request.GET.get('search')
        search_date = timedelta()
        
        # filter_broy = Q(site=site, section=section)
        filter_pann = Q(broyage__user=user)
        existe = Pannes.objects.filter(broyage__user=user, date__month=date.today().month, date__year=date.today().year)

        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]
            for kw in keywords:
                try:
                    search_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filter_pann &= Q(date=search_date)
                except ValueError:
                    if kw.isdigit():
                        kw_int = int(kw)
                        
                        if 1 <= kw_int <= 12:
                            kw_int = str(kw_int)
                            search_date = datetime.strptime(kw_int, '%m').month
                            print(search_date)
                            filter_pann &= Q(date__month=search_date)
                            
                        elif 2000 <= kw_int <= date.today().year:
                            kw_int = str(kw_int)
                            search_date = datetime.strptime(kw_int, '%Y').year
                            print(search_date)
                            filter_pann &= Q(date__year=search_date)
                    continue
        else:
            if existe:
                search_date = date.today().month
                filter_pann &= Q(date__month=search_date, date__year=date.today().year)
            else:
                search_date = get_operational_month()
                print('search_date : ', search_date)
                filter_pann &= Q(date__month=search_date, date__year=date.today().year)
        
        object_pann = Pannes.objects.filter(filter_pann).order_by('-date', 'broyage__post__post')
        total_temp_arret = object_pann.aggregate(total=Sum('duree'))['total'] or timedelta()
        heure = int(total_temp_arret.total_seconds()//3600)
        minute = int(total_temp_arret.total_seconds()%3600//60)
        total_temp_arret_formate = f'{heure:02d}:{minute:02d}'
        context.update({
            'total': 'total',
            'broyage': 'broyage',
            'search_date': search_date,
            'object_pann': object_pann,
            'total_temp_arret': total_temp_arret_formate
        })
        return context    

class adminBroyage(ListView):
    model = Broyage
    template_name = 'broyage/admin-broyage.html'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        site = user.profil.site
        section = "broyage"
        search = self.request.GET.get('search')
        
        filter_broy = Q(site=site)
        filter_pann = Q(site=site, section=section)
        existe = Broyage.objects.filter(site=site, date__year=date.today().year).exists()
        
        search_date = ""
        
        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]
            for kw in keywords:
                try:
                    search_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filter_broy &= Q(date=search_date)
                    filter_pann &= Q(date=search_date)
                    continue
                except ValueError:
                    if kw.isalpha():
                        filter_broy &= Q(user__username__icontains=str(kw))
                        filter_pann &= Q(broyage__user__username__icontains=str(kw))
                    elif kw.isdigit():
                        numb = int(kw)
                        if 1 <= numb <= 12:
                            search_date = datetime.strptime(str(numb), '%m').month
                            filter_broy &= Q(date__month=search_date)
                            filter_pann &= Q(date__month=search_date)
                        elif 2000 <= numb <= date.today().year:
                            search_date = datetime.strptime(str(numb), '%Y').year
                            filter_broy &= Q(date__year=search_date)
                            filter_pann &= Q(date__year=search_date)
                            
        else:
            if existe:
                search_date = date.today().year
                filter_broy &= Q(date__year=search_date)
                filter_pann &= Q(date__year=search_date)
            else:
                search_date = get_operational_month()
                filter_broy &= Q(date__month=search_date)
                filter_pann &= Q(date__month=search_date)
                
            
        object_broy = Broyage.objects.filter(filter_broy).order_by('-date', 'post__post')
        object_pann = Pannes.objects.filter(filter_pann)
        nbr_obj = object_broy.count()
        
        total_prod = int()
        moyenne_rend = Decimal()
        moyenne_conso = Decimal()
        
        total_temp_arret = timedelta()
        total_temp_march = timedelta()
        total_compt = Decimal()
        total_temp_arret_formate = str()
                
        for obj in object_broy:
            temp_arret = object_pann.filter(broyage=obj).aggregate(total=Sum('duree'))['total'] or timedelta()
            heure = int(temp_arret.total_seconds())//3600
            minute = int(temp_arret.total_seconds())%3600 // 60
            temp_arret_formate = f'{heure:02d}:{minute:02d}'
            obj.temp_arret_formate = temp_arret_formate
            
            # Calcul de production
            prod = obj.dif_clinker + obj.dif_gypse + obj.dif_dolomite
            obj.prod = prod.quantize(Decimal('0'), rounding=ROUND_HALF_UP)
            
            # Calcul de temps de marche
            temp_march = obj.post.duree_post - temp_arret
            heure = int(temp_march.total_seconds())//3600
            minute = int(temp_march.total_seconds())%3600 // 60
            temp_march_formate = f'{heure:02d}:{minute:02d}'
            obj.temp_march_formate = temp_march_formate
            
            # Calcul du rendement
            rend = Decimal(prod)/Decimal(temp_march.total_seconds()/3600) if prod and temp_march else Decimal(0)
            obj.rend = rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Calcul de la consommtion spécifique
            conso = Decimal(obj.dif_compt)/Decimal(prod) if obj.dif_compt and prod else Decimal(0)
            obj.conso = conso.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            
            # Calcul de la production mensuelle
            total_prod += prod.quantize(Decimal('0'), rounding=ROUND_HALF_UP)
            
            # Calcul du temps de marche total
            total_temp_march += temp_march
            
            # Calcul de la moyenne du rendement
            moyenne_rend = Decimal(total_prod)/Decimal(total_temp_march.total_seconds()/3600) if total_prod and total_temp_march else Decimal(0)
            moyenne_rend = moyenne_rend.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) 
            
            # Calcul de la consomation spécifique moyenne
            total_compt += obj.dif_compt
            moyenne_conso = Decimal(total_compt)/Decimal(total_prod) if total_compt and total_prod else Decimal(0)
            moyenne_conso = moyenne_conso.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) 
            
            # Calcul de temps d'arrêt total
            total_temp_arret += temp_arret
            heure = int(total_temp_arret.total_seconds())//3600
            minute = int(total_temp_arret.total_seconds())%3600 // 60
            total_temp_arret_formate = f'{heure:02d}:{minute:02d}'
            total_temp_arret_formate = total_temp_arret_formate
        
        
        
        context.update({
            'admin': 'admin',
            'search_date': search_date,
            'object_broy': object_broy,
            
            'total_prod': total_prod,
            'total_rend': moyenne_rend, 
            'total_conso': moyenne_conso,
            
            'total_temp_arret': total_temp_arret_formate,
            'total_temp_march': total_temp_march,
            
        })
        return context
    
class adminBroyagePanne(ListView):
    model = Pannes
    template_name = 'broyage/admin-broyage-panne.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profil = self.request.user.profil
        site = profil.site
        section = 'broyage'
        search = self.request.GET.get('search')
        
        filter_pann = Q(section=section, site=site)
        existe = Pannes.objects.filter(filter_pann, date__year=date.today().year).exists()
        
        if search:
            keywords = [kw.strip() for kw in search.split(',') if kw.strip()]
            for kw in keywords:
                try:
                    search_date = datetime.strptime(kw, '%d/%m/%Y').date()
                    filter_pann &= Q(date=search_date)
                    continue
                except ValueError:
                    if kw.isalpha():
                        filter_pann &= Q(broyage__user__username__icontains=kw)
                    elif kw.isdigit():
                        numb = int(kw)
                        if 1 <= numb <= 12:
                            search_date = datetime.strptime(str(numb), '%m').month
                            filter_pann &= Q(date__month=search_date)
                        elif 2000 <= numb <= date.today().year:
                            search_date = datetime.strptime(str(numb), '%Y').year
                            filter_pann &= Q(date__year=search_date)
                        continue
                    
        else:
            if existe:
                search_date = date.today().month
                filter_pann &= Q(date__month=search_date)
            else:
                search_date = get_operational_month()
                filter_pann &= Q(date__month=search_date)
        
        object_pann = Pannes.objects.filter(filter_pann)
        
        context.update({
            'admin': 'admin',
            'total': 'total',
            'broyage': 'broyage',
            'object_pann': object_pann,
            'total_temp_arret': object_pann.aggregate(total=Sum('duree'))['total'] or timedelta(),
        })
        return context
    

class dashboard(ListView):
    model = Broyage
    template_name = 'broyage/dashboard-broyage.html'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = self.request.user.profil.site
        context.update({
            'dashboard_broyage': 'dashboard_broyage',
        })
        return context


    

