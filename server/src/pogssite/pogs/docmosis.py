import urllib2
import base64
import datetime
import os
import tempfile
import warnings
import MySQLdb as mdb

# Temporary until web deployed
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pogssite.settings")
#from django.http import HttpResponse, HttpResponseRedirect
#from django.template import Context, loader

from sqlalchemy.sql.expression import select, and_, not_
from config import DJANGO_IMAGE_DIR
from image import fitsimage, directory_mod
#from pogs.models import Galaxy
from pogs import pogs_engine
from database.database_support_core import AREA, AREA_USER, GALAXY
from astropy.io.vo.table import parse


def generateReport(userid):
    # Docmosis specific variables
    rendURL='https://dws.docmosis.com/services/rs/render'
    accessKey='MWJjODk3YWYtYjBjMi00NTAzLTgxNzAtMmYwNWQ0NDBhNjRjOjMwMTcyNjA'
    template='Report.doc'

    output = 'Report.pdf'

    hasParam=1
    user = userDetails(userid)

    galaxies = []
    galaxies = userGalaxies(userid)

    # Prep. data for send to Osmosis
    dl = []
    dl.append('{\n')
    dl.append('"accessKey":"' + accessKey + '",\n')
    dl.append('"templateName":"' + template + '",\n')
    dl.append('"outputName":"' + os.path.basename(output) + '",\n')
    dl.append('"storeTo":"mailto:' + user.email + '",\n')
    dl.append('"mailSubject":"theSkyNet POGS - Detailed User Report",\n')
    dl.append('"data":{\n');
    dl.append('"user":"' + user.name + '",\n')
    dl.append('"date":"' + str(datetime.date.today()) +'",\n')
    dl.append('"galaxy":[\n')
    # Loop through galaxies user has worked on.
    for galaxy in galaxies:
        dl.append('{\n')
        dl.append('"galid":"' + galaxy.name + '",\n') 
        dl.append('"pic1":"image:base64:' + userGalaxyImage(userid,galaxy.galaxy_id,'1') + '",\n')
        dl.append('"pic2":"image:base64:' + userGalaxyImage(userid,galaxy.galaxy_id,'2') + '",\n')
        dl.append('"pic3":"image:base64:' + userGalaxyImage(userid,galaxy.galaxy_id,'3') + '",\n')
        dl.append('"pic4":"image:base64:' + userGalaxyImage(userid,galaxy.galaxy_id,'4') + '",\n')
        # Only if there is paramater images
        if(hasParam):
            dl.append('"add":"true",\n')
            dl.append('"pic5":"image:base64:' + galaxyParameterImage(galaxy.galaxy_id,'mu') + '",\n')
            dl.append('"pic6":"image:base64:' + galaxyParameterImage(galaxy.galaxy_id,'m') + '",\n')
            dl.append('"pic7":"image:base64:' + galaxyParameterImage(galaxy.galaxy_id,'ldust') + '",\n')
            dl.append('"pic8":"image:base64:' + galaxyParameterImage(galaxy.galaxy_id,'sfr') + '",\n')
        dl.append('"gatype":"' + galaxy.galaxy_type + '",\n')
        dl.append('"gades":"' + galaxy.design + '",\n')
        dl.append('"gars":"' + str(galaxy.redshift) + '",\n')
        dl.append('"gara":"' + str(galaxy.ra) + '",\n')
        dl.append('"gadec":"' + str(galaxy.dec) + '",\n')
        dl.append('"gapos1":"' + str(galaxy.pos1) + '",\n')
        dl.append('"gapos2":"' + str(galaxy.pos2) + '",\n')
        dl.append('},\n')
    dl.append(']\n')
    dl.append('}\n')
    dl.append('}\n')

    data = ''.join(dl)

    request = urllib2.Request(rendURL,data)
    request.add_header('Content-Type','application/json; charset=UTF-8')
    response = urllib2.urlopen(request)
    
class UserInfo:
    def __init__(self):
        self.name = ""
        self.email = ""

class GalaxyInfo:
    """
    Galaxy information
    """
    def __init__(self):
        self.galaxy_id = 0
        self.galaxy_type = ""
        self.name = ""
        self.design = ""
        self.ra = 0
        self.dec = 0
        self.pos1 = ""
        self.pos2 = ""

