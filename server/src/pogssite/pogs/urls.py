from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from django.views.generic.simple import redirect_to
from pogs.models import Galaxy

urlpatterns = patterns('',
    url(r'^$', redirect_to, {'url': '/pogs/login_form.php', 'permanent': False}),
    url(r'^(?P<userid>\d+)$', 'pogs.views.userGalaxies'),
    url(r'^UserGalaxy/(?P<userid>\d+)/(?P<galaxy_id>\d+)$', 'pogs.views.userGalaxy'),
    url(r'^UserGalaxyImage/(?P<userid>\d+)/(?P<galaxy_id>\d+)/(?P<colour>\d+)$', 'pogs.views.userGalaxyImage'),
    url(r'^Galaxy/(?P<galaxy_id>\d+)$', 'pogs.views.galaxy'),
    url(r'^GalaxyParameterImage/(?P<galaxy_id>\d+)/(?P<name>\w+)$', 'pogs.views.galaxyParameterImage'),
    url(r'^GalaxyList/(?P<page>\d+)$', 'pogs.views.galaxyList'),
    url(r'^GalaxyImage/(?P<galaxy_id>\d+)/(?P<colour>\d+)$', 'pogs.views.galaxyImage'),
)
