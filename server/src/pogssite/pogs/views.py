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
import os
import datetime
import tempfile

from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from django.utils import simplejson
from sqlalchemy.engine import create_engine
from sqlalchemy.sql.expression import select, and_, not_
from config import DJANGO_IMAGE_DIR, DB_LOGIN
from image import fitsimage, directory_mod
from pogs.models import Galaxy
from database.database_support_core import AREA, AREA_USER, GALAXY, DOCMOSIS_TASK, DOCMOSIS_TASK_GALAXY, IMAGE_FILTERS_USED, FILTER

ENGINE = create_engine(DB_LOGIN)

class GalaxyLine:
    def __init__(self):
        self.names = []
        self.ids = []
        self.redshifts = []
        self.widths = []
        self.heights = []

class GalaxyInfo:
    def __init__(self):
        self.galaxy_id = 0
        self.name = ""
        self.ra_cent = 0.0
        self.dec_cent = 0.0
        self.galaxy_type = ""
        self.redshift = 0
        self.dimensions = ""
        self.pct_complete = "0.00%"

def getReferer(request):
    """
    Get the referrer
    """
    try:
        referer = request.META['HTTP_REFERER']
    except KeyError:
        referer = None

    if referer == '' or referer is None:
        referer = 'pogs'
    else:
        parts = referer.split('/')
        referer = parts[3]
    if referer == 'pogssite':
        referer = getRefererFromCookie(request)
    return referer

def getRefererFromCookie(request):
    try:
        referer = request.COOKIES['pogs_referer']
    except KeyError:
        referer = None
    if referer == '' or referer is None:
        referer = 'pogs'
    return referer

def setReferrer(response, referer):
    response.set_cookie('pogs_referer', referer)

def userGalaxies(request, userid):
    pogs_connection = ENGINE.connect()

    user_galaxy_list = []
    idx = 0
    galaxy_line = GalaxyLine()
    for galaxy in user_galaxies(pogs_connection, userid):
        name = galaxy.name
        if galaxy.version_number > 1:
            name = galaxy.name + "[" + str(galaxy.version_number) + "]"
        if not idx:
            galaxy_line = GalaxyLine()
            galaxy_line.names = []
            galaxy_line.ids = []
            galaxy_line.redshifts = []
            user_galaxy_list.append(galaxy_line)
        galaxy_line.names.append(name)
        galaxy_line.ids.append(galaxy.galaxy_id)
        galaxy_line.redshifts.append(str(galaxy.redshift))

        idx += 1
        if idx > 5:
            idx = 0
    pogs_connection.close()
    referer = getReferer(request)

    t = loader.get_template('pogs/index.html')
    c = Context({
        'user_galaxy_list': user_galaxy_list,
        'userid':           userid,
        'referer':          referer,
    })
    response = HttpResponse(t.render(c))
    setReferrer(response, referer)
    return response

def userGalaxy(request, userid, galaxy_id):

    userid = int(userid)
    galaxy_id = int(galaxy_id)

    connection = ENGINE.connect()

    if request.is_ajax():
        query = select([DOCMOSIS_TASK])
        query = query.where(DOCMOSIS_TASK.c.userid == userid)
        query = query.order_by(DOCMOSIS_TASK.c.create_time.desc())
        user = connection.execute(query).first()
        data = 0
        if user:
            datetime_diff = datetime.datetime.utcnow() - user.create_time
            if datetime_diff.seconds < 60:
                data = simplejson.dumps({'success':'False', 'message':'Too recent attempt'})
        if not data:

            # Get task assigned
            task_id = connection.execute(DOCMOSIS_TASK.insert().values(userid = userid)).lastrowid
            # Add galaxy to task
            connection.execute(DOCMOSIS_TASK_GALAXY.insert().values(task_id = task_id, galaxy_id = galaxy_id))
            # Set task to ready status
            connection.execute(DOCMOSIS_TASK.update().where(DOCMOSIS_TASK.c.task_id == task_id).values(status = 1))

            data = simplejson.dumps({'success':'True'})
        response = HttpResponse(data,content_type="application/javascript")
    else:
        galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()
        galaxy_name = galaxy[GALAXY.c.name]
        if galaxy[GALAXY.c.version_number] > 1:
            galaxy_name = galaxy[GALAXY.c.name] + "[" + str(galaxy[GALAXY.c.version_number]) + "]"
        galaxy_height = galaxy[GALAXY.c.dimension_x]
        galaxy_width = galaxy[GALAXY.c.dimension_y]
        
        map_imf = {}
        try: 
            map_fl = {}
            for filter in connection.execute(select([FILTER])):
                map_fl[filter.filter_id] = filter.label
            query = select([IMAGE_FILTERS_USED]).where(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id)
            for image in connection.execute(query):
                fstr = map_fl[image.filter_id_red]
                fstr = fstr + ", " + map_fl[image.filter_id_green]
                fstr = fstr + ", " + map_fl[image.filter_id_blue]
                map_imf[image.image_number] = fstr 
        except: 
            for i in range(1, 4):
                map_imf[i] = 'Unknown Filter'

        referer = getRefererFromCookie(request)

        t = loader.get_template('pogs/user_images.html')
        c = Context({
            'userid': userid,
            'galaxy_id': galaxy_id,
            'galaxy_name': galaxy_name,
            'galaxy_width': galaxy_width,
            'galaxy_height': galaxy_height,
            'image1_filters': map_imf[1], 
            'image2_filters': map_imf[2], 
            'image3_filters': map_imf[3], 
            'image4_filters': map_imf[4], 
            'referer':          referer,
        })
        response = HttpResponse(t.render(c))

    connection.close()
    return response

