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

def userGalaxies(request, userid):
    session = PogsSession()
    image = fitsimage.FitsImage()

    user_galaxy_list = []
    for galaxy in image.userGalaxies(session, userid):
       user_galaxy_list.append(galaxy)
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
    imagePrefixName = galaxy.name

    image = fitsimage.FitsImage()
    inImageFileName = image.get_colour_image_path(imageDirName, imagePrefixName, colour, false)
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
    filename = image.get_file_path(imageDirName, imageFileName, false)
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








