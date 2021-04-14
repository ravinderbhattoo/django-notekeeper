from django import template
from django.shortcuts import reverse

register = template.Library()

@register.simple_tag
def add_active(request, name, slug):
    if slug:
        path = reverse(name, kwargs={'slug': slug})
    else :
        path = reverse(name)
    if request.path == path:
        return "active"
    return ""


@register.filter(name='ext_image')
def ext_image(field):
    """If it have image ext."""
    ext = field.name.split(".")[-1]
    if ext in ["png", "jpg", "jpeg", "eps", "ico"]:
        return field
    else:
        return ""

@register.filter(name='remove_root')
def remove_root(field):
    """Replace txt."""
    return field.replace("/media", "media").replace("<p>","").replace("</p>","")

@register.filter(name='add_css')
def add_css(field, css):
    """Removes all values of arg from the given string"""
    return field.fileas_widget(attrs={"class": css})