def userGalaxyImage(request, userid, galaxy_id, colour):
    tmp = tempfile.mkstemp(".png", "pogs", None, False)
    file = tmp[0]
    os.close(file)

    imageDirName = DJANGO_IMAGE_DIR

    outImageFileName = tmp[1]

    connection = ENGINE.connect()
    userid = int(userid)
    galaxy_id = int(galaxy_id)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()
    imagePrefixName = galaxy[GALAXY.c.name] + "_" + str(galaxy[GALAXY.c.version_number])

    image = fitsimage.FitsImage(connection)
    inImageFileName = directory_mod.get_colour_image_path(imageDirName, imagePrefixName, colour, False)
    image.markImage(inImageFileName, outImageFileName, galaxy_id, userid)
    connection.close()

    sizeBytes = os.path.getsize(outImageFileName)
    file = open(outImageFileName, "rb")
    myImage = file.read(sizeBytes)
    file.close()
    os.remove(outImageFileName)

    DELTA = datetime.timedelta(minutes=10)
    DELTA_SECONDS = DELTA.days * 86400 + DELTA.seconds
    EXPIRATION_MASK = "%a, %d %b %Y %H:%M:%S %Z"
    expires = (datetime.datetime.now()+DELTA).strftime(EXPIRATION_MASK)

    response = HttpResponse(myImage, content_type='image/png')
    response['Content-Disposition'] = 'filename=\"' + imagePrefixName + '_' + colour + '.png\"'
    response['Expires'] = expires
    response['Cache-Control'] = "public, max-age=" + str(DELTA_SECONDS)
    return response

def galaxy(request, galaxy_id):
    connection = ENGINE.connect()
    galaxy_id = int(galaxy_id)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()
    galaxy_name = galaxy[GALAXY.c.name]
    if galaxy[GALAXY.c.version_number] > 1:
        galaxy_name = galaxy[GALAXY.c.name] + "[" + str(galaxy[GALAXY.c.version_number]) + "]"
    galaxy_height = galaxy[GALAXY.c.dimension_x]
    galaxy_width = galaxy[GALAXY.c.dimension_y]
    connection.close()

    referer = getRefererFromCookie(request)

    t = loader.get_template('pogs/galaxy_images.html')
    c = Context({
        'galaxy_id': galaxy_id,
        'galaxy_name': galaxy_name,
        'galaxy_width': galaxy_width,
        'galaxy_height': galaxy_height,
        'referer':          referer,
    })
    return HttpResponse(t.render(c))

def galaxyListOld(request, page):
    return HttpResponseRedirect("../GalaxyList?page=" + page)

