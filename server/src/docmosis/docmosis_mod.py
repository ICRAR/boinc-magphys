#! /usr/bin/env python2.7
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
import urllib2
import base64
import datetime
import os
import tempfile
import warnings

from sqlalchemy import *
from config import WG_BOINC_PROJECT_ROOT,DJANGO_IMAGE_DIR, DJANGO_DOCMOSIS_KEY, DJANGO_DOCMOSIS_TEMPLATE, DB_LOGIN
from image import fitsimage, directory_mod
from database.database_support_core import GALAXY,IMAGE_FILTERS_USED,FILTER
from astropy.io.vo.table import parse
from docmosis import votable_mod

# TODO - Look at using direct MySQL connection
os.environ.setdefault("BOINC_PROJECT_DIR", WG_BOINC_PROJECT_ROOT)
from Boinc import database

ENGINE = create_engine(DB_LOGIN)

def emailGalaxyReport(userid,galaxy_ids):
    # Docmosis specific variables
    rendURL='https://dws.docmosis.com/services/rs/render'

    user = userDetails(userid)
    galaxies = galaxyDetails(galaxy_ids)

    data = dataString(user,galaxies)

    request = urllib2.Request(rendURL,data)
    request.add_header('Content-Type','application/json; charset=UTF-8')
    response = urllib2.urlopen(request)

class UserInfo:
    def __init__(self):
        self.id = ""
        self.name = ""
        self.email = ""

class GalaxyInfo:
    """
    Galaxy information
    """
    def __init__(self):
        self.galaxy_id = 0
        self.galaxy_type = ""
        self.redshift = 0.0
        self.name = ""
        self.version = 0
        self.design = ""
        self.ra_eqj2000 = 0
        self.dec_eqj2000 = 0
        self.ra_eqb1950 = 0
        self.dec_eqb1950 = 0
        self.pos1 = ""
        self.pos2 = ""

def dataString(user,galaxies):
    hasParam = 1
    # Prep. data for send to Osmosis
    dl = []
    dl.append('{\n')
    dl.append('"accessKey":"' + DJANGO_DOCMOSIS_KEY + '",\n')
    dl.append('"templateName":"' + DJANGO_DOCMOSIS_TEMPLATE + '",\n')
    dl.append('"outputName":"DetailedUserReport.pdf",\n')
    dl.append('"storeTo":"mailto:' + user.email + '",\n')
    dl.append('"mailSubject":"theSkyNet POGS - Detailed User Report",\n')
    dl.append('"data":{\n')
    dl.append('"user":"' + user.name + '",\n')
    dl.append('"date":"' + str(datetime.date.today()) +'",\n')
    dl.append('"galaxy":[\n')
    # Loop through galaxies user has worked on.
    for galaxy in galaxies:
        dl.append('{\n')
        dl.append('"galid":"' + galaxy.name + '",\n')
        dl.append('"pic1":"image:base64:' + userGalaxyImage(user.id,galaxy.galaxy_id,1) + '",\n')
        dl.append('"pic2":"image:base64:' + userGalaxyImage(user.id,galaxy.galaxy_id,2) + '",\n')
        dl.append('"pic3":"image:base64:' + userGalaxyImage(user.id,galaxy.galaxy_id,3) + '",\n')
        dl.append('"pic4":"image:base64:' + userGalaxyImage(user.id,galaxy.galaxy_id,4) + '",\n')
        dl.append('"pic1_label":"' + galaxyFilterLabel(galaxy.galaxy_id,1) + '",\n') 
        dl.append('"pic2_label":"' + galaxyFilterLabel(galaxy.galaxy_id,2) + '",\n') 
        dl.append('"pic3_label":"' + galaxyFilterLabel(galaxy.galaxy_id,3) + '",\n') 
        dl.append('"pic4_label":"' + galaxyFilterLabel(galaxy.galaxy_id,4) + '",\n') 
        # Only if there is paramater images
        if hasParam:
            dl.append('"add":"true",\n')
            dl.append('"pic5":"image:base64:' + galaxyParameterImage(galaxy.galaxy_id,'mu') + '",\n')
            dl.append('"pic6":"image:base64:' + galaxyParameterImage(galaxy.galaxy_id,'m') + '",\n')
            dl.append('"pic7":"image:base64:' + galaxyParameterImage(galaxy.galaxy_id,'ldust') + '",\n')
            dl.append('"pic8":"image:base64:' + galaxyParameterImage(galaxy.galaxy_id,'sfr') + '",\n')
        dl.append('"gatype":"' + galaxy.galaxy_type + '",\n')
        dl.append('"gars":"' + str(galaxy.redshift) + '",\n')
        dl.append('"gades":"' + galaxy.design + '",\n')
        dl.append('"gara_eqj2000":"' + str(galaxy.ra_eqj2000) + '",\n')
        dl.append('"gadec_eqj2000":"' + str(galaxy.dec_eqj2000) + '",\n')
        dl.append('"gara_eqb1950":"' + str(galaxy.ra_eqb1950) + '",\n')
        dl.append('"gadec_eqb1950":"' + str(galaxy.dec_eqb1950) + '",\n')
        dl.append('},\n')
    dl.append(']\n')
    dl.append('}\n')
    dl.append('}\n')

    data = ''.join(dl)

    return data

