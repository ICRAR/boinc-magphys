import fitsimage

image = fitsimage.FitsImage()

magphysDir = "/Users/rob/magphys/"
fitsFileName = magphysDir + "POGS_NGC6240.fits"
imageDirName = magphysDir + "POGS_NGC6240"
imagePrefixName = "POGS_NGC6240_log"

inImageFileName = imageDirName + "/" + imagePrefixName + "_colour_1.jpg"
outImageFileName = imageDirName + "/" + imagePrefixName + "_colour_1_mark.jpg"
galaxy_id = 1;
userid = 2

#image.buildImage(fitsFileName, imageDirName, imagePrefixName, "log", False, False, False)
image.markImage(inImageFileName, outImageFileName, galaxy_id, userid)
galaxyIds = image.userGalaxy(userid)
for galaxyId in galaxyIds:
    print 'GalaxyId', galaxyIds