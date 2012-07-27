from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from pogs.models import Galaxy

urlpatterns = patterns('',
    url(r'^$', 'pogs.views.galaxies'),
    url(r'^UserGalaxy/(?P<userid>\d+)/(?P<galaxy_id>\d+)$', 'pogs.views.userGalaxy'),
    url(r'^UserGalaxyImage/(?P<userid>\d+)/(?P<galaxy_id>\d+)/(?P<colour>\d+)$', 'pogs.views.userGalaxyImage'),
)
