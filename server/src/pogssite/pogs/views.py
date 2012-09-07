from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext, Context, loader
from config import django_image_dir
from image import fitsimage
from sqlalchemy.orm import sessionmaker
from django.db import connection
from pogs.models import Galaxy
from pogs import PogsSession
from database import database_support
import os, io, datetime, tempfile

class GalaxyLine:
    name1 = ""
    name2 = ""
    name3 = ""
    name4 = ""
    name5 = ""
    name6 = ""
    id1 = ""
    id2 = ""
    id3 = ""
    id4 = ""
    id5 = ""
    id6 = ""
    redshift1 = ""
    redshift2 = ""
    redshift3 = ""
    redshift4 = ""
    redshift5 = ""
    redshift6 = ""
    width1 = 100
    width2 = 100
    width3 = 100
    width4 = 100
    width5 = 100
    width6 = 100
    height1 = 100
    height2 = 100
    height3 = 100
    height4 = 100
    height5 = 100
    height6 = 100
    
class GalaxyInfo:
    galaxy_id = 0
    name = ""
    ra_cent = 0.0
    dec_cent = 0.0
    galaxy_type = ""
    redshift = 0
    pct_complete = "0.00%"
    
def getReferer(request):
    try:
        referer = request.META['HTTP_REFERER']
    except KeyError as e:
        referer = None
        
    if referer == '' or referer == None:
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
    except KeyError as e:
        referer = None
    if referer == '' or referer == None:
        referer = 'pogs'
    return referer;

def setReferrer(response, referer):
    response.set_cookie('pogs_referer', referer)

def userGalaxies(request, userid):
    session = PogsSession()
    image = fitsimage.FitsImage()

    user_galaxy_list = []
    idx = 0
    galaxy_line = GalaxyLine()
    for galaxy in image.userGalaxies(session, userid):
        name = galaxy.name
        if galaxy.version_number > 1:
            name = galaxy.name + "[" + str(galaxy.version_number) + "]"
        if idx == 0:
            galaxy_line = GalaxyLine()
            galaxy_line.name1 = name
            galaxy_line.id1 = galaxy.galaxy_id
            galaxy_line.redshift1 = str(galaxy.redshift)
            user_galaxy_list.append(galaxy_line)
            idx = 1
        elif idx == 1:
            galaxy_line.name2 = name
            galaxy_line.id2 = galaxy.galaxy_id
            galaxy_line.redshift2 = str(galaxy.redshift)
            idx = 2
        elif idx == 2:
            galaxy_line.name3 = name
            galaxy_line.id3 = galaxy.galaxy_id
            galaxy_line.redshift3 = str(galaxy.redshift)
            idx = 3
        elif idx == 3:
            galaxy_line.name4 = name
            galaxy_line.id4 = galaxy.galaxy_id
            galaxy_line.redshift4 = str(galaxy.redshift)
            idx = 4
        elif idx == 4:
            galaxy_line.name5 = name
            galaxy_line.id5 = galaxy.galaxy_id
            galaxy_line.redshift5 = str(galaxy.redshift)
            idx = 5
        elif idx == 5:
            galaxy_line.name6 = name
            galaxy_line.id6 = galaxy.galaxy_id
            galaxy_line.redshift6 = str(galaxy.redshift)
            idx = 0
    session.close()
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
    session = PogsSession()
    userid = int(userid)
    galaxy_id = int(galaxy_id)
    galaxy = session.query(database_support.Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=galaxy_id).first()
    galaxy_name = galaxy.name
    if galaxy.version_number > 1:
        galaxy_name = galaxy.name + "[" + str(galaxy.version_number) + "]"
    galaxy_height = galaxy.dimension_x;
    galaxy_width = galaxy.dimension_y;
    session.close()
    
    referer = getRefererFromCookie(request)
    
    t = loader.get_template('pogs/user_images.html')
    c = Context({
        'userid': userid,
        'galaxy_id': galaxy_id,
        'galaxy_name': galaxy_name,
        'galaxy_width': galaxy_width,
        'galaxy_height': galaxy_height,
        'referer':          referer,
    })
    return HttpResponse(t.render(c))

