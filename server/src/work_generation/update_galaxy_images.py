#! /usr/bin/env python2.7
"""
Update all the images from the fits image
"""

import os
import logging
from database.database_support import Galaxy
from image.fitsimage import FitsImage
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import DB_LOGIN, WG_IMAGE_DIRECTORY


LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

engine = create_engine(DB_LOGIN)
Session = sessionmaker(bind=engine)

session = Session()
image = FitsImage()

for galaxy in session.query(Galaxy).order_by(Galaxy.name).all():
    filePrefixName = galaxy.name + "_" + str(galaxy.version_number)
    fitsFileName = filePrefixName + ".fits"

    LOG.info('Processing %s (%d)', galaxy.name, galaxy.version_number)
    INPUT_FILE = image.get_file_path(WG_IMAGE_DIRECTORY, fitsFileName, False)
    if os.path.isfile(INPUT_FILE):
        image.buildImage(INPUT_FILE, WG_IMAGE_DIRECTORY, filePrefixName, 'asinh', False, False, False, session, galaxy.galaxy_id)

session.commit()
