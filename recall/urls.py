from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin

import render.views

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'recall.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', render.views.RenderFromUrlView.as_view())
)

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    try:
        import debug_toolbar
    except:
        debug_toolbar = None

    if debug_toolbar is not None:
        urlpatterns += patterns(
            '',
            url(r'^__debug__/', include(debug_toolbar.urls)),
        )
