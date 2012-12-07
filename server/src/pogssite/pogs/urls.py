#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
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
    url(r'^GalaxyList/(?P<page>\d+)$', 'pogs.views.galaxyListOld'),
    url(r'^GalaxyList/$', 'pogs.views.galaxyList'),
    url(r'^GalaxyList$', 'pogs.views.galaxyList'),
    url(r'^GalaxyImage/(?P<galaxy_id>\d+)/(?P<colour>\d+)$', 'pogs.views.galaxyImage'),
    url(r'^GalaxyImageFilter/(?P<galaxy_id>\d+)/(?P<image_number>\d+)$', 'pogs.views.galaxyImageFilter'),
    url(r'^GalaxyThumbnailImage/(?P<galaxy_id>\d+)/(?P<colour>\d+)$', 'pogs.views.galaxyThumbnailImage'),
)
