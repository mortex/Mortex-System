from django.conf.urls.defaults import *
from sales.models import ShirtStyle

info_dict = {
    'queryset': ShirtStyle.objects.all(),
}

urlpatterns = patterns('',
    (r'^shirtorders/(?P<orderid>\d+)$', 'sales.views.shirtorderview'),
    (r'^shirtorders/$', 'sales.views.shirtorders'),
)
