from django.conf.urls.defaults import *
from sales.models import ShirtStyle

info_dict = {
    'queryset': ShirtStyle.objects.all(),
}

urlpatterns = patterns('',
    (r'^inventory/(?P<shirtstyleid>\d+)/(?P<variationid>\d+)/(?P<colorid>\d+)$', 'sales.views.manageinventory'),
    (r'^shirtorders/(?P<orderid>\d+)/edit/$', 'sales.views.shirtorderadd'),
    (r'^shirtorders/(?P<orderid>\d+)$', 'sales.views.shirtorderview'),
    (r'^shirtorders/add$', 'sales.views.shirtorderadd'),
    (r'^shirtorders/orderline/$', 'sales.views.orderline'),
    (r'^shirtorders/$', 'sales.views.shirtorders'),
    (r'^data/customeraddresses/$', 'sales.data_views.customeraddresses'),
    (r'^data/shirtstyles/$', 'sales.data_views.shirtstyles'),
    (r'^data/styleprices/$', 'sales.data_views.styleprices'),
    (r'^data/shirtstylevariations/$', 'sales.data_views.shirtstylevariations'),
    (r'^sizes/edit/$', 'sales.views.editsizes'),
    (r'^sizes/addsize/$', 'sales.views.addsize'),
)
