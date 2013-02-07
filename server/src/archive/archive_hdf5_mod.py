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
import h5py
import logging
import numpy
from sqlalchemy.sql.expression import select, func
from database.database_support_core import FITS_HEADER, AREA, IMAGE_FILTERS_USED, AREA_USER, PIXEL_RESULT, PIXEL_PARAMETER, PIXEL_FILTER, PIXEL_HISTOGRAM

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

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

INDEX_BEST_FIT         = 0
INDEX_PERCENTILE_50    = 1
INDEX_HIGHEST_PROB_BIN = 2
INDEX_PERCENTILE_2_5   = 3
INDEX_PERCENTILE_16    = 4
INDEX_PERCENTILE_84    = 5
INDEX_PERCENTILE_97_5  = 6

INDEX_F_MU_SFH     = 0
INDEX_F_MU_IR      = 1
INDEX_MU_PARAMETER = 2
INDEX_TAU_V        = 3
INDEX_SSFR_0_1GYR  = 4
INDEX_M_STARS      = 5
INDEX_L_DUST       = 6
INDEX_T_C_ISM      = 7
INDEX_T_W_BC       = 8
INDEX_XI_C_TOT     = 9
INDEX_XI_PAH_TOT   = 10
INDEX_XI_MIR_TOT   = 11
INDEX_XI_W_TOT     = 12
INDEX_TAU_V_ISM    = 13
INDEX_M_DUST       = 14
INDEX_SFR_0_1GYR   = 15

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
data_type_fits_header = numpy.dtype([
    ('keyword', h5py.special_dtype(vlen=str)),
    ('value',   h5py.special_dtype(vlen=str)),
])
data_type_image_filter = numpy.dtype([
    ('image_number',    long),
    ('filter_id_red',   long),
    ('filter_id_green', long),
    ('filter_id_blue',  long),
])
data_type_pixel = numpy.dtype([
    ('pxresult_id' , long),
    ('area_id'     , long),
    ('i_sfh'       , float),
    ('i_ir'        , float),
    ('chi2'        , float),
    ('redshift'    , float),
    ('i_opt'       , float),
    ('dmstar'      , float),
    ('dfmu_aux'    , float),
    ('dz'          , float),
])
data_type_pixel_histogram = numpy.dtype([
    ('x_axis', float),
    ('hist_value', float),
])
data_type_pixel_parameter =  numpy.dtype([
    ('first_prob_bin', float),
    ('last_prob_bin',  float),
    ('bin_step',       float),

])
data_type_pixel_filter = numpy.dtype([
    ('observed_flux', float),
    ('observational_uncertainty', float),
    ('flux_bfm', float),
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
    data = numpy.zeros(count, dtype=data_type_fits_header)
    count = 0
    for fits_header in connection.execute(select([FITS_HEADER]).where(FITS_HEADER.c.galaxy_id == galaxy_id).order_by(FITS_HEADER.c.fitsheader_id)):
        data[count] = (
            fits_header[FITS_HEADER.c.keyword],
            fits_header[FITS_HEADER.c.value],
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
        data[count] = (
            image_filters_used[IMAGE_FILTERS_USED.c.image_number],
            image_filters_used[IMAGE_FILTERS_USED.c.filter_id_red],
            image_filters_used[IMAGE_FILTERS_USED.c.filter_id_green],
            image_filters_used[IMAGE_FILTERS_USED.c.filter_id_blue],
            )
        count += 1
    group.create_dataset('image_filters', data=data, compression='gzip')

def store_pixels(connection, galaxy_id, group, dimension_x, dimension_y, dimension_z, pixel_count):
    """
    Store the pixel data
    """
    LOG.info('Storing the pixel data - {0} pixels to process'.format(pixel_count))
    count = connection.execute(select([func.count(PIXEL_HISTOGRAM.c.pxhistogram_id)], from_obj=PIXEL_HISTOGRAM.join(PIXEL_RESULT)).where(PIXEL_RESULT.c.galaxy_id == galaxy_id)).first()[0]

    data = numpy.empty((dimension_x, dimension_y, NUMBER_PARAMETERS, NUMBER_IMAGES), dtype=numpy.float)
    data.fill(numpy.NaN)
    data_pixel_details = group.create_dataset('pixel_details', (dimension_x, dimension_y), dtype=data_type_pixel, compression='gzip')
    data_pixel_parameters = group.create_dataset('pixel_parameters', (dimension_x, dimension_y, NUMBER_PARAMETERS), dtype=data_type_pixel_parameter, compression='gzip')
    data_pixel_filter = group.create_dataset('pixel_filters', (dimension_x, dimension_y, dimension_z), dtype=data_type_pixel_filter, compression='gzip')
    data_pixel_histograms_grid = group.create_dataset('pixel_histograms_grid', (dimension_x, dimension_y, NUMBER_PARAMETERS), dtype=h5py.special_dtype(ref=h5py.RegionReference), compression='gzip')
    data_pixel_histograms_list = group.create_dataset('pixel_histograms_list', (count,), dtype=data_type_pixel_histogram, compression='gzip')

    count = 0
    pixel_histogram_count = 0
    for pixel_result in connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.galaxy_id == galaxy_id)):
        count += 1

        if count % 500 == 0:
            LOG.info('Processed {0} of {1}'.format(count, pixel_count))

        pxresult_id = pixel_result[PIXEL_RESULT.c.pxresult_id]
        x = pixel_result[PIXEL_RESULT.c.x]
        y = pixel_result[PIXEL_RESULT.c.y]
        data[x, y, INDEX_F_MU_SFH    , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.fmu_sfh]
        data[x, y, INDEX_F_MU_IR     , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.fmu_ir]
        data[x, y, INDEX_MU_PARAMETER, INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.mu]
        data[x, y, INDEX_TAU_V       , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.tauv]
        data[x, y, INDEX_SSFR_0_1GYR , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.s_sfr]
        data[x, y, INDEX_M_STARS     , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.m]
        data[x, y, INDEX_L_DUST      , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.ldust]
        data[x, y, INDEX_T_C_ISM     , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.t_c_ism]
        data[x, y, INDEX_T_W_BC      , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.t_w_bc]
        data[x, y, INDEX_XI_C_TOT    , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.xi_c_tot]
        data[x, y, INDEX_XI_PAH_TOT  , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.xi_pah_tot]
        data[x, y, INDEX_XI_MIR_TOT  , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.xi_mir_tot]
        data[x, y, INDEX_XI_W_TOT    , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.x_w_tot]
        data[x, y, INDEX_TAU_V_ISM   , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.tvism]
        data[x, y, INDEX_M_DUST      , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.mdust]
        data[x, y, INDEX_SFR_0_1GYR  , INDEX_BEST_FIT] = pixel_result[PIXEL_RESULT.c.sfr]

        data_pixel_details[x, y] = (
            pxresult_id,
            pixel_result[PIXEL_RESULT.c.area_id],
            pixel_result[PIXEL_RESULT.c.i_sfh],
            pixel_result[PIXEL_RESULT.c.i_ir],
            pixel_result[PIXEL_RESULT.c.chi2],
            pixel_result[PIXEL_RESULT.c.redshift],
            pixel_result[PIXEL_RESULT.c.i_opt],
            pixel_result[PIXEL_RESULT.c.dmstar],
            pixel_result[PIXEL_RESULT.c.dfmu_aux],
            pixel_result[PIXEL_RESULT.c.dz],
        )

        for pixel_parameter in connection.execute(select([PIXEL_PARAMETER]).where(PIXEL_PARAMETER.c.pxresult_id == pxresult_id).order_by(PIXEL_PARAMETER.c.pxparameter_id)):
            if pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] is not None:
                z = pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] - 1
                data[x, y, z, INDEX_PERCENTILE_50]    = pixel_parameter[PIXEL_PARAMETER.c.percentile50]
                data[x, y, z, INDEX_HIGHEST_PROB_BIN] = pixel_parameter[PIXEL_PARAMETER.c.high_prob_bin] if pixel_parameter[PIXEL_PARAMETER.c.high_prob_bin] is not None else numpy.NaN
                data[x, y, z, INDEX_PERCENTILE_2_5]   = pixel_parameter[PIXEL_PARAMETER.c.percentile2_5]
                data[x, y, z, INDEX_PERCENTILE_16]    = pixel_parameter[PIXEL_PARAMETER.c.percentile16]
                data[x, y, z, INDEX_PERCENTILE_84]    = pixel_parameter[PIXEL_PARAMETER.c.percentile84]
                data[x, y, z, INDEX_PERCENTILE_97_5]  = pixel_parameter[PIXEL_PARAMETER.c.percentile97_5]

                first_prob_bin = pixel_parameter[PIXEL_PARAMETER.c.first_prob_bin] if pixel_parameter[PIXEL_PARAMETER.c.first_prob_bin] is not None else numpy.NaN
                last_prob_bin = pixel_parameter[PIXEL_PARAMETER.c.last_prob_bin] if pixel_parameter[PIXEL_PARAMETER.c.last_prob_bin] is not None else numpy.NaN
                bin_step = pixel_parameter[PIXEL_PARAMETER.c.bin_step] if pixel_parameter[PIXEL_PARAMETER.c.bin_step] is not None else numpy.NaN
                data_pixel_parameters[x, y, z] = (
                    first_prob_bin,
                    last_prob_bin,
                    bin_step,
                )

                pixel_histogram_start = pixel_histogram_count
                for pixel_histogram in connection.execute(select([PIXEL_HISTOGRAM]).where(PIXEL_HISTOGRAM.c.pxparameter_id == pixel_parameter[PIXEL_PARAMETER.c.pxparameter_id]).order_by(PIXEL_HISTOGRAM.c.pxhistogram_id)):
                    data_pixel_histograms_list[pixel_histogram_count] = (
                        pixel_histogram[PIXEL_HISTOGRAM.c.x_axis],
                        pixel_histogram[PIXEL_HISTOGRAM.c.hist_value],
                    )
                    pixel_histogram_count += 1
                # only store it if we have it
                if pixel_histogram_count - pixel_histogram_start > 0:
                    data_pixel_histograms_grid[x, y, z] = data_pixel_histograms_list.regionref[pixel_histogram_start:pixel_histogram_count]

        filter_layer = 0
        for pixel_filter in connection.execute(select([PIXEL_FILTER]).where(PIXEL_FILTER.c.pxresult_id == pxresult_id).order_by(PIXEL_FILTER.c.pxfilter_id)):
            # Sometimes we seem to get two versions of the data - just use the first set
            if filter_layer < dimension_z:
                data_pixel_filter[x, y, filter_layer] = (
                    pixel_filter[PIXEL_FILTER.c.observed_flux],
                    pixel_filter[PIXEL_FILTER.c.observational_uncertainty],
                    pixel_filter[PIXEL_FILTER.c.flux_bfm],
                )
                filter_layer += 1

    pixel_dataset = group.create_dataset('pixels', data=data, compression='gzip')
    pixel_dataset.attrs['DIM3_F_MU_SFH']     = INDEX_F_MU_SFH
    pixel_dataset.attrs['DIM3_F_MU_IR']      = INDEX_F_MU_IR
    pixel_dataset.attrs['DIM3_MU_PARAMETER'] = INDEX_MU_PARAMETER
    pixel_dataset.attrs['DIM3_TAU_V']        = INDEX_TAU_V
    pixel_dataset.attrs['DIM3_SSFR_0_1GYR']  = INDEX_SSFR_0_1GYR
    pixel_dataset.attrs['DIM3_M_STARS']      = INDEX_M_STARS
    pixel_dataset.attrs['DIM3_L_DUST']       = INDEX_L_DUST
    pixel_dataset.attrs['DIM3_T_C_ISM']      = INDEX_T_C_ISM
    pixel_dataset.attrs['DIM3_T_W_BC']       = INDEX_T_W_BC
    pixel_dataset.attrs['DIM3_XI_C_TOT']     = INDEX_XI_C_TOT
    pixel_dataset.attrs['DIM3_XI_PAH_TOT']   = INDEX_XI_PAH_TOT
    pixel_dataset.attrs['DIM3_XI_MIR_TOT']   = INDEX_XI_MIR_TOT
    pixel_dataset.attrs['DIM3_XI_W_TOT']     = INDEX_XI_W_TOT
    pixel_dataset.attrs['DIM3_TAU_V_ISM']    = INDEX_TAU_V_ISM
    pixel_dataset.attrs['DIM3_M_DUST']       = INDEX_M_DUST
    pixel_dataset.attrs['DIM3_SFR_0_1GYR']   = INDEX_SFR_0_1GYR

    pixel_dataset.attrs['DIM4_BEST_FIT']         = INDEX_BEST_FIT
    pixel_dataset.attrs['DIM4_PERCENTILE_50']    = INDEX_PERCENTILE_50
    pixel_dataset.attrs['DIM4_HIGHEST_PROB_BIN'] = INDEX_HIGHEST_PROB_BIN
    pixel_dataset.attrs['DIM4_PERCENTILE_2_5']   = INDEX_PERCENTILE_2_5
    pixel_dataset.attrs['DIM4_PERCENTILE_16']    = INDEX_PERCENTILE_16
    pixel_dataset.attrs['DIM4_PERCENTILE_84']    = INDEX_PERCENTILE_84
    pixel_dataset.attrs['DIM4_PERCENTILE_97_5']  = INDEX_PERCENTILE_97_5

    pxresult_id = connection.execute(select([PIXEL_RESULT.c.pxresult_id]).where(PIXEL_RESULT.c.galaxy_id == galaxy_id)).first()[0]
    filter_layer = 0
    for pixel_filter in connection.execute(select([PIXEL_FILTER]).where(PIXEL_FILTER.c.pxresult_id == pxresult_id).order_by(PIXEL_FILTER.c.pxfilter_id)):
        data_pixel_filter.attrs[pixel_filter[PIXEL_FILTER.c.filter_name]] = filter_layer
        filter_layer += 1

    return count
