import fitsimage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database_support import login

image = fitsimage.FitsImage()

magphysDir = "/Users/rob/magphys/"
method = "log"
createBWImages = True
createLog = True
debug = True

image.buildImage(magphysDir + "POGS_NGC1209.fits", magphysDir + "POGS_NGC1209", "POGS_NGC1209_" + method, method, createBWImages, createLog, debug)
image.buildImage(magphysDir + "POGS_NGC2500.fits", magphysDir + "POGS_NGC2500", "POGS_NGC2500_" + method, method, createBWImages, createLog, debug)
image.buildImage(magphysDir + "POGS_NGC2537.fits", magphysDir + "POGS_NGC2537", "POGS_NGC2537_" + method, method, createBWImages, createLog, debug)
image.buildImage(magphysDir + "POGS_NGC2541.fits", magphysDir + "POGS_NGC2541", "POGS_NGC2541_" + method, method, createBWImages, createLog, debug)
image.buildImage(magphysDir + "POGS_NGC2798.fits", magphysDir + "POGS_NGC2798", "POGS_NGC2798_" + method, method, createBWImages, createLog, debug)
image.buildImage(magphysDir + "POGS_NGC6240.fits", magphysDir + "POGS_NGC6240", "POGS_NGC6240_" + method, method, createBWImages, createLog, debug)
image.buildImage(magphysDir + "POGS_NGC6384.fits", magphysDir + "POGS_NGC6384", "POGS_NGC6384_" + method, method, createBWImages, createLog, debug)