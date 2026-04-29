# myApp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from myApp.models import AdminProfile

@receiver(post_save, sender=User)
def create_admin_profile(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        AdminProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_admin_profile(sender, instance, **kwargs):
    if instance.is_superuser and hasattr(instance, 'admin_profile'):
        instance.admin_profile.save()