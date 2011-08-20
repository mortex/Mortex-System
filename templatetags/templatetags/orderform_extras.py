import re

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def hash(h, key):
    return h[key]

@register.filter
def attr(obj, attrname):
    return obj.__dict__[attrname]

@register.filter
@stringfilter
def unspace(s):
    """Replace all spaces in a string with underscores

    This allows the string to be used as an HTML element's id or class
    attribute, in which spaces delimit multiple discrete values."""

    return re.sub(r" ", r"_", s)
