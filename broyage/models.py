from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.text import slugify
from django.utils import timezone
from accounts.models import Site

# Create your models here

class Totaliseur(models.Model):
    post = models.ForeignKey('packing.Post', on_delete=models.CASCADE, default='06H-14H')
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    compt_debut = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    clinker_debut = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    gypse_debut = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    dolomite_debut = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    date = models.DateField(default=timezone.now)
    slug = models.SlugField()
    
    class Meta:
        verbose_name = 'Totaliseur'
        verbose_name_plural = 'Totaliseur'
        ordering = ('-date', 'post__post')
        
    def get_shift_letter(self):
        return {
            '06H-14H': 'A',
            '14H-22H': 'B',
            '22H-06H': 'C',
            
            '06H-18H': 'A',
            '18H-06H': 'B',
        }.get(self.post.post, '?')
        
    def generate_title(self):
        date_str = self.date.strftime('%d/%m/%Y')
        return f"Totaliseur_{date_str}_{self.get_shift_letter()}_{self.site}"

    def generate_slug(self):
        date_str = self.date.strftime('%d-%m-%Y')
        return f"Totaliseur_{slugify(date_str)}_{self.get_shift_letter()}_{self.site}-{int(datetime.now().timestamp())}"
    
    def __str__(self):
        return self.generate_title()

    def save(self, *args, **kwargs):
        # if not self.slug:
        self.slug = self.generate_slug()
        super().save(*args, **kwargs)



    

class Broyage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey('packing.Post', on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    totaliseur = models.ForeignKey(Totaliseur, on_delete=models.CASCADE, blank=True)
    title = models.CharField(max_length=50)
    compt_fin = models.DecimalField(max_digits=20, decimal_places=2)
    clinker_fin = models.DecimalField(max_digits=20, decimal_places=2)
    gypse_fin = models.DecimalField(max_digits=20, decimal_places=2)
    dolomite_fin = models.DecimalField(max_digits=20, decimal_places=2)
    dif_compt = models.DecimalField(max_digits=25, decimal_places=2, blank=True, null=True)
    dif_clinker = models.DecimalField(max_digits=25, decimal_places=2, blank=True, null=True)
    dif_dolomite = models.DecimalField(max_digits=25, decimal_places=2, blank=True, null=True)
    dif_gypse = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    slug = models.SlugField()
    
    class Meta:
        verbose_name = 'Grinding'
        verbose_name_plural = 'Grinding'
        ordering =  ['site', '-date', 'post']
        
    def __str__(self):
        return self.title

    def generate_title(self):
        date_str = self.totaliseur.date.strftime("%Y-%m-%d")
        shift = {'06H-14H': 'A', '14H-22H': 'B', '06H-18H': 'A', '18H-06H': 'B'}.get(self.post.post, 'C')
        return f"Broy_{date_str}_{shift}_{self.site}"

    def generate_slug(self):
        return f"{slugify(self.title)}-{int(datetime.now().timestamp())}"

    def calculate_differences(self):
        
        query = Totaliseur.objects.filter(
            post=self.totaliseur.post,
            date=self.totaliseur.date,
            site=self.site
        ).first()

        if query:
            self.dif_compt = self.compt_fin - query.compt_debut
            self.dif_clinker = self.clinker_fin - query.clinker_debut
            self.dif_dolomite = self.dolomite_fin - query.dolomite_debut
            self.dif_gypse = self.gypse_fin - query.gypse_debut
        else:
            self.dif_compt = self.dif_clinker = self.dif_dolomite = self.dif_gypse = 0
            
            

       
            
