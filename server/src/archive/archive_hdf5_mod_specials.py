#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2015
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
Module used to write data to an HDF5 file
"""
import gzip
import shutil
import datetime
import h5py
import math
import numpy
import os
import time
from utils.logging_helper import config_logger
from sqlalchemy.sql.expression import select, func
from config import MIN_HIST_VALUE, ARCHIVED, PROCESSED, HDF5_OUTPUT_DIRECTORY, POGS_TMP
from database.database_support_core import FITS_HEADER, AREA, IMAGE_FILTERS_USED, AREA_USER, PIXEL_RESULT, PARAMETER_NAME, GALAXY, RUN_FILTER
from utils.name_builder import get_sed_files_bucket, get_galaxy_file_name
from utils.s3_helper import S3Helper
from utils.shutdown_detection import shutdown

LOG = config_logger(__name__)

OUTPUT_FORMAT_1_00 = 'Version 1.00'
OUTPUT_FORMAT_1_01 = 'Version 1.01'
OUTPUT_FORMAT_1_02 = 'Version 1.02'
OUTPUT_FORMAT_1_03 = 'Version 1.03'
OUTPUT_FORMAT_1_04 = 'Version 1.04'

PARAMETER_TYPES = ['f_mu (SFH)',
                   'f_mu (IR)',
                   'mu parameter',
                   'tau_V',
                   'sSFR_0.1Gyr',
                   'M(stars)',
                   'Ldust',
                   'T_C^ISM',
                   'T_W^BC',
                   'xi_C^tot',
                   'xi_PAH^tot',
                   'xi_MIR^tot',
                   'xi_W^tot',
                   'tau_V^ISM',
                   'M(dust)',
                   'SFR_0.1Gyr']

NUMBER_PARAMETERS = 16
NUMBER_IMAGES = 7
HISTOGRAM_BLOCK_SIZE = 1000000
MAX_X_Y_BLOCK = 1024

INDEX_BEST_FIT = 0
INDEX_PERCENTILE_50 = 1
INDEX_HIGHEST_PROB_BIN = 2
INDEX_PERCENTILE_2_5 = 3
INDEX_PERCENTILE_16 = 4
INDEX_PERCENTILE_84 = 5
INDEX_PERCENTILE_97_5 = 6

INDEX_F_MU_SFH = 0
INDEX_F_MU_IR = 1
INDEX_MU_PARAMETER = 2
INDEX_TAU_V = 3
INDEX_SSFR_0_1GYR = 4
INDEX_M_STARS = 5
INDEX_L_DUST = 6
INDEX_T_C_ISM = 7
INDEX_T_W_BC = 8
INDEX_XI_C_TOT = 9
INDEX_XI_PAH_TOT = 10
INDEX_XI_MIR_TOT = 11
INDEX_XI_W_TOT = 12
INDEX_TAU_V_ISM = 13
INDEX_M_DUST = 14
INDEX_SFR_0_1GYR = 15

data_type_area = numpy.dtype([
    ('area_id',     long),
    ('top_x',       int),
    ('top_y',       int),
    ('bottom_x',    int),
    ('bottom_y',    int),
    ('workunit_id', long),
    ('update_time', h5py.special_dtype(vlen=str)),
])
data_type_area_user = numpy.dtype([
    ('area_id', long),
    ('userid', long),
    ('create_time', h5py.special_dtype(vlen=str)),
])
data_type_fits_header1_00 = numpy.dtype([
    ('keyword', h5py.special_dtype(vlen=str)),
    ('value',   h5py.special_dtype(vlen=str)),
])
data_type_fits_header1_01 = numpy.dtype([
    ('keyword', h5py.special_dtype(vlen=str)),
    ('value',   h5py.special_dtype(vlen=str)),
    ('comment', h5py.special_dtype(vlen=str)),
])
data_type_image_filter = numpy.dtype([
    ('image_number',    long),
    ('filter_id_red',   long),
    ('filter_id_green', long),
    ('filter_id_blue',  long),
])
data_type_pixel = numpy.dtype([
    ('pxresult_id', long),
    ('area_id',     long),
    ('i_sfh',       float),
    ('i_ir',        float),
    ('chi2',        float),
    ('redshift',    float),
    ('i_opt',       float),
    ('dmstar',      float),
    ('dfmu_aux',    float),
    ('dz',          float),
])
data_type_pixel_histogram = numpy.dtype([
    ('x_axis', float),
    ('hist_value', float),
])
data_type_block_details = numpy.dtype([
    ('block_id', long),
    ('index',    long),
    ('length',   long),
])
data_type_pixel_parameter = numpy.dtype([
    ('first_prob_bin', float),
    ('last_prob_bin',  float),
    ('bin_step',       float),
])
data_type_pixel_filter = numpy.dtype([
    ('observed_flux',             float),
    ('observational_uncertainty', float),
    ('flux_bfm',                  float),
])


def store_area(connection, galaxy_id, group):
    """
    Store the areas associated with a galaxy
    """
    LOG.info('Storing the areas')
    count = connection.execute(select([func.count(AREA.c.area_id)]).where(AREA.c.galaxy_id == galaxy_id).where(AREA.c.top_x >= 0)).first()[0]
    rad_count = connection.execute(select([func.count(AREA.c.area_id)]).where(AREA.c.galaxy_id == galaxy_id).where(AREA.c.top_x == -2)).first()[0]
    int_flux_count = 0

    LOG.info('Count {0}'.format(count))

    data = numpy.zeros(count, dtype=data_type_area)

    rad_data = None
    if rad_count > 0:
        # if there are radial areas, create the array for them
        rad_data = numpy.zeros(rad_count, dtype=data_type_area)
        rad_count = 0

    count = 0
    for area in connection.execute(select([AREA]).where(AREA.c.galaxy_id == galaxy_id).order_by(AREA.c.area_id)):
        if area[AREA.c.top_x] == -1:
            # This is an integrated flux area
            LOG.info('Integrated flux area found (id={0})'.format(area[AREA.c.area_id]))
            int_flux = numpy.zeros(1, dtype=data_type_area)  # Can only ever be 1 integrated flux area
            int_flux[0] = (area[AREA.c.area_id],
                           area[AREA.c.top_x],
                           area[AREA.c.top_y],
                           area[AREA.c.bottom_x],
                           area[AREA.c.bottom_y],
                           area[AREA.c.workunit_id] if area[AREA.c.workunit_id] is not None else -1,
                           str(area[AREA.c.update_time]),
                           )
            group.create_dataset('int_flux', data=int_flux, compression='gzip')
            int_flux_count = 1

        elif area[AREA.c.top_x] == -2:
            # This is a radial area
            LOG.info('Radial area {0} found (id={1})'.format(rad_count+1, area[AREA.c.area_id]))
            rad_data[rad_count] = (
                area[AREA.c.area_id],
                area[AREA.c.top_x],
                area[AREA.c.top_y],
                area[AREA.c.bottom_x],
                area[AREA.c.bottom_y],
                area[AREA.c.workunit_id] if area[AREA.c.workunit_id] is not None else -1,
                str(area[AREA.c.update_time]),
            )

            rad_count += 1

        else:
            # This is a standard area
            data[count] = (
                area[AREA.c.area_id],
                area[AREA.c.top_x],
                area[AREA.c.top_y],
                area[AREA.c.bottom_x],
                area[AREA.c.bottom_y],
                area[AREA.c.workunit_id] if area[AREA.c.workunit_id] is not None else -1,
                str(area[AREA.c.update_time]),
                )
            count += 1
    if rad_data is not None:
        group.create_dataset('rad_area', data=rad_data, compression='gzip')

    group.create_dataset('area', data=data, compression='gzip')
    return count, rad_count, int_flux_count  # now return the radial area count too. Int flux count will be 0 or 1


def store_area_user(connection, galaxy_id, group):
    """
    Store the areas associated with a galaxy
    """
    LOG.info('Storing the area_users')
    count = connection.execute(select([func.count(AREA_USER.c.areauser_id)], from_obj=AREA_USER.join(AREA)).where(AREA.c.galaxy_id == galaxy_id)).first()[0]
    data = numpy.zeros(count, dtype=data_type_area_user)
    count = 0
    for area_user in connection.execute(select([AREA_USER], from_obj=AREA_USER.join(AREA)).where(AREA.c.galaxy_id == galaxy_id).order_by(AREA_USER.c.areauser_id)):
        data[count] = (
            area_user[AREA_USER.c.area_id],
            area_user[AREA_USER.c.userid],
            str(area_user[AREA_USER.c.create_time]),
        )
        count += 1
    group.create_dataset('area_user', data=data, compression='gzip')


def store_fits_header(connection, galaxy_id, group):
    """
    Store the fits header data for a galaxy in the HDF5 file
    """
    LOG.info('Storing the fits headers')
    count = connection.execute(select([func.count(FITS_HEADER.c.fitsheader_id)]).where(FITS_HEADER.c.galaxy_id == galaxy_id)).first()[0]
    data = numpy.zeros(count, dtype=data_type_fits_header1_01)
    count = 0
    for fits_header in connection.execute(select([FITS_HEADER]).where(FITS_HEADER.c.galaxy_id == galaxy_id).order_by(FITS_HEADER.c.fitsheader_id)):
        data[count] = (
            fits_header[FITS_HEADER.c.keyword],
            fits_header[FITS_HEADER.c.value],
            fits_header[FITS_HEADER.c.comment],
        )
        count += 1
    group.create_dataset('fits_header', data=data, compression='gzip')


def store_image_filters(connection, galaxy_id, group):
    """
    Store the image filters used
    """
    LOG.info('Storing the image filters')
    count = connection.execute(select([func.count(IMAGE_FILTERS_USED.c.image_filters_used_id)]).where(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id)).first()[0]
    data = numpy.zeros(count, dtype=data_type_image_filter)
    count = 0
    for image_filters_used in connection.execute(select([IMAGE_FILTERS_USED]).where(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id).order_by(IMAGE_FILTERS_USED.c.image_filters_used_id)):
        data[count] = (image_filters_used[IMAGE_FILTERS_USED.c.image_number],
                       image_filters_used[IMAGE_FILTERS_USED.c.filter_id_red],
                       image_filters_used[IMAGE_FILTERS_USED.c.filter_id_green],
                       image_filters_used[IMAGE_FILTERS_USED.c.filter_id_blue], )
        count += 1
    group.create_dataset('image_filters', data=data, compression='gzip')


def get_chunks(dimension):
    """
    Break the dimension up into chunks
    :param dimension:
    :return: a list with the number of chunks

    >>> get_chunks(1)
    [0]
    >>> get_chunks(10)
    [0]
    >>> get_chunks(1023)
    [0]
    >>> get_chunks(1024)
    [0]
    >>> get_chunks(1025)
    [0, 1]
    >>> get_chunks(2047)
    [0, 1]
    >>> get_chunks(2048)
    [0, 1]
    >>> get_chunks(2049)
    [0, 1, 2]

    """
    return range(((dimension - 1) / MAX_X_Y_BLOCK) + 1)


def get_size(block, dimension):
    """
    How big is this axis
    :param block:
    :param dimension:
    :return:

    >>> get_size(0, 50)
    50
    >>> get_size(0, 1024)
    1024
    >>> get_size(0, 2244)
    1024
    >>> get_size(1, 2244)
    1024
    >>> get_size(2, 2244)
    196
    """
    elements = get_chunks(dimension)
    if len(elements) == 1:
        return dimension
    elif block < len(elements) - 1:
        return MAX_X_Y_BLOCK

    return dimension - (block * MAX_X_Y_BLOCK)


def area_intersects_block1(block_x, block_y, area_details):
    """
    Is the area in this block
    :param block_x:
    :param block_y:
    :param area_details:
    :return:
    >>> area_intersects_block1(0, 0, [0, 0, 10, 10])
    True
    >>> area_intersects_block1(0, 0, [1020, 1020, 1030, 1030])
    True
    >>> area_intersects_block1(0, 1, [1020, 1020, 1030, 1030])
    True
    >>> area_intersects_block1(1, 0, [1020, 1020, 1030, 1030])
    True
    >>> area_intersects_block1(1, 1, [1020, 1020, 1030, 1030])
    True
    >>> area_intersects_block1(2, 1, [1020, 1020, 1030, 1030])
    False
    >>> area_intersects_block1(1, 2, [1020, 1020, 1030, 1030])
    False
    >>> area_intersects_block1(2, 2, [1020, 1020, 1030, 1030])
    False
    """
    x1 = area_details[0]
    if x1 < 0:  # areas with negative x are special and should be disregarded here.
        return False
    y1 = area_details[1]
    x2 = area_details[2]
    y2 = area_details[3]
    block_top_x = block_x * MAX_X_Y_BLOCK
    block_top_y = block_y * MAX_X_Y_BLOCK
    block_bottom_x = block_top_x + MAX_X_Y_BLOCK - 1
    block_bottom_y = block_top_y + MAX_X_Y_BLOCK - 1
    LOG.info('x1: {0}, y1: {1}, x2: {2}, y2: {3} - btx: {4}, bty: {5}, bbx: {6}, bby: {7}'.format(x1, y1, x2, y2, block_top_x, block_top_y, block_bottom_x, block_bottom_y))

    separate = x2 < block_top_x or x1 > block_bottom_x or y1 > block_bottom_y or y2 < block_top_y
    return not separate


def area_intersects_block(connection, key, block_x, block_y, map_area_ids):
    """
    Is this area in the block we're working on?
    :param connection:
    :param key: the number before the
    :param block_x:
    :param block_y:
    :return:
    """
    (path, file_name) = os.path.split(key)
    (area_id_name, ext) = os.path.splitext(file_name)
    area_id = int(area_id_name)
    area_details = map_area_ids.get(area_id)
    if area_details is None:
        area = connection.execute(select([AREA]).where(AREA.c.area_id == area_id)).first()
        area_details = [area[AREA.c.top_x], area[AREA.c.top_y], area[AREA.c.bottom_x], area[AREA.c.bottom_y]]
        map_area_ids[area_id] = area_details

    # We have to be careful as an area could straddle a boundary so some bits will be in it and others won't
    return area_intersects_block1(block_x, block_y, area_details)


def load_map_areas(connection, map_areas, galaxy_id):
    """
    Load the area map

    :param connection:
    :param map_areas:
    :param galaxy_id:
    :return:
    """
    LOG.info('Loading the area details')
    for area in connection.execute(select([AREA]).where(AREA.c.galaxy_id == galaxy_id)):
        area_details = [area[AREA.c.top_x], area[AREA.c.top_y], area[AREA.c.bottom_x], area[AREA.c.bottom_y]]
        map_areas[area[AREA.c.area_id]] = area_details
    LOG.info('Loaded the area details')


def pixel_in_block(raw_x, raw_y, block_x, block_y):
    """
    Is the pixel inside the block we're processing

    :param raw_x:
    :param raw_y:
    :param block_x:
    :param block_y:
    :return:
    >>> pixel_in_block(0, 0, 0, 0)
    True
    >>> pixel_in_block(0, 0, 0, 1)
    False
    >>> pixel_in_block(0,0,1,0)
    False
    >>> pixel_in_block(1023,0,0,0)
    True
    >>> pixel_in_block(1024,0,0,0)
    False
    >>> pixel_in_block(1024,0,1,0)
    True
    >>> pixel_in_block(0,1024,0,1)
    True
    >>> pixel_in_block(1024,1024,0,1)
    False
    >>> pixel_in_block(1024,1024,1,0)
    False
    """
    block_top_x = block_x * MAX_X_Y_BLOCK
    block_top_y = block_y * MAX_X_Y_BLOCK
    block_bottom_x = block_top_x + MAX_X_Y_BLOCK - 1
    block_bottom_y = block_top_y + MAX_X_Y_BLOCK - 1
    return block_top_x <= raw_x <= block_bottom_x and block_top_y <= raw_y <= block_bottom_y


def store_pixels(connection, galaxy_file_name, group, dimension_x, dimension_y, number_filters, area_total, rad_area_total, int_flux_area_total, galaxy_id, map_parameter_name):
    """
    Store the pixel data
    """
    LOG.info('Storing the pixel data for {0} - {1} areas to process'.format(galaxy_file_name, area_total))
    group.attrs['PIXELS_MAX_X_Y_BLOCK'] = MAX_X_Y_BLOCK
    group.attrs['PIXELS_DIM3_F_MU_SFH'] = INDEX_F_MU_SFH
    group.attrs['PIXELS_DIM3_F_MU_IR'] = INDEX_F_MU_IR
    group.attrs['PIXELS_DIM3_MU_PARAMETER'] = INDEX_MU_PARAMETER
    group.attrs['PIXELS_DIM3_TAU_V'] = INDEX_TAU_V
    group.attrs['PIXELS_DIM3_SSFR_0_1GYR'] = INDEX_SSFR_0_1GYR
    group.attrs['PIXELS_DIM3_M_STARS'] = INDEX_M_STARS
    group.attrs['PIXELS_DIM3_L_DUST'] = INDEX_L_DUST
    group.attrs['PIXELS_DIM3_T_C_ISM'] = INDEX_T_C_ISM
    group.attrs['PIXELS_DIM3_T_W_BC'] = INDEX_T_W_BC
    group.attrs['PIXELS_DIM3_XI_C_TOT'] = INDEX_XI_C_TOT
    group.attrs['PIXELS_DIM3_XI_PAH_TOT'] = INDEX_XI_PAH_TOT
    group.attrs['PIXELS_DIM3_XI_MIR_TOT'] = INDEX_XI_MIR_TOT
    group.attrs['PIXELS_DIM3_XI_W_TOT'] = INDEX_XI_W_TOT
    group.attrs['PIXELS_DIM3_TAU_V_ISM'] = INDEX_TAU_V_ISM
    group.attrs['PIXELS_DIM3_M_DUST'] = INDEX_M_DUST
    group.attrs['PIXELS_DIM3_SFR_0_1GYR'] = INDEX_SFR_0_1GYR

    group.attrs['PIXELS_DIM4_BEST_FIT'] = INDEX_BEST_FIT
    group.attrs['PIXELS_DIM4_PERCENTILE_50'] = INDEX_PERCENTILE_50
    group.attrs['PIXELS_DIM4_HIGHEST_PROB_BIN'] = INDEX_HIGHEST_PROB_BIN
    group.attrs['PIXELS_DIM4_PERCENTILE_2_5'] = INDEX_PERCENTILE_2_5
    group.attrs['PIXELS_DIM4_PERCENTILE_16'] = INDEX_PERCENTILE_16
    group.attrs['PIXELS_DIM4_PERCENTILE_84'] = INDEX_PERCENTILE_84
    group.attrs['PIXELS_DIM4_PERCENTILE_97_5'] = INDEX_PERCENTILE_97_5

    histogram_list = []
    keys = []
    map_areas = {}
    pixel_count = 0
    pixel_type = 0
    rad_pixel_count = 0
    int_flux_pixel_count = 0
    
    area_count = 0

    special_group = None

    if rad_area_total > 0:
        # We have radial pixels to process

        # Get the number of radial pixels for this galaxy
        rad_pixels = connection.execute(select([func.count(PIXEL_RESULT.c.pxresult_id)]).where(PIXEL_RESULT.c.galaxy_id == galaxy_id).where(PIXEL_RESULT.c.x == -2)).first()[0]

        rad_data = numpy.empty((1, rad_pixels, NUMBER_PARAMETERS, NUMBER_IMAGES), dtype=numpy.float)
        rad_data = rad_data.fill(numpy.NaN)
    
        if special_group is None:
            special_group = group.create_group('special_pixels')

        rad_pixel_details = special_group.create_dataset(
            'pixel_details_rad',
            (1,rad_pixels,),
            dtype=data_type_pixel,
            compression='gzip')
        rad_pixel_parameters = special_group.create_dataset(
            'pixel_parameters_rad',
            (1,rad_pixels, NUMBER_PARAMETERS),
            dtype=data_type_pixel_parameter,
            compression='gzip')

        # We can't use the z dimension as blank layers show up in the SED file
        rad_pixel_filter = special_group.create_dataset(
            'pixel_filters_rad',
            (1,rad_pixels, number_filters),
            dtype=data_type_pixel_filter,
            compression='gzip')
        rad_pixel_histograms_grid = special_group.create_dataset(
            'pixel_histograms_rad',
            (1,rad_pixels, NUMBER_PARAMETERS),
            dtype=data_type_block_details,
            compression='gzip')
            
        rad_histogram_group = special_group.create_group('rad_histrogram')
        rad_histogram_data = rad_histogram_group.create_dataset('histogram', (rad_pixels,), dtype=data_type_pixel_histogram, compression='gzip')

        rad_histogram_block_id = 1
        rad_histogram_block_index = 0
        rad_histogram_list = []

    if int_flux_area_total > 0:
        # We have an integrated flux area to process

        if special_group is None:
            special_group = group.create_group('special_pixels')

        int_flux_data = numpy.empty((1, 1, NUMBER_PARAMETERS, NUMBER_IMAGES), dtype=numpy.float)
        int_flux_data = int_flux_data.fill(numpy.NaN)

        int_flux_pixel_details = special_group.create_dataset(
            'pixel_details_int_flux',
            (1,1,),
            dtype=data_type_pixel,
            compression='gzip')
        int_flux_pixel_parameters = special_group.create_dataset(
            'pixel_parameters_int_flux',
            (1,1, NUMBER_PARAMETERS),
            dtype=data_type_pixel_parameter,
            compression='gzip')

        # We can't use the z dimension as blank layers show up in the SED file
        int_flux_pixel_filter = special_group.create_dataset(
            'pixel_filters_int_flux',
            (1,1, number_filters),
            dtype=data_type_pixel_filter,
            compression='gzip')
        int_flux_pixel_histograms_grid = special_group.create_dataset(
            'pixel_histograms_int_flux',
            (1,1, NUMBER_PARAMETERS),
            dtype=data_type_block_details,
            compression='gzip')

        # A single pixel histogram?
        int_flux_histogram_group = special_group.create_group('int_flux_histrogram')
        int_flux_histogram_data = int_flux_histogram_group.create_dataset('histogram', (1,), dtype=data_type_pixel_histogram, compression='gzip')

        int_flux_histogram_block_id = 1
        int_flux_histogram_block_index = 0
        int_flux_histogram_list = []

    histogram_block_id = 1
    histogram_block_index = 0
    s3helper = S3Helper()
    bucket = s3helper.get_bucket(get_sed_files_bucket())

    # Load the area details and keys
    load_map_areas(connection, map_areas, galaxy_id)
    for key in bucket.list(prefix='{0}/'.format(galaxy_file_name)):
        # Ignore the key
        if key.key.endswith('/'):
            continue
        keys.append(key)

    histogram_group = group.create_group('histogram_blocks')
    histogram_data = histogram_group.create_dataset('block_1', (HISTOGRAM_BLOCK_SIZE,), dtype=data_type_pixel_histogram, compression='gzip')
    # At this point, the containers for all histograms have been built
    for block_x in get_chunks(dimension_x):  # Loop all pixels in the block.
        for block_y in get_chunks(dimension_y):
            LOG.info('block x = {0}, y = {1}'.format(block_x, block_y))

            if shutdown() is True:
                raise SystemExit

            LOG.info('Starting {0} : {1}.'.format(block_x, block_y))

            size_x = get_size(block_x, dimension_x)
            size_y = get_size(block_y, dimension_y)

            # Create the arrays for this block
            data = numpy.empty((size_x, size_y, NUMBER_PARAMETERS, NUMBER_IMAGES), dtype=numpy.float)
            data.fill(numpy.NaN)
            data_pixel_details = group.create_dataset(
                'pixel_details_{0}_{1}'.format(block_x, block_y),
                (size_x, size_y),
                dtype=data_type_pixel,
                compression='gzip')
            data_pixel_parameters = group.create_dataset(
                'pixel_parameters_{0}_{1}'.format(block_x, block_y),
                (size_x, size_y, NUMBER_PARAMETERS),
                dtype=data_type_pixel_parameter,
                compression='gzip')

            # We can't use the z dimension as blank layers show up in the SED file
            data_pixel_filter = group.create_dataset(
                'pixel_filters_{0}_{1}'.format(block_x, block_y),
                (size_x, size_y, number_filters),
                dtype=data_type_pixel_filter,
                compression='gzip')
            data_pixel_histograms_grid = group.create_dataset(
                'pixel_histograms_grid_{0}_{1}'.format(block_x, block_y),
                (size_x, size_y, NUMBER_PARAMETERS),
                dtype=data_type_block_details,
                compression='gzip')

            for key in keys:
                if shutdown() is True:
                    raise SystemExit

                if not area_intersects_block(connection, key.key, block_x, block_y, map_areas):
                    LOG.info('Skipping {0}'.format(key.key))
                    continue

                # Now process the file
                start_time = time.time()
                LOG.info('Processing file {0} / {1}'.format(key.key, len(keys)))
                temp_file = os.path.join(POGS_TMP, 'temp.sed')
                key.get_contents_to_filename(temp_file)

                if is_gzip(temp_file):
                    f = gzip.open(temp_file, "rb")
                else:
                    f = open(temp_file, "r")

                area_id = None
                pxresult_id = None
                pixel_type = 0  #0 for normal, 1 for int flux, 2 for radial
                line_number = 0
                percentiles_next = False
                histogram_next = False
                skynet_next1 = False
                skynet_next2 = False
                skip_this_pixel = False
                map_pixel_results = {}
                list_filters = []
                try:
                    for line in f:

                        line_number += 1

                        if line.startswith(" ####### "):
                            # Clear all the maps and stuff
                            map_pixel_results = {}
                            list_filters = []

                            # Split the line to extract the data
                            values = line.split()
                            point_name = values[1]
                            pxresult_id = point_name[3:].rstrip()
                            (raw_x, raw_y, area_id) = get_pixel_result(connection, pxresult_id)
                            LOG.info('rawx = {0} rawy = {1}'.format(raw_x, raw_y))
                            
                            if raw_x == -1:
                                # this pixel is for integrated flux
                                pixel_type = 1
                                LOG.info('Int flux')
                            elif raw_x == -2:
                                # this pixel is for radial 
                                pixel_type = 2
                                LOG.info('Radial pixel')
                            else:
                                # just a standard pixel
                                pixel_type = 0
                              
                            if pixel_type == 0:  # Only standard pixels are in blocks
                                # The pixel could be out of this block as the cutting up is not uniform
                                if pixel_in_block(raw_x, raw_y, block_x, block_y):
                                    # correct x & y for this block
                                    x = raw_x - (block_x * MAX_X_Y_BLOCK)
                                    y = raw_y - (block_y * MAX_X_Y_BLOCK)
                                    # TODO next line commented out
                                    #LOG.info('Processing pixel {0}:{1} or {2}:{3} - {4}:{5}'.format(raw_x, raw_y, x, y, block_x, block_y))
                                    line_number = 0
                                    percentiles_next = False
                                    histogram_next = False
                                    skynet_next1 = False
                                    skynet_next2 = False
                                    skip_this_pixel = True #todo skipping now
                                    pixel_count += 1
                                
                                else:
                                    # TODO next line commented out
                                    LOG.info('Skipping pixel {0}:{1} - {2}:{3}'.format(raw_x, raw_y, block_x, block_y))
                                    skip_this_pixel = True
                                    
                            else:  # Still need these set for non-standard pixels
                                x = 0
                                y = raw_y
                                line_number = 0
                                percentiles_next = False
                                histogram_next = False
                                skynet_next1 = False
                                skynet_next2 = False
                                skip_this_pixel = False
                                
                                if pixel_type == 1:
                                    int_flux_pixel_count += 1
                                elif pixel_type == 2:
                                    rad_pixel_count += 1
                                    
                        elif skip_this_pixel:
                            # Do nothing as we're skipping this pixel
                            pass
                        elif pxresult_id is not None:
                            if line_number == 2:
                                filter_names = line.split()
                                filter_layer = 0
                                for filter_name in filter_names:
                                    if filter_name != '#':
                                        
                                        if pixel_type == 0:
                                            data_pixel_filter.attrs[filter_name] = filter_layer
                                        elif pixel_type == 2:
                                            rad_pixel_filter.attrs[filter_name] = filter_layer
                                        elif pixel_type == 1:
                                            int_flux_pixel_filter.attrs[filter_name] = filter_layer
                                        filter_layer += 1 
                                            
                            elif line_number == 3:
                                values = line.split()
                                for value in values:
                                    list_filters.append([float(value)])

                            elif line_number == 4:
                                filter_layer = 0
                                values = line.split()
                                for value in values:
                                    filter_description = list_filters[filter_layer]
                                    filter_description.append(float(value))
                                    filter_layer += 1

                            elif line_number == 9:
                                values = line.split()
                                map_pixel_results['i_sfh'] = float(values[0])
                                map_pixel_results['i_ir'] = float(values[1])
                                map_pixel_results['chi2'] = float(values[2])
                                map_pixel_results['redshift'] = float(values[3])

                            elif line_number == 11:
                                values = line.split()

                                # Work out where this stuff needs to go.
                                if pixel_type == 0:
                                    data[x, y, INDEX_F_MU_SFH, INDEX_BEST_FIT] = float(values[0])
                                    data[x, y, INDEX_F_MU_IR, INDEX_BEST_FIT] = float(values[1])
                                    data[x, y, INDEX_MU_PARAMETER, INDEX_BEST_FIT] = float(values[2])
                                    data[x, y, INDEX_TAU_V, INDEX_BEST_FIT] = float(values[3])
                                    data[x, y, INDEX_SSFR_0_1GYR, INDEX_BEST_FIT] = float(values[4])
                                    data[x, y, INDEX_M_STARS, INDEX_BEST_FIT] = float(values[5])
                                    data[x, y, INDEX_L_DUST, INDEX_BEST_FIT] = float(values[6])
                                    data[x, y, INDEX_T_W_BC, INDEX_BEST_FIT] = float(values[7])
                                    data[x, y, INDEX_T_C_ISM, INDEX_BEST_FIT] = float(values[8])
                                    data[x, y, INDEX_XI_C_TOT, INDEX_BEST_FIT] = float(values[9])
                                    data[x, y, INDEX_XI_PAH_TOT, INDEX_BEST_FIT] = float(values[10])
                                    data[x, y, INDEX_XI_MIR_TOT, INDEX_BEST_FIT] = float(values[11])
                                    data[x, y, INDEX_XI_W_TOT, INDEX_BEST_FIT] = float(values[12])
                                    data[x, y, INDEX_TAU_V_ISM, INDEX_BEST_FIT] = float(values[13])
                                    data[x, y, INDEX_M_DUST, INDEX_BEST_FIT] = float(values[14])
                                    data[x, y, INDEX_SFR_0_1GYR, INDEX_BEST_FIT] = float(values[15])

                                elif pixel_type == 2:
                                    rad_data[x, y, INDEX_F_MU_SFH, INDEX_BEST_FIT] = float(values[0])
                                    rad_data[x, y, INDEX_F_MU_IR, INDEX_BEST_FIT] = float(values[1])
                                    rad_data[x, y, INDEX_MU_PARAMETER, INDEX_BEST_FIT] = float(values[2])
                                    rad_data[x, y, INDEX_TAU_V, INDEX_BEST_FIT] = float(values[3])
                                    rad_data[x, y, INDEX_SSFR_0_1GYR, INDEX_BEST_FIT] = float(values[4])
                                    rad_data[x, y, INDEX_M_STARS, INDEX_BEST_FIT] = float(values[5])
                                    rad_data[x, y, INDEX_L_DUST, INDEX_BEST_FIT] = float(values[6])
                                    rad_data[x, y, INDEX_T_W_BC, INDEX_BEST_FIT] = float(values[7])
                                    rad_data[x, y, INDEX_T_C_ISM, INDEX_BEST_FIT] = float(values[8])
                                    rad_data[x, y, INDEX_XI_C_TOT, INDEX_BEST_FIT] = float(values[9])
                                    rad_data[x, y, INDEX_XI_PAH_TOT, INDEX_BEST_FIT] = float(values[10])
                                    rad_data[x, y, INDEX_XI_MIR_TOT, INDEX_BEST_FIT] = float(values[11])
                                    rad_data[x, y, INDEX_XI_W_TOT, INDEX_BEST_FIT] = float(values[12])
                                    rad_data[x, y, INDEX_TAU_V_ISM, INDEX_BEST_FIT] = float(values[13])
                                    rad_data[x, y, INDEX_M_DUST, INDEX_BEST_FIT] = float(values[14])
                                    rad_data[x, y, INDEX_SFR_0_1GYR, INDEX_BEST_FIT] = float(values[15])

                                elif pixel_type == 1:
                                    int_flux_data[x, y, INDEX_F_MU_SFH, INDEX_BEST_FIT] = float(values[0])
                                    int_flux_data[x, y, INDEX_F_MU_IR, INDEX_BEST_FIT] = float(values[1])
                                    int_flux_data[x, y, INDEX_MU_PARAMETER, INDEX_BEST_FIT] = float(values[2])
                                    int_flux_data[x, y, INDEX_TAU_V, INDEX_BEST_FIT] = float(values[3])
                                    int_flux_data[x, y, INDEX_SSFR_0_1GYR, INDEX_BEST_FIT] = float(values[4])
                                    int_flux_data[x, y, INDEX_M_STARS, INDEX_BEST_FIT] = float(values[5])
                                    int_flux_data[x, y, INDEX_L_DUST, INDEX_BEST_FIT] = float(values[6])
                                    int_flux_data[x, y, INDEX_T_W_BC, INDEX_BEST_FIT] = float(values[7])
                                    int_flux_data[x, y, INDEX_T_C_ISM, INDEX_BEST_FIT] = float(values[8])
                                    int_flux_data[x, y, INDEX_XI_C_TOT, INDEX_BEST_FIT] = float(values[9])
                                    int_flux_data[x, y, INDEX_XI_PAH_TOT, INDEX_BEST_FIT] = float(values[10])
                                    int_flux_data[x, y, INDEX_XI_MIR_TOT, INDEX_BEST_FIT] = float(values[11])
                                    int_flux_data[x, y, INDEX_XI_W_TOT, INDEX_BEST_FIT] = float(values[12])
                                    int_flux_data[x, y, INDEX_TAU_V_ISM, INDEX_BEST_FIT] = float(values[13])
                                    int_flux_data[x, y, INDEX_M_DUST, INDEX_BEST_FIT] = float(values[14])
                                    int_flux_data[x, y, INDEX_SFR_0_1GYR, INDEX_BEST_FIT] = float(values[15])

                            elif line_number == 13:
                                filter_layer = 0
                                values = line.split()
                                for value in values:
                                    filter_description = list_filters[filter_layer]
                                    if filter_layer < number_filters:
                                        if pixel_type == 0:
                                            data_pixel_filter[x, y, filter_layer] = (
                                                filter_description[0],
                                                filter_description[1],
                                                float(value),
                                            )
                                        elif pixel_type == 2:
                                            rad_pixel_filter[x, y, filter_layer] = (
                                                filter_description[0],
                                                filter_description[1],
                                                float(value),
                                            )
                                        elif pixel_type == 1:
                                            int_flux_pixel_filter[x, y, filter_layer] = (
                                                filter_description[0],
                                                filter_description[1],
                                                float(value),
                                            )

                                        filter_layer += 1

                            elif line_number > 13:
                                if line.startswith("# ..."):
                                    parts = line.split('...')
                                    parameter_name = parts[1].strip()
                                    parameter_name_id = map_parameter_name[parameter_name]
                                    percentiles_next = False
                                    histogram_next = True
                                    skynet_next1 = False
                                    skynet_next2 = False

                                    if pixel_type == 0:
                                        histogram_list = []
                                    elif pixel_type == 2:
                                        rad_histogram_list = []
                                    elif pixel_type == 1:
                                        int_flux_histogram_list = []

                                elif line.startswith("#....percentiles of the PDF......"):
                                    percentiles_next = True
                                    histogram_next = False
                                    skynet_next1 = False
                                    skynet_next2 = False

                                    # Write out the histogram into a block for compression improvement
                                    if pixel_type == 0:
                                        data_pixel_histograms_grid[x, y, parameter_name_id - 1] = (histogram_block_id, histogram_block_index, len(histogram_list))
                                        for pixel_histogram_item in histogram_list:
                                            if histogram_block_index >= HISTOGRAM_BLOCK_SIZE:

                                                histogram_block_id += 1
                                                histogram_block_index = 0
                                                histogram_data = histogram_group.create_dataset(
                                                    'block_{0}'.format(histogram_block_id),
                                                    (HISTOGRAM_BLOCK_SIZE,),
                                                    dtype=data_type_pixel_histogram,
                                                    compression='gzip')

                                                LOG.info('Created new histogram block_{0}'.format(histogram_block_id))

                                            histogram_data[histogram_block_index] = (
                                                pixel_histogram_item[0],
                                                pixel_histogram_item[1],
                                            )

                                            histogram_block_index += 1

                                    elif pixel_type == 2:
                                        rad_pixel_histograms_grid[x, y, parameter_name_id - 1] = (rad_histogram_block_id, rad_histogram_block_index, len(rad_histogram_list))
                                        for rad_pixel_histogram_item in rad_histogram_list:
                                            rad_histogram_data[rad_histogram_block_index] = (
                                                rad_pixel_histogram_item[0],
                                                rad_pixel_histogram_item[1],
                                            )
                                    elif pixel_type == 1:
                                        int_flux_pixel_histograms_grid[x, y, parameter_name_id - 1] = (int_flux_histogram_block_id, int_flux_histogram_block_index, len(int_flux_histogram_list))
                                        for int_flux_pixel_histogram_item in int_flux_histogram_list:
                                            int_flux_histogram_data[int_flux_histogram_block_index] = (
                                                int_flux_pixel_histogram_item[0],
                                                int_flux_pixel_histogram_item[1],
                                            )

                                elif line.startswith(" #...theSkyNet"):
                                    percentiles_next = False
                                    histogram_next = False
                                    skynet_next1 = True
                                    skynet_next2 = False
                                elif line.startswith("# theSkyNet2"):
                                    percentiles_next = False
                                    histogram_next = False
                                    skynet_next1 = False
                                    skynet_next2 = True
                                elif percentiles_next:
                                    values = line.split()
                                    z = parameter_name_id - 1

                                    place_to_load = None

                                    # Work out where this stuff needs to go.
                                    if pixel_type == 0:
                                        data[x, y, z, INDEX_PERCENTILE_2_5] = float(values[0])
                                        data[x, y, z, INDEX_PERCENTILE_16] = float(values[1])
                                        data[x, y, z, INDEX_PERCENTILE_50] = float(values[2])
                                        data[x, y, z, INDEX_PERCENTILE_84] = float(values[3])
                                        data[x, y, z, INDEX_PERCENTILE_97_5] = float(values[4])
                                    elif pixel_type == 2:

                                        rad_data[x, y, z, INDEX_PERCENTILE_2_5] = float(values[0])
                                        rad_data[x, y, z, INDEX_PERCENTILE_16] = float(values[1])
                                        rad_data[x, y, z, INDEX_PERCENTILE_50] = float(values[2])
                                        rad_data[x, y, z, INDEX_PERCENTILE_84] = float(values[3])
                                        rad_data[x, y, z, INDEX_PERCENTILE_97_5] = float(values[4])
                                    elif pixel_type == 1:

                                        int_flux_data[x, y, z, INDEX_PERCENTILE_2_5] = float(values[0])
                                        int_flux_data[x, y, z, INDEX_PERCENTILE_16] = float(values[1])
                                        int_flux_data[x, y, z, INDEX_PERCENTILE_50] = float(values[2])
                                        int_flux_data[x, y, z, INDEX_PERCENTILE_84] = float(values[3])
                                        int_flux_data[x, y, z, INDEX_PERCENTILE_97_5] = float(values[4])


                                    percentiles_next = False
                                elif histogram_next:
                                    values = line.split()
                                    hist_value = float(values[1])
                                    if hist_value > MIN_HIST_VALUE and not math.isnan(hist_value):
                                        if pixel_type == 0:
                                            histogram_list.append((float(values[0]), hist_value))
                                        elif pixel_type == 2:
                                            rad_histogram_list.append((float(values[0]), hist_value))
                                        elif pixel_type == 1:
                                            int_flux_histogram_list.append((float(values[0]), hist_value))
                                elif skynet_next1:
                                    values = line.split()

                                    # Work out where this stuff needs to go.
                                    if pixel_type == 0:
                                        data_pixel_details[x, y] = (
                                            pxresult_id,
                                            area_id,
                                            map_pixel_results['i_sfh'],
                                            map_pixel_results['i_ir'],
                                            map_pixel_results['chi2'],
                                            map_pixel_results['redshift'],
                                            float(values[0]),
                                            float(values[2]),
                                            float(values[3]),
                                            float(values[4]),
                                        )
                                    elif pixel_type == 2:
                                        rad_pixel_details[x, y] = (
                                            pxresult_id,
                                            area_id,
                                            map_pixel_results['i_sfh'],
                                            map_pixel_results['i_ir'],
                                            map_pixel_results['chi2'],
                                            map_pixel_results['redshift'],
                                            float(values[0]),
                                            float(values[2]),
                                            float(values[3]),
                                            float(values[4]),
                                        )
                                    elif pixel_type == 1:
                                        int_flux_pixel_details[x, y] = (
                                            pxresult_id,
                                            area_id,
                                            map_pixel_results['i_sfh'],
                                            map_pixel_results['i_ir'],
                                            map_pixel_results['chi2'],
                                            map_pixel_results['redshift'],
                                            float(values[0]),
                                            float(values[2]),
                                            float(values[3]),
                                            float(values[4]),
                                        )

                                    skynet_next1 = False
                                elif skynet_next2:
                                    # We have the highest bin probability values which require the parameter_id
                                    values = line.split()
                                    high_prob_bin = float(values[0]) if float(values[0]) is not None else numpy.NaN
                                    first_prob_bin = float(values[1]) if float(values[1]) is not None else numpy.NaN
                                    last_prob_bin = float(values[2]) if float(values[2]) is not None else numpy.NaN
                                    bin_step = float(values[3]) if float(values[3]) is not None else numpy.NaN
                                    z = parameter_name_id - 1

                                    # Work out where this stuff needs to go.
                                    if pixel_type == 0:
                                        data[x, y, z, INDEX_HIGHEST_PROB_BIN] = high_prob_bin
                                        data_pixel_parameters[x, y, z] = (
                                            first_prob_bin,
                                            last_prob_bin,
                                            bin_step,
                                        )
                                    elif pixel_type == 2:
                                        rad_data[x, y, z, INDEX_HIGHEST_PROB_BIN] = high_prob_bin
                                        rad_pixel_parameters[x, y, z] = (
                                            first_prob_bin,
                                            last_prob_bin,
                                            bin_step,
                                        )
                                    elif pixel_type == 1:
                                        int_flux_data[x, y, z, INDEX_HIGHEST_PROB_BIN] = high_prob_bin
                                        int_flux_pixel_parameters[x, y, z] = (
                                            first_prob_bin,
                                            last_prob_bin,
                                            bin_step,
                                        )

                                    skynet_next2 = False

                except IOError:
                    LOG.error('IOError after {0} lines'.format(line_number))
                finally:
                    f.close()

                area_count += 1
                LOG.info('{0:0.3f} seconds for file {1}. {2} of {3} areas.'.format(time.time() - start_time, key.key, area_count, area_total))

            if rad_pixel_count > 0:
                special_group.create_dataset('pixels', data=rad_data, compression='gzip')
            if int_flux_pixel_count >0:
                special_group.create_dataset('pixels', data=int_flux_data, compression='gzip')

            group.create_dataset('pixels_{0}_{1}'.format(block_x, block_y), data=data, compression='gzip')

    LOG.info('histogram_blocks: {0}, x_blocks: {1}, y_blocks: {2}'.format(histogram_block_id, block_x, block_y))

    return pixel_count + int_flux_pixel_count + rad_pixel_count


def is_gzip(file_to_check):
    """
    Test if the file is a gzip file by opening it and reading the magic number

    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/NGC1209__wu719_0_0.gzip')
    True
    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/NGC1209__wu719_1_0.gzip')
    True
    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/NGC1209__wu719_0_0')
    False
    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/NGC1209__wu719_1_0')
    False
    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/empty')
    False
    """
    result = False
    f = open(file_to_check, "rb")
    try:
        magic = f.read(2)
        if len(magic) == 2:
            method = ord(f.read(1))

            result = magic == '\037\213' and method == 8

    except IOError:
        pass
    finally:
        f.close()
    return result


def get_pixel_result(connection, pxresult_id):
    """
    Get the pixel result row from the database
    """
    pixel_result = connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.pxresult_id == pxresult_id)).first()

    if pixel_result is None:
        LOG.error("Pixel Result row not found for pxresult_id = {0}".format(pxresult_id))
        raise ValueError
    else:
        # Record the area_id
        area_id = pixel_result[PIXEL_RESULT.c.area_id]
        x = pixel_result[PIXEL_RESULT.c.x]
        y = pixel_result[PIXEL_RESULT.c.y]
        return x, y, area_id


def get_number_filters(connection, run_id):
    """
    Get the number of filters used in this run

    :param connection:
    :param run_id:
    :return:
    """
    count = connection.execute(select([func.count(RUN_FILTER.c.run_filter_id)]).where(RUN_FILTER.c.run_id == run_id)).first()[0]
    return count


def archive_to_hdf5(connection, modulus, remainder):
    """
    Archive data to an HDF5 file

    :param connection:
    :return:
    """
    # Load the parameter name map
    map_parameter_name = {}
    for parameter_name in connection.execute(select([PARAMETER_NAME])):
        map_parameter_name[parameter_name[PARAMETER_NAME.c.name]] = parameter_name[PARAMETER_NAME.c.parameter_name_id]

    # Look in the database for the galaxies
    galaxy_ids = []
    for galaxy in connection.execute(select([GALAXY]).where(GALAXY.c.status_id == PROCESSED).order_by(GALAXY.c.galaxy_id)):
        if modulus is None or int(galaxy[GALAXY.c.galaxy_id]) % modulus == remainder:
            galaxy_ids.append(galaxy[GALAXY.c.galaxy_id])

    for galaxy_id_str in galaxy_ids[:500]:

        if shutdown() is True:
            raise SystemExit

        start_time = time.time()

        galaxy_id1 = int(galaxy_id_str)
        galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id1)).first()
        if galaxy is None:
            LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
        else:
            LOG.info('Archiving Galaxy with galaxy_id of %d - %s', galaxy_id1, galaxy[GALAXY.c.name])

            # Copy the galaxy details
            galaxy_file_name = get_galaxy_file_name(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id])
            filename = os.path.join(HDF5_OUTPUT_DIRECTORY, '{0}.hdf5'.format(galaxy_file_name))

            h5_file = h5py.File(filename, 'w')

            # Build the groups
            galaxy_group = h5_file.create_group('galaxy')
            area_group = galaxy_group.create_group('area')
            pixel_group = galaxy_group.create_group('pixel')

            # Write the galaxy data
            galaxy_group.attrs['galaxy_id'] = galaxy[GALAXY.c.galaxy_id]
            galaxy_group.attrs['run_id'] = galaxy[GALAXY.c.run_id]
            galaxy_group.attrs['name'] = galaxy[GALAXY.c.name]
            galaxy_group.attrs['dimension_x'] = galaxy[GALAXY.c.dimension_x]
            galaxy_group.attrs['dimension_y'] = galaxy[GALAXY.c.dimension_y]
            galaxy_group.attrs['dimension_z'] = galaxy[GALAXY.c.dimension_z]
            galaxy_group.attrs['redshift'] = float(galaxy[GALAXY.c.redshift])
            galaxy_group.attrs['create_time'] = str(galaxy[GALAXY.c.create_time])
            galaxy_group.attrs['image_time'] = str(galaxy[GALAXY.c.image_time])
            galaxy_group.attrs['galaxy_type'] = galaxy[GALAXY.c.galaxy_type]
            galaxy_group.attrs['ra_cent'] = galaxy[GALAXY.c.ra_cent]
            galaxy_group.attrs['dec_cent'] = galaxy[GALAXY.c.dec_cent]
            galaxy_group.attrs['sigma'] = float(galaxy[GALAXY.c.sigma])
            galaxy_group.attrs['pixel_count'] = galaxy[GALAXY.c.pixel_count]
            galaxy_group.attrs['pixels_processed'] = galaxy[GALAXY.c.pixels_processed]
            galaxy_group.attrs['output_format'] = OUTPUT_FORMAT_1_04

            galaxy_id_aws = galaxy[GALAXY.c.galaxy_id]

            # Store the data associated with the galaxy
            store_fits_header(connection, galaxy_id_aws, galaxy_group)
            store_image_filters(connection, galaxy_id_aws, galaxy_group)

            # Store the data associated with the areas
            area_count, rad_area_count, int_flux_count = store_area(connection, galaxy_id_aws, area_group)
            LOG.info('Stored {0} normal areas, {1} integrated flux areas, {2} radial areas'.format(area_count, rad_area_count, int_flux_count))
            store_area_user(connection, galaxy_id_aws, area_group)
            h5_file.flush()

            number_filters = get_number_filters(connection, galaxy[GALAXY.c.run_id])

            # Store the values associated with a pixel
            pixel_count = store_pixels(connection,
                                       galaxy_file_name,
                                       pixel_group,
                                       galaxy[GALAXY.c.dimension_x],
                                       galaxy[GALAXY.c.dimension_y],
                                       number_filters,
                                       area_count, rad_area_count, int_flux_count,  # Now send through the number of other areas
                                       galaxy[GALAXY.c.galaxy_id],
                                       map_parameter_name)

            # Flush the HDF5 data to disk
            h5_file.flush()
            h5_file.close()

            # Move the file
            to_store = os.path.join(HDF5_OUTPUT_DIRECTORY, 'to_store')
            LOG.info('Moving the file %s to %s', filename, to_store)
            if not os.path.exists(to_store):
                os.makedirs(to_store)

            # Sometimes the file can exist so remove it
            old_filename = os.path.join(to_store, '{0}.hdf5'.format(galaxy_file_name))
            LOG.info('Checking for old file %s', old_filename)
            if os.path.exists(old_filename):
                LOG.info('Removing old file %s', old_filename)
                os.remove(old_filename)

            shutil.move(filename, to_store)

            connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy_id1).values(status_id=ARCHIVED, status_time=datetime.datetime.now()))

            end_time = time.time()
            LOG.info('Galaxy with galaxy_id of %d was archived.', galaxy_id1)
            LOG.info('Copied %d areas %d pixels.', area_count, pixel_count)
            total_time = end_time - start_time
            LOG.info('Total time %d mins %.1f secs', int(total_time / 60), total_time % 60)
