#! /usr/bin/env python2.7
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
Compare the values in the database to those in the HDF5 file
"""

from __future__ import print_function
import os
import sys

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../../boinc/py')))

import argparse
import h5py
import time
import math
import numpy
from utils.logging_helper import config_logger
from archive.archive_hdf5_mod import INDEX_F_MU_SFH, INDEX_BEST_FIT, INDEX_F_MU_IR, INDEX_MU_PARAMETER, INDEX_TAU_V, INDEX_SSFR_0_1GYR, INDEX_M_STARS, INDEX_L_DUST, INDEX_T_C_ISM, INDEX_T_W_BC, INDEX_XI_C_TOT, INDEX_XI_PAH_TOT, INDEX_XI_MIR_TOT, INDEX_XI_W_TOT, INDEX_TAU_V_ISM, INDEX_M_DUST, INDEX_SFR_0_1GYR, INDEX_PERCENTILE_50, INDEX_HIGHEST_PROB_BIN, INDEX_PERCENTILE_2_5, INDEX_PERCENTILE_16, INDEX_PERCENTILE_84, INDEX_PERCENTILE_97_5
from config import DB_LOGIN
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from database.database_support_core import GALAXY, PIXEL_RESULT, PIXEL_FILTER, FITS_HEADER, IMAGE_FILTERS_USED, AREA, AREA_USER, PIXEL_PARAMETER, PIXEL_HISTOGRAM
from utils.readable_dir import ReadableDir

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))

parser = argparse.ArgumentParser('Check a Galaxy by galaxy_id')
parser.add_argument('-o','--output_dir', action=ReadableDir, nargs=1, help='where the HDF5 files have been written')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id or 4-30 if you need a range')
args = vars(parser.parse_args())

OUTPUT_DIRECTORY = args['output_dir']
OUTPUT_FORMAT = 'Version 1.00'

# Connect to the two databases
engine_aws = create_engine(DB_LOGIN)
connection = engine_aws.connect()
error_count = 0

def compare(param1, param2, tag1, tag2 = None, tag3 = None, tag4 = None, tag5 = None):
    """
    Compare two results to make sure they are the same
    """
    global error_count
    if param1 is None:
        math_isnan_param1 = True
    elif isinstance(param1, float):
        math_isnan_param1 = math.isnan(param1)
    else:
        math_isnan_param1 = False

    if param2 is None:
        math_isnan_param2 = True
    elif isinstance(param1, float):
        math_isnan_param2 = math.isnan(param2) or param2 is None
    else:
        math_isnan_param2 = False

    if math_isnan_param1 and math_isnan_param2:
        # The same
        pass

    elif param1 != param2:
        if tag2 is not None and tag3 is not None and tag4 is not None and tag5 is not None:
            tag = '{0} {1} {2} {3} - {4}'.format(tag1, tag2, tag3, tag4, tag5)
        elif tag2 is not None and tag3 is not None and tag4 is not None:
            tag = '{0} {1} {2} - {3}'.format(tag1, tag2, tag3, tag4)
        elif tag2 is not None and tag3 is not None:
            tag = '{0} {1} - {2}'.format(tag1, tag2, tag3)
        else:
            tag = tag1
        LOG.warning('{0} : {1} != {2}'.format(tag, param1, param2))
        error_count += 1

def check_galaxy_attributes(galaxy):
    """
    Check the galaxy attributes
    """
    LOG.info('Checking the galaxy attributes')
    compare(galaxy_group.attrs['galaxy_id']        , galaxy[GALAXY.c.galaxy_id]       , 'galaxy_id'          )
    compare(galaxy_group.attrs['run_id']           , galaxy[GALAXY.c.run_id]          , 'run_id'             )
    compare(galaxy_group.attrs['name']             , galaxy[GALAXY.c.name]            , 'name'               )
    compare(galaxy_group.attrs['dimension_x']      , galaxy[GALAXY.c.dimension_x]     , 'dimension_x'        )
    compare(galaxy_group.attrs['dimension_y']      , galaxy[GALAXY.c.dimension_y]     , 'dimension_y'        )
    compare(galaxy_group.attrs['dimension_z']      , galaxy[GALAXY.c.dimension_z]     , 'dimension_z'        )
    compare(galaxy_group.attrs['redshift']         , float(galaxy[GALAXY.c.redshift]) , 'redshift'           )
    compare(galaxy_group.attrs['create_time']      , str(galaxy[GALAXY.c.create_time]), 'create_time'        )
    compare(galaxy_group.attrs['image_time']       , str(galaxy[GALAXY.c.image_time]) , 'image_time'         )
    compare(galaxy_group.attrs['version_number']   , galaxy[GALAXY.c.version_number]  , 'version_number'     )
    compare(galaxy_group.attrs['current']          , galaxy[GALAXY.c.current]         , 'current'            )
    compare(galaxy_group.attrs['galaxy_type']      , galaxy[GALAXY.c.galaxy_type]     , 'galaxy_type'        )
    compare(galaxy_group.attrs['ra_cent']          , galaxy[GALAXY.c.ra_cent]         , 'ra_cent'            )
    compare(galaxy_group.attrs['dec_cent']         , galaxy[GALAXY.c.dec_cent]        , 'dec_cent'           )
    compare(galaxy_group.attrs['sigma']            , float(galaxy[GALAXY.c.sigma])    , 'sigma'              )
    compare(galaxy_group.attrs['pixel_count']      , galaxy[GALAXY.c.pixel_count]     , 'pixel_count'        )
    compare(galaxy_group.attrs['pixels_processed'] , galaxy[GALAXY.c.pixels_processed], 'pixels_processed'   )
    compare(galaxy_group.attrs['output_format']    , OUTPUT_FORMAT                    , 'output_format'      )

def check_fits_header(galaxy_id, galaxy_group):
    """
    Check the fits header
    """
    LOG.info('Checking the fits header')
    data = galaxy_group['fits_header']
    count = 0
    for fits_header in connection.execute(select([FITS_HEADER]).where(FITS_HEADER.c.galaxy_id == galaxy_id).order_by(FITS_HEADER.c.fitsheader_id)):
        compare(data[count][0], fits_header[FITS_HEADER.c.keyword], 'Fits Header', count, 'keyword')
        compare(data[count][1], fits_header[FITS_HEADER.c.value]  , 'Fits Header', count, 'value')
        count += 1

def check_image_filter(galaxy_id, galaxy_group):
    """
    Check the image filters
    """
    LOG.info('Checking the image filters')
    data = galaxy_group['image_filters']
    count = 0
    for image_filters_used in connection.execute(select([IMAGE_FILTERS_USED]).where(IMAGE_FILTERS_USED.c.galaxy_id == galaxy_id).order_by(IMAGE_FILTERS_USED.c.image_filters_used_id)):
        compare(data[count][0], image_filters_used[IMAGE_FILTERS_USED.c.image_number]   , 'Image Filter', count, 'image_number')
        compare(data[count][1], image_filters_used[IMAGE_FILTERS_USED.c.filter_id_red]  , 'Image Filter', count, 'filter_id_red')
        compare(data[count][2], image_filters_used[IMAGE_FILTERS_USED.c.filter_id_green], 'Image Filter', count, 'filter_id_green')
        compare(data[count][3], image_filters_used[IMAGE_FILTERS_USED.c.filter_id_blue] , 'Image Filter', count, 'filter_id_blue')
        count += 1


def check_area(galaxy_id, area_group):
    """
    Check the areas
    """
    LOG.info('Checking the areas')
    data = area_group['area']
    count = 0
    for area in connection.execute(select([AREA]).where(AREA.c.galaxy_id == galaxy_id).order_by(AREA.c.area_id)):
        compare(data[count][0], area[AREA.c.area_id]         , 'Area', count, 'area_id')
        compare(data[count][1], area[AREA.c.top_x]           , 'Area', count, 'top_x')
        compare(data[count][2], area[AREA.c.top_y]           , 'Area', count, 'top_y')
        compare(data[count][3], area[AREA.c.bottom_x]        , 'Area', count, 'bottom_x')
        compare(data[count][4], area[AREA.c.bottom_y]        , 'Area', count, 'bottom_y')
        compare(data[count][5], area[AREA.c.workunit_id]     , 'Area', count, 'workunit_id')
        compare(data[count][6], str(area[AREA.c.update_time]), 'Area', count, 'update_time')
        count += 1


def check_area_user(galaxy_id, area_group):
    """
    Check the area user
    """
    data = area_group['area_user']
    count = 0
    for area_user in connection.execute(select([AREA_USER], from_obj=AREA_USER.join(AREA)).where(AREA.c.galaxy_id == galaxy_id).order_by(AREA_USER.c.areauser_id)):
        compare(data[count][0], area_user[AREA_USER.c.area_id]         , 'Area User', count, 'area_id')
        compare(data[count][1], area_user[AREA_USER.c.userid]          , 'Area User', count, 'userid')
        compare(data[count][2], str(area_user[AREA_USER.c.create_time]), 'Area User', count, 'create_time')
        count += 1


def compare_region(hdf5_data, start_number, end_number):
    """
    Compare the regions
    """
    pass


def check_pixel(galaxy_id, pixel_group, pixel_count):
    """
    Check the pixels
    """
    LOG.info('Checking the pixels')
    data = pixel_group['pixels']
    data_pixel_details = pixel_group['pixel_details']
    data_pixel_parameters = pixel_group['pixel_parameters']
    data_pixel_filter = pixel_group['pixel_filters']
    data_pixel_histograms_list = pixel_group['pixel_histograms_list']
    data_pixel_histograms_grid = pixel_group['pixel_histograms_grid']

    count = 0
    pixel_histogram_count = 0
    for pixel_result in connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.galaxy_id == galaxy_id)):
        count += 1
        if count % 500 == 0:
            LOG.info('Processed {0} of {1}'.format(count, pixel_count))

        pxresult_id = pixel_result[PIXEL_RESULT.c.pxresult_id]
        x = pixel_result[PIXEL_RESULT.c.x]
        y = pixel_result[PIXEL_RESULT.c.y]
        compare(data[x, y, INDEX_F_MU_SFH    , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.fmu_sfh]   , 'Pixel', x, y, INDEX_BEST_FIT, 'fmu_sfh')
        compare(data[x, y, INDEX_F_MU_IR     , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.fmu_ir]    , 'Pixel', x, y, INDEX_BEST_FIT, 'fmu_ir')
        compare(data[x, y, INDEX_MU_PARAMETER, INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.mu]        , 'Pixel', x, y, INDEX_BEST_FIT, 'mu')
        compare(data[x, y, INDEX_TAU_V       , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.tauv]      , 'Pixel', x, y, INDEX_BEST_FIT, 'tauv')
        compare(data[x, y, INDEX_SSFR_0_1GYR , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.s_sfr]     , 'Pixel', x, y, INDEX_BEST_FIT, 's_sfr')
        compare(data[x, y, INDEX_M_STARS     , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.m]         , 'Pixel', x, y, INDEX_BEST_FIT, 'm')
        compare(data[x, y, INDEX_L_DUST      , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.ldust]     , 'Pixel', x, y, INDEX_BEST_FIT, 'ldust')
        compare(data[x, y, INDEX_T_C_ISM     , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.t_c_ism]   , 'Pixel', x, y, INDEX_BEST_FIT, 't_c_ism')
        compare(data[x, y, INDEX_T_W_BC      , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.t_w_bc]    , 'Pixel', x, y, INDEX_BEST_FIT, 't_w_bc')
        compare(data[x, y, INDEX_XI_C_TOT    , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.xi_c_tot]  , 'Pixel', x, y, INDEX_BEST_FIT, 'xi_c_tot')
        compare(data[x, y, INDEX_XI_PAH_TOT  , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.xi_pah_tot], 'Pixel', x, y, INDEX_BEST_FIT, 'xi_pah_tot')
        compare(data[x, y, INDEX_XI_MIR_TOT  , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.xi_mir_tot], 'Pixel', x, y, INDEX_BEST_FIT, 'xi_mir_tot')
        compare(data[x, y, INDEX_XI_W_TOT    , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.x_w_tot]   , 'Pixel', x, y, INDEX_BEST_FIT, 'x_w_tot')
        compare(data[x, y, INDEX_TAU_V_ISM   , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.tvism]     , 'Pixel', x, y, INDEX_BEST_FIT, 'tvism')
        compare(data[x, y, INDEX_M_DUST      , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.mdust]     , 'Pixel', x, y, INDEX_BEST_FIT, 'mdust')
        compare(data[x, y, INDEX_SFR_0_1GYR  , INDEX_BEST_FIT], pixel_result[PIXEL_RESULT.c.sfr]       , 'Pixel', x, y, INDEX_BEST_FIT, 'sfr')

        compare(data_pixel_details[x, y][0], pxresult_id                          , 'Pixel Details', x, y, 'pxresult_id')
        compare(data_pixel_details[x, y][1], pixel_result[PIXEL_RESULT.c.area_id] , 'Pixel_Details', x, y, 'area_id')
        compare(data_pixel_details[x, y][2], pixel_result[PIXEL_RESULT.c.i_sfh]   , 'Pixel_Details', x, y, 'i_sfh')
        compare(data_pixel_details[x, y][3], pixel_result[PIXEL_RESULT.c.i_ir]    , 'Pixel_Details', x, y, 'i_ir')
        compare(data_pixel_details[x, y][4], pixel_result[PIXEL_RESULT.c.chi2]    , 'Pixel_Details', x, y, 'chi2')
        compare(data_pixel_details[x, y][5], pixel_result[PIXEL_RESULT.c.redshift], 'Pixel_Details', x, y, 'redshift')
        compare(data_pixel_details[x, y][6], pixel_result[PIXEL_RESULT.c.i_opt]   , 'Pixel_Details', x, y, 'i_opt')
        compare(data_pixel_details[x, y][7], pixel_result[PIXEL_RESULT.c.dmstar]  , 'Pixel_Details', x, y, 'dmstar')
        compare(data_pixel_details[x, y][8], pixel_result[PIXEL_RESULT.c.dfmu_aux], 'Pixel_Details', x, y, 'dfmu_aux')
        compare(data_pixel_details[x, y][9], pixel_result[PIXEL_RESULT.c.dz]      , 'Pixel_Details', x, y, 'dz')

        for pixel_parameter in connection.execute(select([PIXEL_PARAMETER]).where(PIXEL_PARAMETER.c.pxresult_id == pxresult_id).order_by(PIXEL_PARAMETER.c.pxparameter_id)):
            z = pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] - 1
            compare(data[x, y, z, INDEX_PERCENTILE_50]   , pixel_parameter[PIXEL_PARAMETER.c.percentile50]    , 'Pixel_Parameter', x, y, INDEX_PERCENTILE_50    , z)
            compare(data[x, y, z, INDEX_HIGHEST_PROB_BIN], pixel_parameter[PIXEL_PARAMETER.c.high_prob_bin] \
                        if pixel_parameter[PIXEL_PARAMETER.c.high_prob_bin] is not None else numpy.NaN        , 'Pixel_Parameter', x, y, INDEX_HIGHEST_PROB_BIN , z)
            compare(data[x, y, z, INDEX_PERCENTILE_2_5]  , pixel_parameter[PIXEL_PARAMETER.c.percentile2_5]   , 'Pixel_Parameter', x, y, INDEX_PERCENTILE_2_5   , z)
            compare(data[x, y, z, INDEX_PERCENTILE_16]   , pixel_parameter[PIXEL_PARAMETER.c.percentile16]    , 'Pixel_Parameter', x, y, INDEX_PERCENTILE_16    , z)
            compare(data[x, y, z, INDEX_PERCENTILE_84]   , pixel_parameter[PIXEL_PARAMETER.c.percentile84]    , 'Pixel_Parameter', x, y, INDEX_PERCENTILE_84    , z)
            compare(data[x, y, z, INDEX_PERCENTILE_97_5] , pixel_parameter[PIXEL_PARAMETER.c.percentile97_5]  , 'Pixel_Parameter', x, y, INDEX_PERCENTILE_97_5  , z)

            first_prob_bin = pixel_parameter[PIXEL_PARAMETER.c.first_prob_bin] if pixel_parameter[PIXEL_PARAMETER.c.first_prob_bin] is not None else numpy.NaN
            last_prob_bin = pixel_parameter[PIXEL_PARAMETER.c.last_prob_bin] if pixel_parameter[PIXEL_PARAMETER.c.last_prob_bin] is not None else numpy.NaN
            bin_step = pixel_parameter[PIXEL_PARAMETER.c.bin_step] if pixel_parameter[PIXEL_PARAMETER.c.bin_step] is not None else numpy.NaN

            compare(data_pixel_parameters[x, y, z][0], first_prob_bin, 'Pixel_Parameter', x, y, z, 'first_prob_bin')
            compare(data_pixel_parameters[x, y, z][1], last_prob_bin,  'Pixel_Parameter', x, y, z, 'last_prob_bin')
            compare(data_pixel_parameters[x, y, z][2], bin_step,       'Pixel_Parameter', x, y, z, 'bin_step')

            pixel_histogram_start = pixel_histogram_count
            for pixel_histogram in connection.execute(select([PIXEL_HISTOGRAM]).where(PIXEL_HISTOGRAM.c.pxparameter_id == pixel_parameter[PIXEL_PARAMETER.c.pxparameter_id]).order_by(PIXEL_HISTOGRAM.c.pxhistogram_id)):
                compare(data_pixel_histograms_list[pixel_histogram_count][0], pixel_histogram[PIXEL_HISTOGRAM.c.x_axis],     'Pixel_histogram', pixel_histogram_count, 'x_axis')
                compare(data_pixel_histograms_list[pixel_histogram_count][1], pixel_histogram[PIXEL_HISTOGRAM.c.hist_value], 'Pixel_histogram', pixel_histogram_count, 'hist_value')

                pixel_histogram_count += 1
            compare_region(data_pixel_histograms_grid[x, y, z], pixel_histogram_start, pixel_histogram_count)


        filter_layer = 0
        for pixel_filter in connection.execute(select([PIXEL_FILTER]).where(PIXEL_FILTER.c.pxresult_id == pxresult_id).order_by(PIXEL_FILTER.c.pxfilter_id)):
            compare(data_pixel_filter[x, y, filter_layer][0], pixel_filter[PIXEL_FILTER.c.observed_flux]            , 'Pixel_Filter', x, y, filter_layer, 'observed_flux')
            compare(data_pixel_filter[x, y, filter_layer][1], pixel_filter[PIXEL_FILTER.c.observational_uncertainty], 'Pixel_Filter', x, y, filter_layer, 'observational_uncertainty')
            compare(data_pixel_filter[x, y, filter_layer][2], pixel_filter[PIXEL_FILTER.c.flux_bfm]                 , 'Pixel_Filter', x, y, filter_layer, 'flux_bfm')
            filter_layer += 1

try:
    # Get the galaxies to work on
    galaxy_ids = None
    if len(args['galaxy_id']) == 1 and args['galaxy_id'][0].find('-') > 1:
        list = args['galaxy_id'][0].split('-')
        LOG.info('Range from %s to %s', list[0], list[1])
        galaxy_ids = range(int(list[0]), int(list[1]) + 1)
    else:
        galaxy_ids = args['galaxy_id']

    for galaxy_id_str in galaxy_ids:
        start_time = time.time()
        area_count = 0
        pixel_count = 0

        galaxy_id1 = int(galaxy_id_str)
        galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id1)).first()
        if galaxy is None:
            LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
        else:
            LOG.info('Archiving Galaxy with galaxy_id of %d - %s', galaxy_id1, galaxy[GALAXY.c.name])

            # Copy the galaxy details
            if galaxy[GALAXY.c.version_number] == 1:
                filename = os.path.join(OUTPUT_DIRECTORY, '{0}.hdf5'.format(galaxy[GALAXY.c.name]))
            else:
                filename = os.path.join(OUTPUT_DIRECTORY, '{0}_V{1}.hdf5'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number]))

            h5_file = h5py.File(filename, 'r')

            galaxy_id_aws = galaxy[GALAXY.c.galaxy_id]

            galaxy_group = h5_file['galaxy']
            area_group = galaxy_group['area']
            pixel_group = galaxy_group['pixel']

            check_galaxy_attributes(galaxy)
            check_fits_header(galaxy_id_aws, galaxy_group)
            check_image_filter(galaxy_id_aws, galaxy_group)
            check_area(galaxy_id_aws, area_group)
            check_area_user(galaxy_id_aws, area_group)
            check_pixel(galaxy_id_aws, pixel_group, galaxy[GALAXY.c.pixel_count])

except Exception:
    LOG.exception('Major error')

finally:
    connection.close()

LOG.info('{0} errors found.'.format(error_count))
