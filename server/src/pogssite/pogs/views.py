from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.http import HttpResponse
from django.template import Context, loader
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
    id1 = ""
    id2 = ""
    id3 = ""
    id4 = ""
    redshift1 = ""
    redshift2 = ""
    redshift3 = ""
    redshift4 = ""

def userGalaxies(request, userid):
    session = PogsSession()
    image = fitsimage.FitsImage()

    user_galaxy_list = []
    idx = 0
    galaxy_line = GalaxyLine()
    for galaxy in image.userGalaxies(session, userid):
        if idx == 0:
            galaxy_line = GalaxyLine()
            galaxy_line.name1 = galaxy.name
            galaxy_line.id1 = galaxy.galaxy_id
            galaxy_line.redshift1 = str(galaxy.redshift)
            user_galaxy_list.append(galaxy_line)
            idx = 1
        elif idx == 1:
            galaxy_line.name2 = galaxy.name
            galaxy_line.id2 = galaxy.galaxy_id
            galaxy_line.redshift2 = str(galaxy.redshift)
            idx = 2
        elif idx == 2:
            galaxy_line.name3 = galaxy.name
            galaxy_line.id3 = galaxy.galaxy_id
            galaxy_line.redshift3 = str(galaxy.redshift)
            idx = 3
        elif idx == 3:
            galaxy_line.name4 = galaxy.name
            galaxy_line.id4 = galaxy.galaxy_id
            galaxy_line.redshift4 = str(galaxy.redshift)
            idx = 0
    session.close()

    t = loader.get_template('pogs/index.html')
    c = Context({
        'user_galaxy_list': user_galaxy_list,
        'userid':           userid,
    })
    return HttpResponse(t.render(c))

def userGalaxy(request, userid, galaxy_id):
    session = PogsSession()
    userid = int(userid)
    galaxy_id = int(galaxy_id)
    galaxy = session.query(database_support.Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=galaxy_id).first()
    galaxy_name = galaxy.name
    galaxy_height = galaxy.dimension_x;
    galaxy_width = galaxy.dimension_y;
    session.close()
    
    t = loader.get_template('pogs/user_images.html')
    c = Context({
        'userid': userid,
        'galaxy_id': galaxy_id,
        'galaxy_name': galaxy_name,
        'galaxy_width': galaxy_width,
        'galaxy_height': galaxy_height,
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

def userFitsImage(request, userid, galaxy_id, name):
    imageDirName = django_image_dir

    session = PogsSession()
    userid = int(userid)
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