def userGalaxyImage(request, userid, galaxy_id, colour):
    tmp = tempfile.mkstemp(".png", "pogs", None, False)
    file = tmp[0]
    os.close(file)

    imageDirName = django_image_dir

    outImageFileName = tmp[1]

    session = PogsSession()
    userid = int(userid)
    galaxy_id = int(galaxy_id)
    galaxy = session.query(database_support.Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=galaxy_id).first()
    imagePrefixName = galaxy.name + "_" + str(galaxy.version_number)

    image = fitsimage.FitsImage()
    inImageFileName = image.get_colour_image_path(imageDirName, imagePrefixName, colour, False)
    image.markImage(session, inImageFileName, outImageFileName, galaxy_id, userid)
    session.close()

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
    session = PogsSession()
    galaxy_id = int(galaxy_id)
    galaxy = session.query(database_support.Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=galaxy_id).first()
    galaxy_name = galaxy.name
    if galaxy.version_number > 1:
        galaxy_name = galaxy.name + "[" + str(galaxy.version_number) + "]"
    galaxy_height = galaxy.dimension_x;
    galaxy_width = galaxy.dimension_y;
    session.close()
    
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
    except KeyError as e:
        page = 1
    try:
        type = request.GET["type"]
    except KeyError as e:
        type = ""
    try:
        name = request.GET["name"].upper()
    except KeyError as e:
        name = ""
    try:
        ra_from = request.GET["ra_from"]
    except KeyError as e:
        ra_from= ""
    try:
        ra_to = request.GET["ra_to"]
    except KeyError as e:
        ra_to = ""
    try:
        dec_from = request.GET["dec_from"]
    except KeyError as e:
        dec_from = ""
    try:
        dec_to = request.GET["dec_to"]
    except KeyError as e:
        dec_to = ""
    try:
        sort = request.GET["sort"]
    except KeyError as e:
        sort = "NAME"
    try:
        per_page = request.GET["per_page"]
    except KeyError as e:
        per_page = "50"
    
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
    session = PogsSession()
    query = session.query(database_support.Galaxy).filter("current=true");
    if type == "S":
        query = query.filter("galaxy_type like'S%' and galaxy_type not like'SB%' and galaxy_type not like'S0%'")
    elif type == "SB":
        query = query.filter("galaxy_type like'SB%'")
    elif type == "L":
        query = query.filter("galaxy_type like'S0%'")
    elif type == "E":
        query = query.filter("galaxy_type like'E%'")
    elif type == "I":
        query = query.filter("galaxy_type like'I%'")
        
    if name != "":
        query = query.filter("name like'" + name + "%'")
        
    if ra_from != "" and ra_to != "":
        query = query.filter("ra_cent between " + str(float(ra_from)) + " and " + str(float(ra_to)));
    elif ra_from != "":
        query = query.filter("ra_cent >= " + str(float(ra_from)));
    elif ra_to != "":
        query = query.filter("ra_cent <= " + str(float(ra_to)));
    
    if dec_from != "" and dec_to != "":
        query = query.filter("dec_cent between " + str(float(dec_from)) + " and " + str(float(dec_to)));
    elif dec_from != "":
        query = query.filter("dec_cent >= " + str(float(dec_from)));
    elif dec_to != "":
        query = query.filter("dec_cent <= " + str(float(dec_to)));
        
    if sort == "NAME":
        query = query.order_by(database_support.Galaxy.name, database_support.Galaxy.version_number)
    elif sort == "RADEC":
        query = query.order_by(database_support.Galaxy.ra_cent, database_support.Galaxy.dec_cent)
    elif sort == "TYPE":
        query = query.order_by(database_support.Galaxy.galaxy_type)
        query = query.order_by(database_support.Galaxy.name, database_support.Galaxy.version_number)
    elif sort == "USED":
        query = query.order_by(database_support.Galaxy.name, database_support.Galaxy.version_number)
    else:
        query = query.order_by(database_support.Galaxy.name, database_support.Galaxy.version_number)
    galaxies = query.all()
    galaxy_list = []
    count = 0
    galaxy_line = None
    for galaxy in galaxies:
        count += 1
        #name = galaxy.name
        #if galaxy.version_number > 1:
        #    name = galaxy.name + "[" + str(galaxy.version_number) + "]"
        if count < start:
            pass
        elif len(galaxy_list) >= lines_per_page:
            next_page = page + 1
            break
        else:
            line = GalaxyInfo();
            line.name = galaxy.name
            line.galaxy_id = galaxy.galaxy_id
            line.ra_cent = galaxy.ra_cent
            line.dec_cent = galaxy.dec_cent
            line.redshift = galaxy.redshift
            line.galaxy_type = galaxy.galaxy_type
            if galaxy.pixel_count == None or galaxy.pixels_processed == None or galaxy.pixel_count == 0:
                line.pct_complete = "0.00%"
            else:
                line.pct_complete = "{:.2%}".format(galaxy.pixels_processed/galaxy.pixel_count)
            galaxy_list.append(line)
    session.close()
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
    imageDirName = django_image_dir

    session = PogsSession()
    galaxy_id = int(galaxy_id)
    galaxy = session.query(database_support.Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=galaxy_id).first()

    image = fitsimage.FitsImage()
    imagePrefixName = '{0}_{1}'.format(galaxy.name, galaxy.version_number);
    imageFileName = image.get_colour_image_path(imageDirName, imagePrefixName, colour, False)
    session.close()

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
    imageDirName = django_image_dir

    session = PogsSession()
    galaxy_id = int(galaxy_id)
    galaxy = session.query(database_support.Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=galaxy_id).first()

    image = fitsimage.FitsImage()
    imagePrefixName = '{0}_{1}'.format(galaxy.name, galaxy.version_number);
    imageFileName = image.get_thumbnail_colour_image_path(imageDirName, imagePrefixName, colour, False)
    session.close()

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
    imageDirName = django_image_dir

    session = PogsSession()
    galaxy_id = int(galaxy_id)
    galaxy = session.query(database_support.Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=galaxy_id).first()

    image = fitsimage.FitsImage()
    imageFileName = '{0}_{1}_{2}.png'.format(galaxy.name, galaxy.version_number, name);
    filename = image.get_file_path(imageDirName, imageFileName, False)
    session.close()

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
