#! /usr/bin/env python2.7
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
Extract data from the HDF5 file
"""
import sys
import os
import logging

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import csv
import argparse
import uuid
from hdf5_2_fits.extract_from_hdf5_mod import get_features_and_layers
from hdf5_2_fits.to_fits import generate_files

parser = argparse.ArgumentParser('Extract elements from an HDF5 file',
                                 epilog='You must select at least one feature parameter f0-f6 and one layer parameter l0-l15')

parser.add_argument('email', nargs=1, help='the email address to send the data to')
parser.add_argument('file_name', nargs=1, help='the file with a list of galaxy names in it')

parser.add_argument('-f0', '--best_fit'        , action='store_true', help='extract best fit')
parser.add_argument('-f1', '--percentile_50'   , action='store_true', help='extract percentile 50')
parser.add_argument('-f2', '--highest_prob_bin', action='store_true', help='extract highest probability bin')
parser.add_argument('-f3', '--percentile_2_5'  , action='store_true', help='extract percentile 2.5')
parser.add_argument('-f4', '--percentile_16'   , action='store_true', help='extract percentile 16')
parser.add_argument('-f5', '--percentile_84'   , action='store_true', help='extract percentile 84')
parser.add_argument('-f6', '--percentile_97_5' , action='store_true', help='extract percentile 97.5')

parser.add_argument('-l0',  '--f_mu_sfh'    , action='store_true', help='extract f_mu (SFH)')
parser.add_argument('-l1',  '--f_mu_ir'     , action='store_true', help='extract f_mu (IR)')
parser.add_argument('-l2',  '--mu_parameter', action='store_true', help='extract mu parameter')
parser.add_argument('-l3',  '--tau_v'       , action='store_true', help='extract tau_V')
parser.add_argument('-l4',  '--ssfr_0_1gyr' , action='store_true', help='extract sSFR_0.1Gyr')
parser.add_argument('-l5',  '--m_stars'     , action='store_true', help='extract M(stars)')
parser.add_argument('-l6',  '--l_dust'      , action='store_true', help='extract Ldust')
parser.add_argument('-l7',  '--t_c_ism'     , action='store_true', help='extract T_C^ISM')
parser.add_argument('-l8',  '--t_w_bc'      , action='store_true', help='extract T_W^BC')
parser.add_argument('-l9',  '--xi_c_tot'    , action='store_true', help='extract xi_C^tot')
parser.add_argument('-l10', '--xi_pah_tot'  , action='store_true', help='extract xi_PAH^tot')
parser.add_argument('-l11', '--xi_mir_tot'  , action='store_true', help='extract xi_MIR^tot')
parser.add_argument('-l12', '--xi_w_tot'    , action='store_true', help='extract xi_W^tot')
parser.add_argument('-l13', '--tau_v_ism'   , action='store_true', help='extract tau_V^ISM')
parser.add_argument('-l14', '--m_dust'      , action='store_true', help='extract M(dust)')
parser.add_argument('-l15', '--sfr_0_1gyr'  , action='store_true', help='extract SFR_0.1Gyr')

args = vars(parser.parse_args())

# Does the file exist
if not os.path.exists(args['file_name'][0]):
    parser.print_help()
    exit(1)

features, layers = get_features_and_layers(args)

if len(features) == 0 or len(layers) == 0:
    parser.print_help()
    exit(1)

with open(args['file_name'][0], 'rb') as csv_file:
    reader = csv.reader(csv_file)

    # Skip the header
    names = []
    reader.next()
    for row in reader:
        if int(row[1]) > 1:
            galaxy_name = '{0}_V{1}'.format(row[0], row[1])
        else:
            galaxy_name = row[0]

        names.append(galaxy_name)

# Execute the jobs
uuid_str = str(uuid.uuid4())
for galaxy_name in names[:-1]:
    LOG.info('Submitting job for {0} - no confirmation'.format(galaxy_name))
    generate_files(galaxy_name=galaxy_name, email=args['email'][0], features=features, layers=layers, output_uuid_str=uuid_str, send_confirmation=False)

LOG.info('Submitting job for {0}'.format(galaxy_name))
generate_files(galaxy_name=names[-1], email=args['email'][0], features=features, layers=layers, output_uuid_str=uuid_str)