def userGalaxies(userid):
    """
    Return list of galaxies that have been processed by user
    """

    pogs_connection = pogs_engine.connect()
    user_galaxy_list = []
    galaxy_line = GalaxyInfo()
    for galaxy in user_galaxies(pogs_connection, userid):
        name = galaxy.name
        if galaxy.version_number > 1:
            name = galaxy.name + "[" + str(galaxy.version_number) + "]"
        # Map some external data first
        galaxy_line = galaxyExternalData(name)
        galaxy_line.name = name
        galaxy_line.galaxy_type = galaxy.galaxy_type
        galaxy_line.galaxy_id = galaxy.galaxy_id
        galaxy_line.redshift = galaxy.redshift
        user_galaxy_list.append(galaxy_line)
    pogs_connection.close()

    return user_galaxy_list
    

def galaxyParameterImage(galaxy_id, name):
    """
    Returns base64 string version of galaxy image
    """

    imageDirName = DJANGO_IMAGE_DIR

    connection = pogs_engine.connect()
    galaxy_id = int(galaxy_id)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()

    imageFileName = '{0}_{1}_{2}.png'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number], name)
    filename = directory_mod.get_file_path(imageDirName, imageFileName, False)
    connection.close()

    file = open(filename, "rb")
    image64 = base64.b64encode(file.read())
    file.close()

    return image64

def userGalaxyImage(userid, galaxy_id, colour):
    """
    Returns base64 string version of galaxy image
    """

    tmp = tempfile.mkstemp(".png", "pogs", None, False)
    file = tmp[0]
    os.close(file)

    imageDirName = DJANGO_IMAGE_DIR

    outImageFileName = tmp[1]

    connection = pogs_engine.connect()
    userid = int(userid)
    galaxy_id = int(galaxy_id)
    galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()
    imagePrefixName = galaxy[GALAXY.c.name] + "_" + str(galaxy[GALAXY.c.version_number])

    image = fitsimage.FitsImage(connection)
    inImageFileName = directory_mod.get_colour_image_path(imageDirName, imagePrefixName, colour, False)
    image.markImage(inImageFileName, outImageFileName, galaxy_id, userid)
    connection.close()

    file = open(outImageFileName, "rb")
    image64 = base64.b64encode(file.read())
    file.close()
    os.remove(outImageFileName)

    return image64

def galaxyExternalData(name):
    """    
    Retrieve specific galaxy data from third party.
    """
    
    galaxy_line = GalaxyInfo()

    url='http://leda.univ-lyon1.fr/G.cgi?n=101&c=o&o=' + name[:-1] + '&a=x&z=d'
    table = parseVOTable(url)
    i = 0
    for design in table.array['design']:
        if i:
            galaxy_line.design += ', '
        galaxy_line.design += design
        i += 1


    url='http://leda.univ-lyon1.fr/G.cgi?n=113&c=o&o=' + name[:-1] + '&a=x&z=d'
    table = parseVOTable(url)
    galaxy_line.ra = table.array['alpha'][0]
    galaxy_line.dec = table.array['delta'][0]
    galaxy_line.pos1 = table.array['radec1950'][0]
    galaxy_line.pos2 = table.array['radec2000'][0]
    

    return galaxy_line

def parseVOTable(url):
    """
    Takes parsed URL and gets first table in VOTable
    formatted response
    """

    tmp = tempfile.mkstemp(".xml", "pogs", None, False)
    file = tmp[0]
    os.close(file)

    outXMLFileName = tmp[1]

    response = urllib2.urlopen(url)
    with open(outXMLFileName, 'w') as file:
        file.write(response.read())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        votable = parse(outXMLFileName)
    table = votable.get_first_table()

    os.remove(outXMLFileName)

    return table
    
def user_galaxies(connection, userid):
    """
    Determines the galaxies that the selected user has generated results.  Returns an array of
    galaxy_ids.
    """
    return connection.execute(select([GALAXY], from_obj= GALAXY.join(AREA).join(AREA_USER)).distinct().where(AREA_USER.c.userid == userid).order_by(GALAXY.c.image_time.desc(), GALAXY.c.name, GALAXY.c.version_number))

def userDetails(userid):
    """
    Return user name based on user id. 

    This method is temporary until Python BOINC database framework works.
    """

    user_line = UserInfo()
    connection = mdb.connect('localhost', 'root', '', 'pogs1'); 
    cursor = connection.cursor()
    cursor.execute("SELECT name,email_addr FROM user WHERE id=" + str(userid))
    connection.close()
    row = cursor.fetchone()
    user_line.name = row[0]
    user_line.email = row[1]

    return user_line
