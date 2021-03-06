from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^mortex/', include('mortex.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^admin-media/(?P<path>.*)$', 'django.views.static.serve', {"document_root": settings.MEDIA_ROOT + "admin/"}),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_DOCROOT}),
    (r'', include('sales.urls')),
)
