from django import template
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from myApp.models import AdminProfile

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    try:
        return field.as_widget(attrs={'class': css_class})
    except AttributeError:
        return field

@register.filter(name='add_attrs')
def add_attrs(field, attrs):
    attr_dict = dict(attr.split('=') for attr in attrs.split(','))
    return field.as_widget(attrs=attr_dict)

@register.filter
def split(value, delimiter=","):
    if isinstance(value, str):
        return value.split(delimiter)
    return value

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# =====

# @receiver(post_save, sender=User)
# def create_admin_profile(sender, instance, created, **kwargs):
#     if created:
#         AdminProfile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_admin_profile(sender, instance, **kwargs):
#     instance.profile.save()

