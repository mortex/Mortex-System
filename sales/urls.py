from django.conf.urls.defaults import *
from sales.models import ShirtPrice, ShirtStyle
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required

info_dict = {
    'queryset': ShirtStyle.objects.all(),
}

urlpatterns = patterns('',
    (r'^$', login_required(direct_to_template), {'template': 'sales/index.html'}),
    
    #authentication urls
    (r'^login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', 'django.contrib.auth.views.logout'),
    (r'^changepassword/$', 'django.contrib.auth.views.password_change'),
    (r'^changepassworddone/$', 'django.contrib.auth.views.password_change_done'),
    (r'^resetpassword/$', 'django.contrib.auth.views.password_reset', {'is_admin_site':False}),
    (r'^resetpassworddone/$', 'django.contrib.auth.views.password_reset_done'),
    (r'^resetpasswordcomplete/$', 'django.contrib.auth.views.password_reset_complete'),
    (r'^resetpasswordconfirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    
    #inventory urls
    (r'^inventory/(?P<shirtstyleid>\d+)/(?P<colorid>\d+)$', 'sales.views.manageinventory'),
    (r'^inventory/search/$', 'sales.views.inventorysearch'),
    (r'^inventory/summary$', 'sales.views.inventory_summary'),
    
    #shirt order urls
    (r'^shirtorders/(?P<orderid>\d+)/edit/$', 'sales.views.shirtorderadd'),
    (r'^shirtorders/(?P<orderid>\d+)/$', 'sales.views.shirtorderview'),
    (r'^shirtorders/(?P<orderid>\d+)/print/$', 'sales.views.printshirtorder'),
    (r'^shirtorders/add/$', 'sales.views.shirtorderadd'),
    (r'^shirtorders/orderline/$', 'sales.views.orderline'),
    (r'^shirtorders/$', 'sales.views.shirtorders'),
    (r'^shirtorders/search/$', 'sales.views.shirtordersearch'),
    
    #data urls
    (r'^shirtstyles/$', 'django.views.generic.list_detail.object_list', info_dict),
    ( r'^shirtstyles/(?P<object_id>\d+)/$',
      'django.views.generic.list_detail.object_detail',
      info_dict,
    ),
    ( r'^shirtprices/(?P<object_id>\d+)/$',
      'django.views.generic.list_detail.object_detail',
      {"queryset": ShirtPrice.objects.all()},
    ),
    (r'^shirtstyles/add/$', 'sales.views.add_style'),
    (r'^shirtstyles/edit/(?P<shirtstyleid>\d+)/$', 'sales.views.add_style'),
    (r'^shirtstyles/search/$', 'sales.views.shirtstylesearch'),
    (r'^data/customeraddresses/$', 'sales.data_views.customeraddresses'),
    (r'^data/shirtstyles/$', 'sales.data_views.shirtstyles'),
    (r'^data/styleprices/$', 'sales.data_views.styleprices'),
    (r'^data/shippingorderskus/$', 'sales.data_views.shippingorderskus'),
    
    #shipping urls
    (r'^shipping/add/(?P<shirtorderid>\d+)/$', 'sales.views.addshipment'),
    (r'^shipping/add/$', 'sales.views.purchaseorders'),
    (r'^shipping/(?P<shipmentid>\d+)/edit/$', 'sales.views.addshipment'),
    (r'^shipping/(?P<shipmentid>\d+)/$', 'sales.views.viewshipment'),
    (r'^shipping/(?P<shipmentid>\d+)/print/$', 'sales.views.printshipment'),
    (r'^shipping/(?P<shipmentid>\d+)/printboxlabels/$', 'sales.views.printboxlabels'),
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
    (r'^customers/add/$', 'sales.views.editcustomer'),
    (r'^customers/addaddress/$', 'sales.views.addcustomeraddress'),
    (r'^customers/search/$', 'sales.views.customersearch'),
)
