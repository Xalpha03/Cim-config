from django.contrib import admin
from .models import *
# Register your models here.

class TotaliseurDebutAdmin(admin.ModelAdmin):
    model = Totaliseur
    list_display =['post', 'site', 'compt_debut', 'clinker_debut', 'gypse_debut', 'dolomite_debut', 'date', 'slug']
    fields = ('post', 'site', 'compt_debut', 'clinker_debut', 'gypse_debut', 'dolomite_debut', 'date')
    list_filter = ['site']
    
class TotaliseurFinAdmin(admin.ModelAdmin):
    model = Broyage
    list_display = [
        'title', 'user', 'post', 'site', 'compt_fin', 'clinker_fin', 'gypse_fin', 'dolomite_fin',  
        'dif_compt', 'dif_clinker', 'dif_gypse',  'dif_dolomite', 'date', 'slug'
    ]
    fields = ('user', 'totaliseur', 'compt_fin', 'clinker_fin', 'gypse_fin', 'dolomite_fin',
        
    )
    list_filter = ['user', 'site']
    

   
admin.site.register(Totaliseur, TotaliseurDebutAdmin)
admin.site.register(Broyage, TotaliseurFinAdmin)