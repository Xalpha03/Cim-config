from django.contrib import admin
from .models import *

# Register your models here.


class PostAdmin(admin.ModelAdmin):
    model = Post
    list_display = ['post', 'start_post', 'end_post', 'duree_post']
    fields = ('post', 'start_post', 'end_post', )
    
class PackingAdmin(admin.ModelAdmin):
    model = Packing
    list_display = ['user', 'post', 'site', 'livraison', 'casse', 'vrack', 'date', 'slug']
    fields = ('user', 'post', 'site', 'livraison', 'casse', 'vrack', 'date')
    list_filter = ('post', 'site', 'user')
    
class PanneAdmin(admin.ModelAdmin):
    model = Pannes
    list_display = ['departement', 'site', 'packing', 'broyage', 'section', 'start_panne', 'end_panne', 'duree', 'description', 'date', 'slug']
    fields = ('departement', 'site', 'packing', 'broyage', 'section', 'start_panne', 'end_panne', 'description', 'solution')
    
    
    
admin.site.register(Post, PostAdmin)
admin.site.register(Pannes, PanneAdmin)
admin.site.register(Packing, PackingAdmin)
