#! /usr/bin/env python2.7
"""
Register a galaxy in the database as waiting to be processed
"""
import argparse
import logging
import datetime
import shutil
import pyfits
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from config import db_login
from database.database_support import Galaxy
from image.fitsimage import FitsImage
from utils.writeable_dir import WriteableDir

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser()
parser.add_argument('FITS_file', nargs=1, help='the input FITS file containing the galaxy')
parser.add_argument('redshift', type=float, nargs=1, help='the redshift of the galaxy')
parser.add_argument('image_directory', action=WriteableDir, nargs=1, help='where the images will be written too')
parser.add_argument('galaxy_name', nargs=1, help='the name of the galaxy')
parser.add_argument('hubble_type', nargs=1, help='the hubble type')
args = vars(parser.parse_args())

REDSHIFT = args['redshift'][0]
INPUT_FILE = args['FITS_file'][0]
IMAGE_DIR = args['image_directory']
GALAXY_NAME = args['galaxy_name'][0]
GALAXY_TYPE = args['hubble_type'][0]

# Connect to the database - the login string is set in the database package
engine = create_engine(db_login)
Session = sessionmaker(bind=engine)
session = Session()

LOG.info("Registering %s", GALAXY_NAME)

version_number = session.query(Galaxy).filter(Galaxy.name == GALAXY_NAME).count()
version_number += 1

filePrefixName = "%s_%s" % (GALAXY_NAME, str(version_number))
fitsFileName = filePrefixName + ".fits"

HDULIST = pyfits.open(INPUT_FILE, memmap=True)
LAYER_COUNT = len(HDULIST)
END_Y = HDULIST[0].data.shape[0]
END_X = HDULIST[0].data.shape[1]


# Create and save the object
galaxy = Galaxy()
galaxy.name = GALAXY_NAME
galaxy.dimension_x = END_X
galaxy.dimension_y = END_Y
galaxy.dimension_z = LAYER_COUNT
galaxy.redshift = REDSHIFT
datetime_now = datetime.datetime.now()
galaxy.create_time = datetime_now
galaxy.image_time = datetime_now
galaxy.version_number = version_number
galaxy.galaxy_type = GALAXY_TYPE
galaxy.ra_cent = 0
galaxy.dec_cent = 0
galaxy.current = False
galaxy.pixel_count = 0
galaxy.pixels_processed = 0
session.add(galaxy)

# Flush to the DB so we can get the id
session.flush()

LOG.info('Building the images')
image = FitsImage()
image.buildImage(INPUT_FILE, IMAGE_DIR, filePrefixName, "asinh", False, False, False)

shutil.copyfile(INPUT_FILE, image.get_file_path(IMAGE_DIR, fitsFileName, True))
session.commit()

LOG.info("Done")