def galaxyList(request):
    try:
        page = request.GET["page"]
    except KeyError:
        page = 1
    try:
        type = request.GET["type"]
    except KeyError:
        type = ""
    try:
        name = request.GET["name"].upper()
    except KeyError:
        name = ""
    try:
        ra_from = request.GET["ra_from"]
    except KeyError:
        ra_from= ""
    try:
        ra_to = request.GET["ra_to"]
    except KeyError:
        ra_to = ""
    try:
        dec_from = request.GET["dec_from"]
    except KeyError:
        dec_from = ""
    try:
        dec_to = request.GET["dec_to"]
    except KeyError:
        dec_to = ""
    try:
        sort = request.GET["sort"]
    except KeyError:
        sort = "NAME"
    try:
        per_page = request.GET["per_page"]
    except KeyError:
        per_page = "20"

    lines_per_page = int(per_page)
    galaxies_per_line = 1
    page = int(page)
    if page < 1:
        page = 1
    start = (page-1) * lines_per_page * galaxies_per_line
    next_page = None
    if page == 1:
        prev_page = None
    else:
        prev_page = page - 1
    connection = ENGINE.connect()
    query = select([GALAXY]).where(GALAXY.c.current == True)
    if type == "S":
        query = query.where(and_(GALAXY.c.galaxy_type.like('S%'), not_(GALAXY.c.galaxy_type.like('SB%')), not_(GALAXY.c.galaxy_type.like('S0%'))))
    elif type == "SB":
        query = query.where(GALAXY.c.galaxy_type.like('SB%'))
    elif type == "L":
        query = query.where(GALAXY.c.galaxy_type.like('S0%'))
    elif type == "E":
        query = query.where(GALAXY.c.galaxy_type.like('E%'))
    elif type == "I":
        query = query.where(GALAXY.c.galaxy_type.like('I%'))

    if name != "":
        query = query.where(GALAXY.c.name.like('"' + name + '"%'))

    if ra_from != "" and ra_to != "":
        query = query.where(GALAXY.c.ra_cent.between(float(ra_from), float(ra_to)))
    elif ra_from != "":
        query = query.where(GALAXY.c.ra_cent >= float(ra_from))
    elif ra_to != "":
        query = query.where(GALAXY.c.ra_cent <= float(ra_to))

    if dec_from != "" and dec_to != "":
        query = query.where(GALAXY.c.dec_cent.between(float(dec_from), float(dec_to)))
    elif dec_from != "":
        query = query.where(GALAXY.c.dec_cent >= float(dec_from))
    elif dec_to != "":
        query = query.where(GALAXY.c.dec_cent <= float(dec_to))

    if sort == "NAME":
        query = query.order_by(GALAXY.c.name, GALAXY.c.version_number)
    elif sort == "RADEC":
        query = query.order_by(GALAXY.c.ra_cent, GALAXY.c.dec_cent)
    elif sort == "TYPE":
        query = query.order_by(GALAXY.c.galaxy_type)
        query = query.order_by(GALAXY.c.name, GALAXY.c.version_number)
    elif sort == "USED":
        query = query.order_by(GALAXY.c.image_time.desc())
        query = query.order_by(GALAXY.c.name, GALAXY.c.version_number)
    else:
        query = query.order_by(GALAXY.c.name, GALAXY.c.version_number)
    galaxies = connection.execute(query)
    galaxy_list = []
    count = 0

    for galaxy in galaxies:
        count += 1
        if count < start:
            pass
        elif len(galaxy_list) >= lines_per_page:
            next_page = page + 1
            break
        else:
            line = GalaxyInfo()
            line.name = galaxy[GALAXY.c.name]
            line.galaxy_id = galaxy[GALAXY.c.galaxy_id]
            line.ra_cent = galaxy[GALAXY.c.ra_cent]
            line.dec_cent = galaxy[GALAXY.c.dec_cent]
            line.redshift = galaxy[GALAXY.c.redshift]
            line.galaxy_type = galaxy[GALAXY.c.galaxy_type]
            line.dimensions = '{0} x {1}'.format(galaxy[GALAXY.c.dimension_x], galaxy[GALAXY.c.dimension_y])
            if galaxy[GALAXY.c.pixel_count] is None or galaxy[GALAXY.c.pixels_processed] is None or galaxy[GALAXY.c.pixel_count] == 0:
                line.pct_complete = "0.00%"
            else:
                line.pct_complete = "{:.2%}".format(galaxy[GALAXY.c.pixels_processed]*1.0/galaxy[GALAXY.c.pixel_count])
            galaxy_list.append(line)
    connection.close()
    referer = getReferer(request)

    t = loader.get_template('pogs/galaxy_list.html')
    c = Context({
        'galaxy_list':      galaxy_list,
        'prev_page':        prev_page,
        'next_page':        next_page,
        'referer':          referer,
        'type':             type,
        'name':             name,
        'ra_from':          ra_from,
        'ra_to':            ra_to,
        'dec_from':         dec_from,
        'dec_to':           dec_to,
        'sort':             sort,
        'per_page':         per_page,
    })
    response = HttpResponse(t.render(c))
    setReferrer(response, referer)
    return response

