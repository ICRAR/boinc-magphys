import fitsimage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database_support import login

image = fitsimage.FitsImage()

magphysDir = "/Users/rob/magphys/"
fitsFileName = magphysDir + "POGS_NGC1209.fits"
imageDirName = magphysDir + "POGS_NGC1209"
imagePrefixName = "POGS_NGC1209"

#inImageFileName = imageDirName + "/" + imagePrefixName + "_colour_1.jpg"
inImageFileName = image.get_colour_image_path(imageDirName, imagePrefixName, 1)
outImageFileName = imageDirName + "/" + imagePrefixName + "_colour_1_mark.png"
galaxy_id = 1;
userid = 2

engine = create_engine(login)
Session = sessionmaker(bind=engine)
session = Session()

image.buildImage(fitsFileName, imageDirName, imagePrefixName, "log", False, False, False)
image.markImage(session, inImageFileName, outImageFileName, galaxy_id, userid)
galaxyIds = image.userGalaxyIds(session, userid)
for galaxyId in galaxyIds:
    print 'GalaxyId', galaxyIds