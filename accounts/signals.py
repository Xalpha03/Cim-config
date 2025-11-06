from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profil, Site

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if not created:
        # Sauvegarder le profil seulement s’il existe déjà
        if hasattr(instance, 'profil'):
            instance.profil.save()
            
            
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profil.objects.create(user=instance)