def galaxyImage(request, galaxy_id, colour):
    imageDirName = DJANGO_IMAGE_DIR

    connection = ENGINE.connect()
    galaxy_id = int(galaxy_id)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()

    image = fitsimage.FitsImage(connection)
    imagePrefixName = '{0}_{1}'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number])
    imageFileName = image.get_colour_image_path(imageDirName, imagePrefixName, colour, False)
    connection.close()

    sizeBytes = os.path.getsize(imageFileName)
    file = open(imageFileName, "rb")
    myImage = file.read(sizeBytes)
    file.close()

    DELTA = datetime.timedelta(minutes=100)
    DELTA_SECONDS = DELTA.days * 86400 + DELTA.seconds
    EXPIRATION_MASK = "%a, %d %b %Y %H:%M:%S %Z"
    expires = (datetime.datetime.now()+DELTA).strftime(EXPIRATION_MASK)

    response = HttpResponse(myImage, content_type='image/png')
    response['Content-Disposition'] = 'filename=\"' + imageFileName + '\"'
    response['Expires'] = expires
    response['Cache-Control'] = "public, max-age=" + str(DELTA_SECONDS)
    return response

def galaxyThumbnailImage(request, galaxy_id, colour):
    imageDirName = DJANGO_IMAGE_DIR

    connection = ENGINE.connect()
    galaxy_id = int(galaxy_id)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()

    imagePrefixName = '{0}_{1}'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number])
    imageFileName = directory_mod.get_thumbnail_colour_image_path(imageDirName, imagePrefixName, colour, False)
    connection.close()

    sizeBytes = os.path.getsize(imageFileName)
    file = open(imageFileName, "rb")
    myImage = file.read(sizeBytes)
    file.close()

    DELTA = datetime.timedelta(minutes=100)
    DELTA_SECONDS = DELTA.days * 86400 + DELTA.seconds
    EXPIRATION_MASK = "%a, %d %b %Y %H:%M:%S %Z"
    expires = (datetime.datetime.now()+DELTA).strftime(EXPIRATION_MASK)

    response = HttpResponse(myImage, content_type='image/png')
    response['Content-Disposition'] = 'filename=\"' + imageFileName + '\"'
    response['Expires'] = expires
    response['Cache-Control'] = "public, max-age=" + str(DELTA_SECONDS)
    return response

def galaxyParameterImage(request, galaxy_id, name):
    imageDirName = DJANGO_IMAGE_DIR

    connection = ENGINE.connect()
    galaxy_id = int(galaxy_id)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()

    imageFileName = '{0}_{1}_{2}.png'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number], name)
    filename = directory_mod.get_file_path(imageDirName, imageFileName, False)
    connection.close()

    sizeBytes = os.path.getsize(filename)
    file = open(filename, "rb")
    myImage = file.read(sizeBytes)
    file.close()

    DELTA = datetime.timedelta(minutes=10)
    DELTA_SECONDS = DELTA.days * 86400 + DELTA.seconds
    EXPIRATION_MASK = "%a, %d %b %Y %H:%M:%S %Z"
    expires = (datetime.datetime.now()+DELTA).strftime(EXPIRATION_MASK)

    response = HttpResponse(myImage, content_type='image/png')
    response['Content-Disposition'] = 'filename=\"' + imageFileName + '\"'
    response['Expires'] = expires
    response['Cache-Control'] = "public, max-age=" + str(DELTA_SECONDS)
    return response

def user_galaxies(connection, userid):
    """
    Determines the galaxies that the selected user has generated results.  Returns an array of
    galaxy_ids.
    """
    return connection.execute(select([GALAXY], from_obj= GALAXY.join(AREA).join(AREA_USER)).distinct().where(AREA_USER.c.userid == userid).order_by(GALAXY.c.image_time.desc(), GALAXY.c.name, GALAXY.c.version_number))
