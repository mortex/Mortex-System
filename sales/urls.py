from django.conf.urls.defaults import *
from sales.models import ShirtStyle
from django.views.generic.simple import direct_to_template

info_dict = {
    'queryset': ShirtStyle.objects.all(),
}

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'sales/index.html'}),
    
    #inventory urls
    (r'^inventory/(?P<shirtstyleid>\d+)/(?P<variationid>\d+)/(?P<colorid>\d+)$', 'sales.views.manageinventory'),
    (r'^inventory/search/$', 'sales.views.inventorysearch'),
    
    #shirt order urls
    (r'^shirtorders/(?P<orderid>\d+)/edit/$', 'sales.views.shirtorderadd'),
    (r'^shirtorders/(?P<orderid>\d+)$', 'sales.views.shirtorderview'),
    (r'^shirtorders/add/$', 'sales.views.shirtorderadd'),
    (r'^shirtorders/orderline/$', 'sales.views.orderline'),
    (r'^shirtorders/$', 'sales.views.shirtorders'),
    (r'^shirtorders/search/$', 'sales.views.shirtordersearch'),
    
    #data urls
    (r'^data/customeraddresses/$', 'sales.data_views.customeraddresses'),
    (r'^data/shirtstyles/$', 'sales.data_views.shirtstyles'),
    (r'^data/styleprices/$', 'sales.data_views.styleprices'),
    (r'^data/shirtstylevariations/$', 'sales.data_views.shirtstylevariations'),
    (r'^data/shippingorderskus/$', 'sales.data_views.shippingorderskus'),
    
    #shipping urls
    (r'^shipping/add/(?P<customeraddressid>\d+)/$', 'sales.views.addshipment'),
    (r'^shipping/add/$', 'sales.views.purchaseorders'),
    (r'^shipping/(?P<shipmentid>\d+)/edit/$', 'sales.views.addshipment'),
    (r'^shipping/(?P<shipmentid>\d+)/$', 'sales.views.viewshipment'),
    (r'^shipping/shipmentsku/$', 'sales.views.addshipmentsku'),
    (r'^shipping/search/$', 'sales.views.shipmentsearch'),
    
    #color urls
    (r'^colors/edit/$', 'sales.views.editcolors'),
    (r'^colors/addcategory/$', 'sales.views.addcategory'),
    (r'^colors/addcolor/$', 'sales.views.addcolor'),
    
    #login url
    (r'^login/$', 'django.contrib.auth.views.login'),
    
    #size urls
    (r'^sizes/edit/$', 'sales.views.editsizes'),
    (r'^sizes/addsize/$', 'sales.views.addsize'),
    
    #customer urls
    (r'^customers/(?P<customerid>\d+)/edit/$', 'sales.views.editcustomer'),
    (r'^customers/addaddress/$', 'sales.views.addcustomeraddress'),
)
