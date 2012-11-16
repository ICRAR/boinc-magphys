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
Image generation
"""
import logging
import pyfits
import math
import os, hashlib
import numpy
from PIL import Image
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_
from database.database_support_core import IMAGE_FILTERS_USED, FILTER, AREA, AREA_USER, GALAXY

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

class ImageBuilder:
    """
    This class scales each colour such that the median is centered on 1, and them applies the
    asinh() function to the value.  The hiCut is set to truncate the top 200 values.
    """
    debug = False
    imageFileName = ""
    thumbnailFileName = ""
    image = None
    redFilter = 0
    greenFilter = 0
    blueFilter = 0
    redData = None
    blueData = None
    greenData = None
    width = 0
    height = 0
    blackRGB = (0, 0, 0)

    redHiCut = math.pi/2
    redMedian = 0
    greenHiCut = math.pi/2
    greenMedian = 0
    blueHiCut = math.pi/2
    blueMedian = 0

    centre = 0.6

    def __init__(self, image_number, imageFileName, thumbnailFileName, redFilter, greenFilter, blueFilter, width, height, debug, centre, connection, galaxy_id):
        self.imageFileName = imageFileName
        self.thumbnailFileName = thumbnailFileName
        self.redFilter = redFilter
        self.greenFilter = greenFilter
        self.blueFilter = blueFilter
        self.width = width
        self.height = height
        self.debug = debug
        self.centre = centre
        self.image = Image.new("RGB", (self.width, self.height), self.blackRGB)

        # Get the id's before we build as SqlAlchemy flushes which will cause an error as
        filter_id_red = self._get_filter_id(connection, redFilter)
        filter_id_blue = self._get_filter_id(connection, blueFilter)
        filter_id_green = self._get_filter_id(connection, greenFilter)

        image_filters_used = connection.execute(select([IMAGE_FILTERS_USED]).where(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id)).first()
        if image_filters_used is None:
            IMAGE_FILTERS_USED.insert().values(image_number = image_number,
                file_name = imageFileName,
                galaxy_id = galaxy_id,
                filter_id_red = filter_id_red,
                filter_id_blue = filter_id_blue,
                filter_id_green = filter_id_green)
        else:
            IMAGE_FILTERS_USED.update().where(IMAGE_FILTERS_USED.c.image_filters_used_id == image_filters_used[IMAGE_FILTERS_USED.c.image_filters_used_id]).values(image_number = image_number,
                file_name = imageFileName,
                galaxy_id = galaxy_id,
                filter_id_red = filter_id_red,
                filter_id_blue = filter_id_blue,
                filter_id_green = filter_id_green)


    def _get_filter_id(self, connection, filter_number):
        filter = connection.execute(select([FILTER]).where(FILTER.c.filter_number == filter_number)).first()
        return filter[FILTER.c.filter_id]

    def setData(self, filter, data):
        values = []
        for x in range(0, self.width-1):
            for y in range(0, self.height-1):
                value = data[y, x]
                if not math.isnan(value) and value > 0:
                    values.append(value)

        values.sort()
        if len(values) > 1000:
            topCount = int(len(values)*0.005)
            topValue = values[len(values)-topCount]
        elif len(values) > 0:
            topValue = values[len(values)-1]
        else:
            topValue = 1
        if len(values) > 1:
            medianvalue = values[int(len(values)/2)]
        elif len(values) > 0:
            medianvalue = values[0]
        else:
            medianvalue = 1

        if self.redFilter == filter:
            self.redData = numpy.copy(data)
            self.redHiCut = topValue
            self.redMedian = medianvalue
        elif self.greenFilter == filter:
            self.greenData = numpy.copy(data)
            self.greenHiCut = topValue
            self.greenMedian = medianvalue
        elif self.blueFilter == filter:
            self.blueData = numpy.copy(data)
            self.blueHiCut = topValue
            self.blueMedian = medianvalue

    def isValid(self):
        if self.redData is None or self.greenData is None or self.blueData is None:
            return False
        else:
            return True

    def saveImage(self):
        redSigma = self.centre / self.redMedian
        greenSigma = self.centre / self.greenMedian
        blueSigma = self.centre / self.blueMedian

        redMult = 255.0 / math.asinh(self.redHiCut * redSigma)
        greenMult = 255.0 / math.asinh(self.greenHiCut * greenSigma)
        blueMult = 255.0 / math.asinh(self.blueHiCut * blueSigma)

        redValuerange = []
        greenValuerange = []
        blueValuerange = []
        for z in range(0, 256):
            redValuerange.append(0)
            greenValuerange.append(0)
            blueValuerange.append(0)

        for x in range(0, self.width-1):
            for y in range(0, self.height-1):
                red = self.redData[y,x]
                green = self.greenData[y,x]
                blue = self.blueData[y,x]
                if math.isnan(red):
                    red = 0
                if math.isnan(green):
                    green = 0
                if math.isnan(blue):
                    blue = 0
                if red > 0 or green > 0 or blue > 0:
                    red = math.asinh(red * redSigma) * redMult
                    green = math.asinh(green * greenSigma) * greenMult
                    blue = math.asinh(blue * blueSigma) * blueMult
                    if red < 0:
                        red = 0
                    elif red > 255:
                        red = 255
                    if green < 0:
                        green = 0
                    elif green > 255:
                        green = 255
                    if blue < 0:
                        blue = 0
                    elif blue > 255:
                        blue = 255
                    red = int(red)
                    green = int(green)
                    blue = int(blue)

                    redValuerange[red] += 1
                    greenValuerange[green] += 1
                    blueValuerange[blue] += 1
                    self.image.putpixel((x,self.width-y-1), (red, green, blue))
        self.image.save(self.imageFileName)

        if self.thumbnailFileName:
            self.image = self.image.resize((80,80), Image.ANTIALIAS)
            self.image.save(self.thumbnailFileName)

        if self.debug:
            for z in range(0, 256):
                print z, redValuerange[z], greenValuerange[z], blueValuerange[z]

class FitsImage:
    useHighCut = False
    includeHash = True
    centre = 0.5

    def __init__(self, connection):
        self.sigma = None
        self._connection = connection

    def buildImage(self, fitsFileName, imageDirName, imagePrefixName, debug, galaxy_id):
        """
        Build Three Colour Images, and optionally black and white and white and black images for each image.
        """
        # Use the new asinh algorithm.
        self._buildImageAsinh(fitsFileName, imageDirName, imagePrefixName, debug, self.centre, galaxy_id)

    def _get_image_filters(self, hdulist):
        """
        Get the combinations to use
        """
        image1_filters = [0,0,0]
        image2_filters = [0,0,0]
        image3_filters = [0,0,0]
        image4_filters = [0,0,0]

        filters_used = []

        for hdu in hdulist:
            filter_number = hdu.header['MAGPHYSI']
            filters_used.append(filter_number)

        if 323 in filters_used \
            and 324 in filters_used \
            and 325 in filters_used \
            and 326 in filters_used \
            and 327 in filters_used:
            image1_filters = [326, 325, 324]
            image2_filters = [325, 324, 323]
            image3_filters = [326, 324, 323]
            image4_filters = [327, 325, 323]
        elif 116 in filters_used \
            and 117 in filters_used \
            and 118 in filters_used \
            and 124 in filters_used \
            and 280 in filters_used \
            and 283 in filters_used:
            image1_filters = [118, 117, 116]
            image2_filters = [117, 116, 124]
            image3_filters = [280, 116, 124]
            image4_filters = [283, 117, 124]
        else:
            LOG.critical('No filters defined that we recognise')

        return image1_filters, image2_filters, image3_filters, image4_filters

    def _buildImageAsinh(self, fitsFileName, imageDirName, imagePrefixName, debug, centre, galaxy_id):
        """
        Build Three Colour Images using the asinh() function.
        """
        if imageDirName[-1] != "/":
            imageDirName += "/"
        if os.path.isfile(imageDirName):
            LOG.info('Directory %s exists', imageDirName)
            return 1
        elif os.path.isdir(imageDirName):
            pass
        else:
            os.mkdir(imageDirName)

        hdulist = pyfits.open(fitsFileName, memmap=True)
        if debug:
            hdulist.info()

        hdu = hdulist[0]
        width = hdu.header['NAXIS1']
        height = hdu.header['NAXIS2']

        (image1_filters, image2_filters, image3_filters, image4_filters) = self._get_image_filters(hdulist)

        # Create Three Colour Images
        image1 = ImageBuilder(1, self.get_colour_image_path(imageDirName, imagePrefixName, 1, True),
            self.get_thumbnail_colour_image_path(imageDirName, imagePrefixName, 1, True),
            image1_filters[0], image1_filters[1], image1_filters[2], width, height, debug, centre, self._connection, galaxy_id) # i, r, g
        image2 = ImageBuilder(2, self.get_colour_image_path(imageDirName, imagePrefixName, 2, True), None,
            image2_filters[0], image2_filters[1], image2_filters[2], width, height, debug, centre, self._connection, galaxy_id) # r, g, NUV
        image3 = ImageBuilder(3, self.get_colour_image_path(imageDirName, imagePrefixName, 3, True), None,
            image3_filters[0], image3_filters[1], image3_filters[2], width, height, debug, centre, self._connection, galaxy_id) # 3.6, g, NUV
        image4 = ImageBuilder(4, self.get_colour_image_path(imageDirName, imagePrefixName, 4, True), None,
            image4_filters[0], image4_filters[1], image4_filters[2], width, height, debug, centre, self._connection, galaxy_id) # 22, r, NUV
        images = [image1, image2, image3, image4]

        file = 0
        for hdu in hdulist:
            file += 1
            if debug:
                print hdu,
                print file

            filter = hdu.header['MAGPHYSI']
            for image in images:
                image.setData(filter, hdu.data)

        for image in images:
            if image.isValid():
                image.saveImage()
            else:
                print 'not valid'

        hdulist.close()

    def applyFunc(self, value, method):
        if method == 'atan':
            return math.atan(value / self.sigma)
        elif method == 'log':
            return math.log((value / self.sigma) + 1.0)
        elif method == 'log-old':
            return math.log(value)
        elif method == 'log10':
            return math.log(value, 10.0)
        elif method == 'asinh':
            return math.asinh(value / self.sigma)
        else:
           return value

    def filename_hash(self, name, hash_fanout):
        """
        Accepts a filename (without path) and the hash fanout.
        Returns the directory bucket where the file will reside.
        The hash fanout is typically provided by the project config file.
        """
        h = hex(int(hashlib.md5(name).hexdigest()[:8], 16) % hash_fanout)[2:]

        # check for the long L suffix. It seems like it should
        # never be present but that isn't the case
        if h.endswith('L'):
            h = h[:-1]
        return h

    def get_file_path(self, dirName, fileName, create):
        """
        Accepts a directory name and file name and returns the relative path to the file.
        This method accounts for file hashing and includes the directory
        bucket in the path returned.
        """
        if self.includeHash:
            fanout = 1024
            hashed = self.filename_hash(fileName, fanout)
            hashDirName = os.path.join(dirName,hashed)
            if os.path.isfile(hashDirName):
                pass
            elif os.path.isdir(hashDirName):
                pass
            elif create:
                os.mkdir(hashDirName)
            return os.path.join(dirName,hashed,fileName)
        else:
            return os.path.join(dirName,fileName)

    def get_colour_image_path(self, imageDirName, imagePrefixName, colour, create):
        """
        Generates the relative path to the file given the directory name, image prefix
        and colour.  The file name is used to generate a hash to spread the files across
        many directories to avoid having too many files in a single directory.
        """
        return self.get_file_path(imageDirName, imagePrefixName + "_colour_" + str(colour) + ".png", create)

    def get_thumbnail_colour_image_path(self, imageDirName, imagePrefixName, colour, create):
        """
        Generates the relative path to the file given the directory name, image prefix
        and colour.  The file name is used to generate a hash to spread the files across
        many directories to avoid having too many files in a single directory.
        """
        return self.get_file_path(imageDirName, imagePrefixName + "_tn_colour_" + str(colour) + ".png", create)

    def get_bw_image_path(self, imageDirName, imagePrefixName, file, create):
        """
        Generates the relative path to the file given the directory name, image prefix
        and image number for the Black and White Image.  The file name is used to generate
        a hash to spread the files across many directories to avoid having too many files
        in a single directory.
        """
        return self.get_file_path(imageDirName, imagePrefixName + "_" + str(file) + '_bw.png', create)

    def get_wb_image_path(self, imageDirName, imagePrefixName, file, create):
        """
        Generates the relative path to the file given the directory name, image prefix
        and image number for the White and Black Image.  The file name is used to generate
        a hash to spread the files across many directories to avoid having too many files
        in a single directory.
        """
        return self.get_file_path(imageDirName, imagePrefixName + "_" + str(file) + '_wb.png', create)

    def markImage(self, inImageFileName, outImageFileName, galaxy_id, userid):
        """
        Read the image for the galaxy and generate an image that highlights the areas
        that the specified user has generated results.
        """
        image = Image.open(inImageFileName, "r").convert("RGBA")
        width, height = image.size

        areas = self._connection.execute(select([AREA], from_obj=AREA.join(AREA_USER)).where(and_(AREA_USER.c.userid == userid, AREA.c.galaxy_id == galaxy_id)).order_by(AREA.c.top_x, AREA.c.top_y))

        for area in areas:
            for x in range(area[AREA.c.top_x], area[AREA.c.bottom_x]):
                for y in range(area[AREA.c.top_y], area[AREA.c.bottom_y]):
                    if x < height and y < width:
                        self.markPixel(image, x, width-y-1)

        image.save(outImageFileName)

    def markPixel(self, image, x, y):
        """
        Mark the specified pixel to highlight the area where the user has
        generated results.
        """
        px = image.getpixel((x,y))
        r = int(px[0] + ((255 - px[0]) * 0.5))
        g = int(px[1] + ((255 - px[1]) * 0.5))
        b = int(px[2] + ((255 - px[2]) * 0.5))
        if r > 255:
            r = 255
        if g > 255:
            g = 255
        if b > 255:
            b = 255
        if r < 85:
            r = 85
        if g < 85:
            g = 85
        if b < 85:
            b = 85
        image.putpixel((x,y), (r, g, b))

    def userGalaxies(self, userid):
        """
        Determines the galaxies that the selected user has generated results.  Returns an array of
        galaxy_ids.
        """
        return self._connection.execute(select([GALAXY], from_obj= GALAXY.join(AREA).join(AREA_USER)).where(AREA_USER.c.userid == userid).order_by(GALAXY.c.name, GALAXY.c.version_number))
