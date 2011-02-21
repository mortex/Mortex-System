from django.conf.urls.defaults import *
from sales.models import ShirtStyle

info_dict = {
	'queryset': ShirtStyle.objects.all(),
}

urlpatterns = patterns('',
	(r'^styles/$', 'django.views.generic.list_detail.object_list', info_dict),
	(r'^styles/(?P<object_id>\d+)/$', 'sales.views.styleorder'),
)
