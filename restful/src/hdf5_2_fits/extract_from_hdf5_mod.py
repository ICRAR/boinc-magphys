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
Functions used to extract data from an HDF5
"""
import numpy
import os
import pyfits
from datetime import datetime

OUTPUT_FORMAT_1_00 = 'Version 1.00'
OUTPUT_FORMAT_1_01 = 'Version 1.01'

FEATURES = {
  'best_fit'         : 0,
  'percentile_50'    : 1,
  'highest_prob_bin' : 2,
  'percentile_2_5'   : 3,
  'percentile_16'    : 4,
  'percentile_84'    : 5,
  'percentile_97_5'  : 6,
}

LAYERS = {
  'f_mu_sfh'     : 0 ,
  'f_mu_ir'      : 1 ,
  'mu_parameter' : 2 ,
  'tau_v'        : 3 ,
  'ssfr_0_1gyr'  : 4 ,
  'm_stars'      : 5 ,
  'l_dust'       : 6 ,
  't_c_ism'      : 7 ,
  't_w_bc'       : 8 ,
  'xi_c_tot'     : 9 ,
  'xi_pah_tot'   : 10,
  'xi_mir_tot'   : 11,
  'xi_w_tot'     : 12,
  'tau_v_ism'    : 13,
  'm_dust'       : 14,
  'sfr_0_1gyr'   : 15,
}


def build_fits_image(feature, layer, output_directory, galaxy_group, pixel_data):
    """
    Extract a feature from the HDF5 file into a FITS file

    :param feature:
    :param layer:
    :param galaxy_group:
    :param pixel_data:
    :return:
    """
    feature_index = FEATURES[feature]
    layer_index = LAYERS[layer]

    # I need to reshape the array as pyfits uses y, x whilst the hdf5 uses x, y
    dimension_x = galaxy_group.attrs['dimension_x']
    dimension_y = galaxy_group.attrs['dimension_y']
    data = numpy.empty((dimension_y, dimension_x), dtype=numpy.float)
    data.fill(numpy.NaN)

    for x in range(dimension_x):
        data[:, x] = pixel_data[x, :, layer_index, feature_index]

    utc_now = datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%S')
    hdu = pyfits.PrimaryHDU(data)
    hdu_list = pyfits.HDUList([hdu])

    # Write our details first in the header
    hdu_list[0].header.update('MAGPHYST', layer                               , 'MAGPHYS Parameter')
    hdu_list[0].header.update('DATE'    , utc_now                             , 'Creation UTC (CCCC-MM-DD) date of FITS header')
    hdu_list[0].header.update('GALAXYID', galaxy_group.attrs['galaxy_id']     , 'The POGS Galaxy Id')
    hdu_list[0].header.update('VRSNNMBR', galaxy_group.attrs['version_number'], 'The POGS Galaxy Version Number')
    hdu_list[0].header.update('REDSHIFT', str(galaxy_group.attrs['redshift']) , 'The POGS Galaxy redshift')
    hdu_list[0].header.update('SIGMA'   , str(galaxy_group.attrs['sigma'])    , 'The POGS Galaxy sigma')

    output_format = galaxy_group.attrs['output_format']
    for fits_header in galaxy_group['fits_header']:
        keyword = fits_header[0]
        if keyword not in ['SIMPLE', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2', 'EXTEND', 'DATE']:
            if output_format == OUTPUT_FORMAT_1_00 or keyword == 'COMMENT' or keyword == 'HISTORY':
                hdu_list[0].header.update(keyword, fits_header[1])
            else:
                hdu_list[0].header.update(keyword, fits_header[1], fits_header[2])

    # Write the file
    if galaxy_group.attrs['version_number'] == 1:
        file_name = os.path.join(output_directory, '{0}.{1}.{2}.fits'.format(galaxy_group.attrs['name'], feature, layer))
    else:
        file_name = os.path.join(output_directory, '{0}_V{1}.{2}.{3}.fits'.format(galaxy_group.attrs['name'], galaxy_group.attrs['version_number'], feature, layer))
    hdu_list.writeto(file_name, clobber=True)
    return file_name


def get_features_and_layers(args):
    """
    Get the features and layers
    :param args:
    :return:
    """
    features = []
    if args['best_fit']:
        features.append('best_fit')
    if args['percentile_50']:
        features.append('percentile_50')
    if args['highest_prob_bin']:
        features.append('highest_prob_bin')
    if args['percentile_2_5']:
        features.append('percentile_2_5')
    if args['percentile_16']:
        features.append('percentile_16')
    if args['percentile_84']:
        features.append('percentile_84')
    if args['percentile_97_5']:
        features.append('percentile_97_5')

    layers = []
    if args['f_mu_sfh']:
        layers.append('f_mu_sfh')
    if args['f_mu_ir']:
        layers.append('f_mu_ir')
    if args['mu_parameter']:
        layers.append('mu_parameter')
    if args['tau_v']:
        layers.append('tau_v')
    if args['ssfr_0_1gyr']:
        layers.append('ssfr_0_1gyr')
    if args['m_stars']:
        layers.append('m_stars')
    if args['l_dust']:
        layers.append('l_dust')
    if args['t_c_ism']:
        layers.append('t_c_ism')
    if args['t_w_bc']:
        layers.append('t_w_bc')
    if args['xi_c_tot']:
        layers.append('xi_c_tot')
    if args['xi_pah_tot']:
        layers.append('xi_pah_tot')
    if args['xi_mir_tot']:
        layers.append('xi_mir_tot')
    if args['xi_w_tot']:
        layers.append('xi_w_tot')
    if args['tau_v_ism']:
        layers.append('tau_v_ism')
    if args['m_dust']:
        layers.append('m_dust')
    if args['sfr_0_1gyr']:
        layers.append('sfr_0_1gyr')

    return features, layers
