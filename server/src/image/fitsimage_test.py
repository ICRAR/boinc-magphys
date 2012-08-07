import fitsimage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import db_login

image = fitsimage.FitsImage()

fitsName = "POGS_NGC2500"
magphysDir = "/Users/rob/magphys/"
fitsFileName = magphysDir + fitsName + ".fits"
imageDirName = magphysDir + fitsName
imagePrefixName = fitsName

#inImageFileName = imageDirName + "/" + imagePrefixName + "_colour_1.jpg"
inImageFileName = image.get_colour_image_path(imageDirName, imagePrefixName, 1)
outImageFileName = imageDirName + "/" + imagePrefixName + "_colour_1_mark.png"
galaxy_id = 1;
userid = 2

#engine = create_engine(db_login)
#Session = sessionmaker(bind=engine)
#session = Session()

image.buildImage(fitsFileName, imageDirName, imagePrefixName, "log", False, True, False)
#image.markImage(session, inImageFileName, outImageFileName, galaxy_id, userid)
#galaxyIds = image.userGalaxyIds(session, userid)
#for galaxyId in galaxyIds:
#    print 'GalaxyId', galaxyIds