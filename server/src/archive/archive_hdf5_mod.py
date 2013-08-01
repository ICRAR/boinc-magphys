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
Module used to write data to an HDF5 file
"""
import gzip
import h5py
import math
import numpy
import os
import time
from utils.logging_helper import config_logger
from sqlalchemy.sql.expression import select, func
from config import MIN_HIST_VALUE
from database.database_support_core import FITS_HEADER, AREA, IMAGE_FILTERS_USED, AREA_USER, PIXEL_RESULT
from utils.name_builder import get_files_bucket
from utils.s3_helper import S3Helper

LOG = config_logger(__name__)

OUTPUT_FORMAT_1_00 = 'Version 1.00'
OUTPUT_FORMAT_1_01 = 'Version 1.01'
OUTPUT_FORMAT_1_02 = 'Version 1.02'

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
BLOCK_SIZE = 1000000

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
    count = connection.execute(select([func.count(AREA.c.area_id)]).where(AREA.c.galaxy_id == galaxy_id)).first()[0]
    data = numpy.zeros(count, dtype=data_type_area)
    count = 0
    for area in connection.execute(select([AREA]).where(AREA.c.galaxy_id == galaxy_id).order_by(AREA.c.area_id)):
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
    group.create_dataset('area', data=data, compression='gzip')
    return count


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


def store_pixels(connection, galaxy_file_name, group, dimension_x, dimension_y, dimension_z, area_total, output_directory, map_parameter_name):
    """
    Store the pixel data
    """
    LOG.info('Storing the pixel data for {0} - {1} areas to process'.format(galaxy_file_name, area_total))
    data = numpy.empty((dimension_x, dimension_y, NUMBER_PARAMETERS, NUMBER_IMAGES), dtype=numpy.float)
    data.fill(numpy.NaN)
    data_pixel_details = group.create_dataset('pixel_details', (dimension_x, dimension_y), dtype=data_type_pixel, compression='gzip')
    data_pixel_parameters = group.create_dataset('pixel_parameters', (dimension_x, dimension_y, NUMBER_PARAMETERS), dtype=data_type_pixel_parameter, compression='gzip')
    data_pixel_filter = group.create_dataset('pixel_filters', (dimension_x, dimension_y, dimension_z), dtype=data_type_pixel_filter, compression='gzip')
    data_pixel_histograms_grid = group.create_dataset('pixel_histograms_grid', (dimension_x, dimension_y, NUMBER_PARAMETERS), dtype=data_type_block_details, compression='gzip')

    histogram_group = group.create_group('histogram_blocks')
    histogram_list = []
    pixel_count = 0
    area_count = 0
    block_id = 1
    block_index = 0
    histogram_data = histogram_group.create_dataset('block_1', (BLOCK_SIZE,), dtype=data_type_pixel_histogram, compression='gzip')

    s3helper = S3Helper()
    bucket = s3helper.get_bucket(get_files_bucket())
    for key in bucket.list(prefix='{0}/sed/'.format(galaxy_file_name)):
        # Ignore the key
        if key.key.endswith('/'):
            continue

        # Now process the file
        start_time = time.time()
        LOG.info('Processing file {0}'.format(key.key))
        temp_file = os.path.join(output_directory, 'temp.sed')
        key.get_contents_to_filename(temp_file)

        if is_gzip(temp_file):
            f = gzip.open(temp_file, "rb")
        else:
            f = open(temp_file, "r")

        area_id = None
        pxresult_id = None
        line_number = 0
        percentiles_next = False
        histogram_next = False
        skynet_next1 = False
        skynet_next2 = False
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
                    pointName = values[1]
                    pxresult_id = pointName[3:].rstrip()
                    (x, y, area_id) = get_pixel_result(connection, pxresult_id)
                    line_number = 0
                    percentiles_next = False
                    histogram_next = False
                    skynet_next1 = False
                    skynet_next2 = False
                    pixel_count += 1
                elif pxresult_id is not None:
                    if line_number == 2:
                        filter_names = line.split()
                        filter_layer = 0
                        for filter_name in filter_names:
                            if filter_name != '#':
                                data_pixel_filter.attrs[filter_name] = filter_layer
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
                    elif line_number == 13:
                        filter_layer = 0
                        values = line.split()
                        for value in values:
                            filter_description = list_filters[filter_layer]
                            if filter_layer < dimension_z:
                                data_pixel_filter[x, y, filter_layer] = (
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
                            histogram_list = []
                        elif line.startswith("#....percentiles of the PDF......"):
                            percentiles_next = True
                            histogram_next = False
                            skynet_next1 = False
                            skynet_next2 = False

                            # Write out the histogram into a block for compression improvement
                            data_pixel_histograms_grid[x, y, parameter_name_id - 1] = (block_id, block_index, len(histogram_list))
                            for pixel_histogram_item in histogram_list:
                                # Do we need a new block
                                if block_index >= BLOCK_SIZE:
                                    block_id += 1
                                    block_index = 0
                                    histogram_data = histogram_group.create_dataset('block_{0}'.format(block_id), (BLOCK_SIZE,), dtype=data_type_pixel_histogram, compression='gzip')

                                histogram_data[block_index] = (
                                    pixel_histogram_item[0],
                                    pixel_histogram_item[1],
                                )
                                block_index += 1
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
                            data[x, y, z, INDEX_PERCENTILE_2_5] = float(values[0])
                            data[x, y, z, INDEX_PERCENTILE_16] = float(values[1])
                            data[x, y, z, INDEX_PERCENTILE_50] = float(values[2])
                            data[x, y, z, INDEX_PERCENTILE_84] = float(values[3])
                            data[x, y, z, INDEX_PERCENTILE_97_5] = float(values[4])
                            percentiles_next = False
                        elif histogram_next:
                            values = line.split()
                            hist_value = float(values[1])
                            if hist_value > MIN_HIST_VALUE and not math.isnan(hist_value):
                                histogram_list.append((float(values[0]), hist_value))
                        elif skynet_next1:
                            values = line.split()
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
                            skynet_next1 = False
                        elif skynet_next2:
                            # We have the highest bin probability values which require the parameter_id
                            values = line.split()
                            high_prob_bin = float(values[0]) if float(values[0]) is not None else numpy.NaN
                            first_prob_bin = float(values[1]) if float(values[1]) is not None else numpy.NaN
                            last_prob_bin = float(values[2]) if float(values[2]) is not None else numpy.NaN
                            bin_step = float(values[3]) if float(values[3]) is not None else numpy.NaN
                            z = parameter_name_id - 1
                            data[x, y, z, INDEX_HIGHEST_PROB_BIN] = high_prob_bin
                            data_pixel_parameters[x, y, z] = (
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

    pixel_dataset = group.create_dataset('pixels', data=data, compression='gzip')
    pixel_dataset.attrs['DIM3_F_MU_SFH'] = INDEX_F_MU_SFH
    pixel_dataset.attrs['DIM3_F_MU_IR'] = INDEX_F_MU_IR
    pixel_dataset.attrs['DIM3_MU_PARAMETER'] = INDEX_MU_PARAMETER
    pixel_dataset.attrs['DIM3_TAU_V'] = INDEX_TAU_V
    pixel_dataset.attrs['DIM3_SSFR_0_1GYR'] = INDEX_SSFR_0_1GYR
    pixel_dataset.attrs['DIM3_M_STARS'] = INDEX_M_STARS
    pixel_dataset.attrs['DIM3_L_DUST'] = INDEX_L_DUST
    pixel_dataset.attrs['DIM3_T_C_ISM'] = INDEX_T_C_ISM
    pixel_dataset.attrs['DIM3_T_W_BC'] = INDEX_T_W_BC
    pixel_dataset.attrs['DIM3_XI_C_TOT'] = INDEX_XI_C_TOT
    pixel_dataset.attrs['DIM3_XI_PAH_TOT'] = INDEX_XI_PAH_TOT
    pixel_dataset.attrs['DIM3_XI_MIR_TOT'] = INDEX_XI_MIR_TOT
    pixel_dataset.attrs['DIM3_XI_W_TOT'] = INDEX_XI_W_TOT
    pixel_dataset.attrs['DIM3_TAU_V_ISM'] = INDEX_TAU_V_ISM
    pixel_dataset.attrs['DIM3_M_DUST'] = INDEX_M_DUST
    pixel_dataset.attrs['DIM3_SFR_0_1GYR'] = INDEX_SFR_0_1GYR

    pixel_dataset.attrs['DIM4_BEST_FIT'] = INDEX_BEST_FIT
    pixel_dataset.attrs['DIM4_PERCENTILE_50'] = INDEX_PERCENTILE_50
    pixel_dataset.attrs['DIM4_HIGHEST_PROB_BIN'] = INDEX_HIGHEST_PROB_BIN
    pixel_dataset.attrs['DIM4_PERCENTILE_2_5'] = INDEX_PERCENTILE_2_5
    pixel_dataset.attrs['DIM4_PERCENTILE_16'] = INDEX_PERCENTILE_16
    pixel_dataset.attrs['DIM4_PERCENTILE_84'] = INDEX_PERCENTILE_84
    pixel_dataset.attrs['DIM4_PERCENTILE_97_5'] = INDEX_PERCENTILE_97_5

    LOG.info('Created {0} blocks'.format(block_id))

    return pixel_count


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
