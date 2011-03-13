from django import template

register = template.Library()

@register.filter
def hash(h, key):
    return h[key]
    
@register.filter
def attr(obj, attrname):
    return obj.__dict__[attrname]
