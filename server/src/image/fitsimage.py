#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
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
import pyfits
import math
import numpy
from PIL import Image
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_
from utils.logging_helper import config_logger
from config import POGS_TMP
from database.database_support_core import IMAGE_FILTERS_USED, FILTER, AREA, AREA_USER
from utils.name_builder import get_colour_image_key, get_thumbnail_colour_image_key
from utils.s3_helper import S3Helper

LOG = config_logger(__name__)


class ImageBuilder:
    """
    This class scales each colour such that the median is centered on 1, and them applies the
    asinh() function to the value.  The hiCut is set to truncate the top 200 values.
    """
    _image_file_key = ""
    _thumbnail_file_key = ""
    _image = None
    _red_filter = 0
    _green_filter = 0
    _blue_filter = 0
    _red_data = None
    _blue_data = None
    _green_data = None
    _width = 0
    _height = 0
    _black_RGB = (0, 0, 0)

    _red_hi_cut = math.pi / 2
    _red_median = 0
    _green_hi_cut = math.pi / 2
    _green_median = 0
    _blue_hi_cut = math.pi / 2
    _blue_median = 0

    _centre = 0.6

    def __init__(self, bucket_name, image_number, image_file_key, thumbnail_file_key, red_filter, green_filter, blue_filter, width, height, centre, connection, galaxy_id):
        """
        Initialise the builder

        :param bucket_name:
        :param image_number:
        :param image_file_key:
        :param thumbnail_file_key:
        :param red_filter:
        :param green_filter:
        :param blue_filter:
        :param width:
        :param height:
        :param centre:
        :param connection:
        :param galaxy_id:
        :return:
        """
        self._bucket_name = bucket_name
        self._image_file_key = image_file_key
        self._thumbnail_file_key = thumbnail_file_key
        self._red_filter = red_filter
        self._green_filter = green_filter
        self._blue_filter = blue_filter
        self._width = width
        self._height = height
        self._centre = centre
        self._image = Image.new("RGB", (self._width, self._height), self._black_RGB)

        # Get the id's before we build as SqlAlchemy flushes which will cause an error
        filter_id_red = self._get_filter_id(connection, red_filter)
        filter_id_blue = self._get_filter_id(connection, blue_filter)
        filter_id_green = self._get_filter_id(connection, green_filter)

        image_filters_used = connection.execute(select([IMAGE_FILTERS_USED])
                                                .where(and_(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id, IMAGE_FILTERS_USED.c.image_number == image_number))).first()
        if image_filters_used is None:
            connection.execute(IMAGE_FILTERS_USED.insert()
                               .values(image_number=image_number,
                                       galaxy_id=galaxy_id,
                                       filter_id_red=filter_id_red,
                                       filter_id_blue=filter_id_blue,
                                       filter_id_green=filter_id_green))
        else:
            connection.execute(IMAGE_FILTERS_USED.update()
                               .where(IMAGE_FILTERS_USED.c.image_filters_used_id == image_filters_used[IMAGE_FILTERS_USED.c.image_filters_used_id])
                               .values(image_number=image_number,
                                       galaxy_id=galaxy_id,
                                       filter_id_red=filter_id_red,
                                       filter_id_blue=filter_id_blue,
                                       filter_id_green=filter_id_green))

    def _get_filter_id(self, connection, filter_number):
        filter_data = connection.execute(select([FILTER]).where(FILTER.c.filter_number == filter_number)).first()
        return filter_data[FILTER.c.filter_id]

    def set_data(self, filter_band, data):
        values = []
        for x in range(0, self._width - 1):
            for y in range(0, self._height - 1):
                value = data[y, x]
                if not math.isnan(value) and value > 0:
                    values.append(value)

        values.sort()
        if len(values) > 1000:
            top_count = int(len(values) * 0.005)
            top_value = values[len(values) - top_count]
        elif len(values) > 0:
            top_value = values[len(values) - 1]
        else:
            top_value = 1

        if len(values) > 1:
            median_value = values[int(len(values) / 2)]
        elif len(values) > 0:
            median_value = values[0]
        else:
            median_value = 1

        if self._red_filter == filter_band:
            self._red_data = numpy.copy(data)
            self._red_hi_cut = top_value
            self._red_median = median_value
        elif self._green_filter == filter_band:
            self._green_data = numpy.copy(data)
            self._green_hi_cut = top_value
            self._green_median = median_value
        elif self._blue_filter == filter_band:
            self._blue_data = numpy.copy(data)
            self._blue_hi_cut = top_value
            self._blue_median = median_value

    def is_valid(self):
        if self._red_data is None or self._green_data is None or self._blue_data is None:
            return False
        else:
            return True

    def save_image(self, s3helper):
        """
        Save the image
        :return:
        """
        red_sigma = self._centre / self._red_median
        green_sigma = self._centre / self._green_median
        blue_sigma = self._centre / self._blue_median

        red_multiplier = 255.0 / math.asinh(self._red_hi_cut * red_sigma)
        green_multiplier = 255.0 / math.asinh(self._green_hi_cut * green_sigma)
        blue_multiplier = 255.0 / math.asinh(self._blue_hi_cut * blue_sigma)

        red_value_range = []
        green_value_range = []
        blue_value_range = []
        for z in range(0, 256):
            red_value_range.append(0)
            green_value_range.append(0)
            blue_value_range.append(0)

        for x in range(0, self._width - 1):
            for y in range(0, self._height - 1):
                red = self._red_data[y, x]
                green = self._green_data[y, x]
                blue = self._blue_data[y, x]
                if math.isnan(red):
                    red = 0
                if math.isnan(green):
                    green = 0
                if math.isnan(blue):
                    blue = 0
                if red > 0 or green > 0 or blue > 0:
                    red = math.asinh(red * red_sigma) * red_multiplier
                    green = math.asinh(green * green_sigma) * green_multiplier
                    blue = math.asinh(blue * blue_sigma) * blue_multiplier
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

                    red_value_range[red] += 1
                    green_value_range[green] += 1
                    blue_value_range[blue] += 1
                    self._image.putpixel((x, self._height - y - 1), (red, green, blue))

        self._save_to_s3(self._image_file_key, s3helper)

        if self._thumbnail_file_key:
            self._image = self._image.resize((80, 80), Image.ANTIALIAS)
            self._save_to_s3(self._thumbnail_file_key, s3helper)

    def _save_to_s3(self, image_file_key, s3Helper):
        """
        Save the image to an S3 bucket

        :param image_file_key:
        :return:
        """
        LOG.info('Saving an image to {0}'.format(image_file_key))
        file_name = '{0}/image.png'.format(POGS_TMP)
        self._image.save(file_name)
        s3Helper.add_file_to_bucket(self._bucket_name, image_file_key, file_name)


