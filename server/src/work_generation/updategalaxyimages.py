import pyfits
from PIL import Image
import math
import os, hashlib
import shutil
from database.database_support import Galaxy, Area, AreaUser
from image.fitsimage import FitsImage
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import db_login

FITS_DIR = "/home/ec2-user/galaxies"
IMAGE_DIR = "/home/ec2-user/galaxyImages"

engine = create_engine(db_login)
Session = sessionmaker(bind=engine)

session = Session()

image = FitsImage()

for galaxy in session.query(Galaxy).order_by(Galaxy.name).all():
    filePrefixName = galaxy.name + "_" + str(galaxy.version_number)
    fitsFileName = filePrefixName + ".fits"

    INPUT_FILE = FITS_DIR + "/POGS_" + galaxy.name + ".fits"
    print galaxy.name, galaxy.version_number
    #if os.path.isfile(INPUT_FILE):
    #    pass
    #    #print INPUT_FILE, 'found'
    #else:
    #    #print INPUT_FILE, 'not found'
    #    temp_name = galaxy.name[0:(len(galaxy.name)-1)]
    #    INPUT_FILE = FITS_DIR + "/POGS_" + temp_name + ".fits"
    #    #print INPUT_FILE
    #    if os.path.isfile(INPUT_FILE):
    #        INPUT_FILE = temp_name
    #        pass
    #        #print INPUT_FILE, 'found'
    #    else:
    #        print INPUT_FILE, 'not found'

    #print INPUT_FILE, image.get_file_path(IMAGE_DIR, fitsFileName, True)

    #shutil.copyfile(INPUT_FILE, image.get_file_path(IMAGE_DIR, fitsFileName, True))
    INPUT_FILE = image.get_file_path(IMAGE_DIR, fitsFileName, False)
    if os.path.isfile(INPUT_FILE):
        image.buildImage(INPUT_FILE, IMAGE_DIR, filePrefixName, 'asinh', False, False, False)
