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
import logging
from utils.name_builder import get_galaxy_image_bucket, get_build_png_name, get_galaxy_file_name, get_colour_image_key
from utils.s3_helper import get_bucket, get_s3_connection, get_file_from_bucket
import votable_mod

from sqlalchemy import *
from config import WG_BOINC_PROJECT_ROOT, DOCMOSIS_KEY, DOCMOSIS_TEMPLATE, DB_LOGIN
from image import fitsimage
from database.database_support_core import GALAXY, IMAGE_FILTERS_USED, FILTER

os.environ.setdefault("BOINC_PROJECT_DIR", WG_BOINC_PROJECT_ROOT)
from Boinc import database

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

ENGINE = create_engine(DB_LOGIN)


def email_galaxy_report(connection, userid, galaxy_ids):
    # Docmosis specific variables
    rendURL = 'https://dws.docmosis.com/services/rs/render'

    LOG.info("Retrieve user details")
    user = user_details(userid)
    LOG.info("Retrieve galaxy details")
    galaxies = galaxy_details(connection, galaxy_ids)
    LOG.info("Build JSON data payload")
    data = data_string(connection, user, galaxies)
    LOG.info("Send payload to Docmosis")
    request = urllib2.Request(rendURL, data)
    request.add_header('Content-Type', 'application/json; charset=UTF-8')
    urllib2.urlopen(request)


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
        self.design = ""
        self.ra_eqj2000 = 0
        self.dec_eqj2000 = 0
        self.ra_eqb1950 = 0
        self.dec_eqb1950 = 0
        self.pos1 = ""
        self.pos2 = ""
        self.run_id = 0


def data_string(connection, user, galaxies):
    s3_connection = get_s3_connection()
    bucket = get_bucket(s3_connection, get_galaxy_image_bucket())

    hasParam = 1
    # Prep. data for send to docsmosis
    dl = []
    dl.append('{\n')
    dl.append('"accessKey":"' + DOCMOSIS_KEY + '",\n')
    dl.append('"templateName":"' + DOCMOSIS_TEMPLATE + '",\n')
    dl.append('"outputName":"DetailedUserReport.pdf",\n')
    dl.append('"storeTo":"mailto:' + user.email + '",\n')
    dl.append('"mailSubject":"theSkyNet POGS - Detailed User Report",\n')
    dl.append('"data":{\n')
    dl.append('"user":"' + user.name + '",\n')
    dl.append('"date":"' + str(datetime.date.today()) + '",\n')
    dl.append('"galaxy":[\n')
    # Loop through galaxies user has worked on.
    for galaxy in galaxies:
        galaxy_key = get_galaxy_file_name(galaxy.name, galaxy.run_id, galaxy.galaxy_id)
        dl.append('{\n')
        dl.append('"galid":"' + galaxy.name + ' (version ' + str(galaxy.version_number) + ')",\n')
        dl.append('"pic1":"image:base64:' + user_galaxy_image(bucket, galaxy_key, connection, user.id, galaxy.galaxy_id, 1) + '",\n')
        dl.append('"pic2":"image:base64:' + user_galaxy_image(bucket, galaxy_key, connection, user.id, galaxy.galaxy_id, 2) + '",\n')
        dl.append('"pic3":"image:base64:' + user_galaxy_image(bucket, galaxy_key, connection, user.id, galaxy.galaxy_id, 3) + '",\n')
        dl.append('"pic4":"image:base64:' + user_galaxy_image(bucket, galaxy_key, connection, user.id, galaxy.galaxy_id, 4) + '",\n')
        dl.append('"pic1_label":"' + galaxy_filter_label(connection, galaxy.galaxy_id, 1) + '",\n')
        dl.append('"pic2_label":"' + galaxy_filter_label(connection, galaxy.galaxy_id, 2) + '",\n')
        dl.append('"pic3_label":"' + galaxy_filter_label(connection, galaxy.galaxy_id, 3) + '",\n')
        dl.append('"pic4_label":"' + galaxy_filter_label(connection, galaxy.galaxy_id, 4) + '",\n')
        # Only if there is parameter images
        if hasParam:
            dl.append('"add":"true",\n')
            dl.append('"pic5":"image:base64:' + galaxy_parameter_image(bucket, galaxy_key, 'mu') + '",\n')
            dl.append('"pic6":"image:base64:' + galaxy_parameter_image(bucket, galaxy_key, 'm') + '",\n')
            dl.append('"pic7":"image:base64:' + galaxy_parameter_image(bucket, galaxy_key, 'ldust') + '",\n')
            dl.append('"pic8":"image:base64:' + galaxy_parameter_image(bucket, galaxy_key, 'sfr') + '",\n')
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