class FitsImage:
    useHighCut = False
    centre = 0.5

    def __init__(self, connection):
        self.sigma = None
        self._connection = connection

    def build_image(self, fits_file_name, image_key_stub, galaxy_id, bucket_name):
        """
        Build Three Colour Images, and optionally black and white and white and black images for each image.
        :param fits_file_name:
        :param image_key_stub:
        :param galaxy_id:
        :param bucket:
        """
        # Use the new asinh algorithm.
        self._build_Image_Asinh(fits_file_name, image_key_stub, self.centre, galaxy_id, bucket_name)

    def _get_image_filters(self, hdulist):
        """
        Get the combinations to use
        :param hdulist:
        """
        image1_filters = [0, 0, 0]
        image2_filters = [0, 0, 0]
        image3_filters = [0, 0, 0]
        image4_filters = [0, 0, 0]

        filters_used = []

        for hdu in hdulist:
            filter_number = hdu.header['MAGPHYSI']
            filters_used.append(filter_number)

        if 323 in filters_used and 324 in filters_used and 325 in filters_used and 326 in filters_used and 327 in filters_used:
            image1_filters = [326, 325, 324]
            image2_filters = [325, 324, 323]
            image3_filters = [326, 324, 323]
            image4_filters = [327, 325, 323]
        elif 229 in filters_used and 230 in filters_used and 231 in filters_used and 232 in filters_used and 233 in filters_used:
            image1_filters = [232, 231, 230]
            image2_filters = [231, 230, 229]
            image3_filters = [232, 230, 229]
            image4_filters = [233, 231, 229]
        elif 116 in filters_used and 117 in filters_used and 118 in filters_used and 124 in filters_used and 280 in filters_used and 283 in filters_used:
            image1_filters = [118, 117, 116]
            image2_filters = [117, 116, 124]
            image3_filters = [280, 116, 124]
            image4_filters = [283, 117, 124]
        else:
            LOG.critical('No filters defined that we recognise')

        return image1_filters, image2_filters, image3_filters, image4_filters

    def _build_Image_Asinh(self, fits_file_name, galaxy_key_stub, centre, galaxy_id, bucket_name):
        """
        Build Three Colour Images using the asinh() function.
        :param fits_file_name:
        :param galaxy_key_stub:
        :param centre:
        :param galaxy_id:
        :param bucket:
        """
        hdulist = pyfits.open(fits_file_name, memmap=True)

        hdu = hdulist[0]
        width = hdu.header['NAXIS1']
        height = hdu.header['NAXIS2']

        (image1_filters, image2_filters, image3_filters, image4_filters) = self._get_image_filters(hdulist)

        # Create Three Colour Images
        image1 = ImageBuilder(bucket_name,
                              1,
                              get_colour_image_key(galaxy_key_stub, 1),
                              get_thumbnail_colour_image_key(galaxy_key_stub, 1),
                              image1_filters[0],
                              image1_filters[1],
                              image1_filters[2],
                              width,
                              height,
                              centre,
                              self._connection,
                              galaxy_id)  # i, r, g
        image2 = ImageBuilder(bucket_name,
                              2,
                              get_colour_image_key(galaxy_key_stub, 2),
                              None,
                              image2_filters[0],
                              image2_filters[1],
                              image2_filters[2],
                              width,
                              height,
                              centre,
                              self._connection,
                              galaxy_id)  # r, g, NUV
        image3 = ImageBuilder(bucket_name,
                              3,
                              get_colour_image_key(galaxy_key_stub, 3),
                              None,
                              image3_filters[0],
                              image3_filters[1],
                              image3_filters[2],
                              width,
                              height,
                              centre,
                              self._connection,
                              galaxy_id)  # 3.6, g, NUV
        image4 = ImageBuilder(bucket_name,
                              4,
                              get_colour_image_key(galaxy_key_stub, 4),
                              None,
                              image4_filters[0],
                              image4_filters[1],
                              image4_filters[2],
                              width,
                              height,
                              centre,
                              self._connection,
                              galaxy_id)  # 22, r, NUV
        images = [image1, image2, image3, image4]

        for hdu in hdulist:
            filter_band = hdu.header['MAGPHYSI']
            for image in images:
                image.set_data(filter_band, hdu.data)

        s3helper = S3Helper()
        for image in images:
            if image.is_valid():
                image.save_image(s3helper)
            else:
                print 'not valid'

        hdulist.close()

    def mark_image(self, in_image_file_name, out_image_file_name, galaxy_id, userid):
        """
        Read the image for the galaxy and generate an image that highlights the areas
        that the specified user has generated results.
        :param in_image_file_name:
        :param out_image_file_name:
        :param galaxy_id:
        :param userid:
        """
        image = Image.open(in_image_file_name, "r").convert("RGBA")
        width, height = image.size
        LOG.info('Width: {0}, Height: {1}'.format(width, height))

        areas = self._connection.execute(select([AREA], from_obj=AREA.join(AREA_USER))
                                         .where(and_(AREA_USER.c.userid == userid, AREA.c.galaxy_id == galaxy_id))
                                         .order_by(AREA.c.top_x, AREA.c.top_y))

        for area in areas:
            # LOG.info('top_x: {0}, bottom_x: {1}, top_y: {2}, bottom_y: {3}'.format(area[AREA.c.top_x], area[AREA.c.bottom_x], area[AREA.c.top_y], area[AREA.c.bottom_y]))
            for x in range(area[AREA.c.top_x], area[AREA.c.bottom_x]):
                for y in range(area[AREA.c.top_y], area[AREA.c.bottom_y]):
                    if x < width and y < height:
                        self._mark_pixel(image, x, height - y - 1)

        image.save(out_image_file_name)

    def _mark_pixel(self, image, x, y):
        """
        Mark the specified pixel to highlight the area where the user has
        generated results.
        :param image:
        :param x:
        :param y:
        """
        px = image.getpixel((x, y))
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
        image.putpixel((x, y), (r, g, b))