def galaxyDetails(galaxy_ids):
    """
    Return list of galaxies with detailed data
    """

    connection = ENGINE.connect()
    query = select([GALAXY])
    query = query.where(GALAXY.c.galaxy_id.in_([str(id) for id in galaxy_ids]))
    galaxies = connection.execute(query)

    galaxy_list = []
    for galaxy in galaxies:
        vomap = votable_mod.getVOData(getCorrectedName(galaxy.name))
        galaxy_line = GalaxyInfo()
        galaxy_line.name = galaxy.name
        galaxy_line.design = vomap['design']
        galaxy_line.ra_eqj2000 = vomap['ra_eqj2000']
        galaxy_line.dec_eqj2000 = vomap['dec_eqj2000']
        galaxy_line.ra_eqb1950 = vomap['ra_eqb1950']
        galaxy_line.dec_eqb1950 = vomap['dec_eqb1950']
        galaxy_line.version = galaxy.version_number
        galaxy_line.galaxy_type = galaxy.galaxy_type
        galaxy_line.galaxy_id = galaxy.galaxy_id
        galaxy_line.redshift = galaxy.redshift
        galaxy_list.append(galaxy_line)
    connection.close()

    return galaxy_list


def galaxyParameterImage(galaxy_id, name):
    """
    Returns base64 string version of galaxy image
    """

    imageDirName = DJANGO_IMAGE_DIR

    connection = ENGINE.connect()
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

    connection = ENGINE.connect()
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

    url='http://leda.univ-lyon1.fr/G.cgi?n=101&c=o&o=' + name + '&a=x&z=d'
    table = parseVOTable(url)
    i = 0
    for design in table.array['design']:
        if i:
            galaxy_line.design += ', '
        galaxy_line.design += design
        i += 1

    url='http://leda.univ-lyon1.fr/G.cgi?n=113&c=o&o=' + name + '&a=x&z=d'
    table = parseVOTable(url)

    galaxy_line.ra_eqj2000 = table.array['alpha'][0]
    galaxy_line.dec_eqj2000 = table.array['delta'][0]


    return galaxy_line

def galaxyFilterLabel(galaxy_id,colour):
   """
   Return filters string for given galaxy and colour
   """
   connection = ENGINE.connect()
   map_fl = {}
   for filter in connection.execute(select([FILTER])):
      map_fl[filter.filter_id] = filter.label
   query = select([IMAGE_FILTERS_USED])
   query = query.where(and_(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id,IMAGE_FILTERS_USED.c.image_number == colour))
   image = connection.execute(query).first()
   fstr = map_fl[image.filter_id_red]
   fstr = fstr + ", " + map_fl[image.filter_id_green]
   fstr = fstr + ", " + map_fl[image.filter_id_blue]
   connection.close()

   return fstr


def parseVOTable(url):
    """
    Takes parsed URL and gets first table in VOTable
    formatted response
    """

    tmp = tempfile.mkstemp(".xml", "pogs", None, False)
    file = tmp[0]
    os.close(file)

    outXMLFileName = tmp[1]

    try:
        request = urllib2.Request(url)
        response = urllib2.urlopen(request,timeout=10)
        with open(outXMLFileName, 'w') as file:
            file.write(response.read())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            votable = parse(outXMLFileName)
        table = votable.get_first_table()
    except:
        os.remove(outXMLFileName)
        raise Exception("VOTable provider error")

    os.remove(outXMLFileName)

    return table

def userDetails(userid):
    """
    Fill user details from BOINC database
    """
    user_line = UserInfo()
    user_line.id = userid
    database.connect()
    user = database.Users.find(id=userid)[0]
    user_line.name = user.name
    user_line.email = user.email_addr
    database.close()

    return user_line

def getCorrectedName(name):
    """
    Get the corrected name
    """
    if name[-1:].islower():
        return name[:-1]
    
    return name
