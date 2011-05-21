from django.conf.urls.defaults import *
from sales.models import ShirtStyle

info_dict = {
    'queryset': ShirtStyle.objects.all(),
}

urlpatterns = patterns('',
    (r'^inventory/(?P<shirtstyleid>\d+)/(?P<variationid>\d+)/(?P<colorid>\d+)$', 'sales.views.manageinventory'),
)
