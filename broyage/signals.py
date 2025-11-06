from django.db.models.signals import pre_save
from django.dispatch import receiver
from broyage.models import Broyage

@receiver(pre_save, sender=Broyage)
def prepare_broyage(sender, instance, **kwargs):
    instance.totaliseur= instance.totaliseur
    instance.date = instance.totaliseur.date
    instance.post = instance.totaliseur.post
    instance.site = instance.totaliseur.site
    # if not instance.slug:
    instance.title = instance.generate_title()
    instance.slug = instance.generate_slug()
    
    
    instance.calculate_differences()
