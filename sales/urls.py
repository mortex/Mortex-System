from django.conf.urls.defaults import *
from sales.models import ShirtStyle

info_dict = {
    'queryset': ShirtStyle.objects.all(),
}

urlpatterns = patterns('',)