def galaxy_details(connection, galaxy_ids):
    """
    Return list of galaxies with detailed data
    """
    query = select([GALAXY]).where(GALAXY.c.galaxy_id.in_([str(galaxy_id) for galaxy_id in galaxy_ids]))
    galaxies = connection.execute(query)

    galaxy_list = []
    for galaxy in galaxies:
        vomap = votable_mod.getVOData(get_corrected_name(galaxy.name))
        galaxy_line = GalaxyInfo()
        galaxy_line.name = galaxy[GALAXY.c.name]
        galaxy_line.design = vomap['design']
        galaxy_line.ra_eqj2000 = vomap['ra_eqj2000']
        galaxy_line.dec_eqj2000 = vomap['dec_eqj2000']
        galaxy_line.ra_eqb1950 = vomap['ra_eqb1950']
        galaxy_line.dec_eqb1950 = vomap['dec_eqb1950']
        galaxy_line.galaxy_type = galaxy[GALAXY.c.galaxy_type]
        galaxy_line.galaxy_id = galaxy[GALAXY.c.galaxy_id]
        galaxy_line.redshift = galaxy[GALAXY.c.redshift]
        galaxy_line.run_id = galaxy[GALAXY.c.run_id]
        galaxy_list.append(galaxy_line)

    return galaxy_list


def galaxy_parameter_image(bucket, galaxy_key, name):
    """
    Returns base64 string version of galaxy image
    """
    tmp_file = get_temp_file('.png')
    key = get_build_png_name(galaxy_key, name)
    get_file_from_bucket(bucket, key, tmp_file)

    out_file = open(tmp_file, "rb")
    image64 = base64.b64encode(out_file.read())
    out_file.close()

    os.remove(tmp_file)

    return image64


def get_temp_file(extension):
    """
    Get a temporary file
    """
    tmp = tempfile.mkstemp(extension, "pogs", None, False)
    tmp_file = tmp[0]
    os.close(tmp_file)
    return tmp[1]


def user_galaxy_image(bucket, galaxy_key, connection, userid, galaxy_id, colour):
    """
    Returns base64 string version of galaxy image
    """
    image_file_name = get_temp_file(".png")
    marked_image_file_name = get_temp_file(".png")

    key = get_colour_image_key(galaxy_key, colour)
    get_file_from_bucket(bucket, key, image_file_name)

    image = fitsimage.FitsImage(connection)
    image.mark_image(image_file_name, marked_image_file_name, galaxy_id, userid)

    out_file = open(marked_image_file_name, "rb")
    image64 = base64.b64encode(out_file.read())
    out_file.close()
    os.remove(marked_image_file_name)
    os.remove(image_file_name)

    return image64


def galaxy_filter_label(connection, galaxy_id, colour):
    """
    Return filters string for given galaxy and colour
    """
    map_fl = {}
    for filter_band in connection.execute(select([FILTER])):
        map_fl[filter_band.filter_id] = filter_band.label
    query = select([IMAGE_FILTERS_USED]).where(and_(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id, IMAGE_FILTERS_USED.c.image_number == colour))
    image = connection.execute(query).first()
    fstr = map_fl[image.filter_id_red]
    fstr = fstr + ", " + map_fl[image.filter_id_green]
    fstr = fstr + ", " + map_fl[image.filter_id_blue]

    return fstr


def user_details(userid):
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


def get_corrected_name(name):
    """
    Get the corrected name
    """
    if name[-1:].islower():
        return name[:-1]

    return name
