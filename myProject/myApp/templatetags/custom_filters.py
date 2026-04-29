from django import template

register = template.Library()

@register.filter
def get_range(start, end):
    return range(start, end)

@register.filter
def dict_get(d, k):
    return d.get(k)

@register.filter
def strip(value):
    if isinstance(value, str):
        return value.strip()
    return value