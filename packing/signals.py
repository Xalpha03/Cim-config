from django.db.models.signals import pre_save
from django.dispatch import receiver
from packing.models import Pannes

@receiver(pre_save, sender=Pannes)
def auto_prepare_panne(sender, instance, **kwargs):
    source = instance.get_source()
    if source:
        instance.date = source.date

    if not instance.slug:
        instance.slug = instance.generate_slug()

    instance.duree = instance.calculate_duree()

    if instance.description:
        instance.description = instance.description.upper()
    if instance.solution:
        instance.solution = instance.solution.upper()
