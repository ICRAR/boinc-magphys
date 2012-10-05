import fitsimage
import os

image = fitsimage.FitsImage()

magphysDir = "/Users/rob/magphys/"
method = "asinh"
createBWImages = False
createLog = False
debug = False

image.includeHash = False

#image.buildImage(magphysDir + "POGS_NGC1209.fits", magphysDir + "POGS_NGC1209", "POGS_NGC1209_" + method, method, createBWImages, createLog, debug)
#image.buildImage(magphysDir + "POGS_NGC2500.fits", magphysDir + "POGS_NGC2500", "POGS_NGC2500_" + method, method, createBWImages, createLog, debug)
#image.buildImage(magphysDir + "POGS_NGC2537.fits", magphysDir + "POGS_NGC2537", "POGS_NGC2537_" + method, method, createBWImages, createLog, debug)
#image.buildImage(magphysDir + "POGS_NGC2541.fits", magphysDir + "POGS_NGC2541", "POGS_NGC2541_" + method, method, createBWImages, createLog, debug)
#image.buildImage(magphysDir + "POGS_NGC2798.fits", magphysDir + "POGS_NGC2798", "POGS_NGC2798_" + method, method, createBWImages, createLog, debug)
#image.buildImage(magphysDir + "POGS_NGC6240.fits", magphysDir + "POGS_NGC6240", "POGS_NGC6240_" + method, method, createBWImages, createLog, debug)
#image.buildImage(magphysDir + "POGS_NGC6384.fits", magphysDir + "POGS_NGC6384", "POGS_NGC6384_" + method, method, createBWImages, createLog, debug)

magphysDir = "/Users/rob/magphys/pogsv3/"
for file in os.listdir(magphysDir):
    str = file.split('.')
    if (len(str) > 1):
        print file
        name = str[0]
        image.buildImage(magphysDir + file, magphysDir + name, name, method, createBWImages, createLog, debug)