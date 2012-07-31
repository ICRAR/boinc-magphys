from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.http import HttpResponse
from django.template import Context, loader
from image import fitsimage
from sqlalchemy.orm import sessionmaker
from django.db import connection
from pogs.models import Galaxy
from pogs import PogsSession
from database import database_support
import os, io, datetime, tempfile


def galaxiesx(request):
    #Session = sessionmaker()
    #session = Session(bind=connection)
    #image = fitsimage.FitsImage()
    #user_galaxy_list = image.userGalaxies(session, 2);
    # 
    #t = loader.get_template('pogs/index.html')
    #c = Context({
    #    'user_galaxy_list': user_galaxy_list,
    #})
    #return HttpResponse(t.render(c))
    
    user_galaxy_list = Galaxy.objects.all();
    return render_to_response('pogs/index.html', {'user_galaxy_list': user_galaxy_list})

def userGalaxies(request, userid):
    session = PogsSession();
    image = fitsimage.FitsImage();
    
    user_galaxy_list = []
    for galaxy in image.userGalaxies(session, userid):
       user_galaxy_list.append(galaxy)
    
    t = loader.get_template('pogs/index.html');
    c = Context({
        'user_galaxy_list': user_galaxy_list,
        'userid':           userid,
    })
    return HttpResponse(t.render(c));

def userGalaxy(request, userid, galaxy_id):
    t = loader.get_template('pogs/user_images.html')
    c = Context({
        'userid': userid,
        'galaxy_id': galaxy_id,
    })
    return HttpResponse(t.render(c));

def userGalaxyImage(request, userid, galaxy_id, colour):
    tmp = tempfile.mkstemp(".png", "pogs", None, False);
    file = tmp[0];
    os.close(file);
    
    #imageDirName = "/Users/rob/magphys/POGS_NGC1209";
    imageDirName = "/home/ec2-user/galaxyImages";
    
    outImageFileName = tmp[1];
    
    session = PogsSession();
    userid = int(userid)
    galaxy_id = int(galaxy_id);
    galaxy = session.query(database_support.Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=galaxy_id).first()
    imagePrefixName = galaxy.name;
    
    image = fitsimage.FitsImage();
    inImageFileName = image.get_colour_image_path(imageDirName, imagePrefixName, colour);
    image.markImage(session, inImageFileName, outImageFileName, galaxy_id, userid);
    
    sizeBytes = os.path.getsize(outImageFileName);
    file = open(outImageFileName, "rb");
    myImage = file.read(sizeBytes);
    file.close();
    os.remove(outImageFileName);
    
    DELTA = datetime.timedelta(minutes=10);
    DELTA_SECONDS = DELTA.days * 86400 + DELTA.seconds;
    EXPIRATION_MASK = "%a, %d %b %Y %H:%M:%S %Z";
    expires = (datetime.datetime.now()+DELTA).strftime(EXPIRATION_MASK)
    
    response = HttpResponse(myImage, content_type='image/png');
    response['Content-Disposition'] = 'filename=\"' + imagePrefixName + '_' + colour + '.png\"'
    response['Expires'] = expires;
    response['Cache-Control'] = "public, max-age=" + str(DELTA_SECONDS);
    return response;







