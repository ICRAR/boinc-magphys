import os
from database.database_support import Galaxy
from image.fitsimage import FitsImage
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import DB_LOGIN

FITS_DIR = "/home/ec2-user/galaxies"
IMAGE_DIR = "/home/ec2-user/galaxyImages"

engine = create_engine(DB_LOGIN)
Session = sessionmaker(bind=engine)

session = Session()
image = FitsImage()

for galaxy in session.query(Galaxy).order_by(Galaxy.name).all():
    filePrefixName = galaxy.name + "_" + str(galaxy.version_number)
    fitsFileName = filePrefixName + ".fits"

    INPUT_FILE = FITS_DIR + "/POGS_" + galaxy.name + ".fits"
    print galaxy.name, galaxy.version_number

    INPUT_FILE = image.get_file_path(IMAGE_DIR, fitsFileName, False)
    if os.path.isfile(INPUT_FILE):
        image.buildImage(INPUT_FILE, IMAGE_DIR, filePrefixName, 'asinh', False, False, False, session)

session.commit()
