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
Update all the images from the fits image
"""

import os
import logging
import time
from image.fitsimage import FitsImage
from sqlalchemy import create_engine
from config import DB_LOGIN, WG_IMAGE_DIRECTORY


LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

engine = create_engine(DB_LOGIN)
connection =  engine.connect()
transaction = connection.begin()
image = FitsImage(connection)

for galaxy in session.query(Galaxy).order_by(Galaxy.name).all():
    transaction = connection.begin()
    start = time.time()
    filePrefixName = galaxy.name + "_" + str(galaxy.version_number)
    fitsFileName = filePrefixName + ".fits"

    LOG.info('Processing %s (%d)', galaxy.name, galaxy.version_number)
    input_file = image.get_file_path(WG_IMAGE_DIRECTORY, fitsFileName, False)
    if os.path.isfile(input_file):
        image.buildImage(input_file, WG_IMAGE_DIRECTORY, filePrefixName, False, galaxy.galaxy_id)

    end = time.time()
    LOG.info("Images generated in %.2f seconds", end - start)

    transaction.commit()
