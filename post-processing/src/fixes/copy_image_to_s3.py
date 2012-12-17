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
"""
Copy the images from the shared store to S3
"""
import logging
import boto
from boto.s3.key import Key

from sqlalchemy import create_engine, select
from config import DB_LOGIN, WG_IMAGE_DIRECTORY
from database.database_support_core import GALAXY
from image import directory_mod

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

# This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
s3_connection = boto.connect_s3()
bucket = s3_connection.get_bucket('boinc.theskynet.org-galaxy_images')

def copy_file(file_name):
    key = Key(bucket)
    key.key = file_name
    key.set_contents_from_filename(file_name)

for galaxy in connection.execute(select([GALAXY])):
    LOG.info('Processing %d - %s', galaxy[GALAXY.c.galaxy_id], galaxy[GALAXY.c.name])

    file_prefix_name = galaxy[GALAXY.c.name] + "_" + str(galaxy[GALAXY.c.version_number])
    for i in [1, 2, 3, 4]:
        file_name = directory_mod.get_colour_image_path(WG_IMAGE_DIRECTORY, file_prefix_name, i, False)
        copy_file(file_name)

        file_name = directory_mod.get_thumbnail_colour_image_path(WG_IMAGE_DIRECTORY, file_prefix_name, i, False)
        copy_file(file_name)

    fits_file_name = directory_mod.get_file_path(WG_IMAGE_DIRECTORY, file_prefix_name + '.fits', False)
    copy_file(fits_file_name)
