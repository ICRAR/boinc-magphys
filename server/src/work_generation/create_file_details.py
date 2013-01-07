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
Load the run details into the database
"""
import logging
import os
import sys

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import argparse
import glob

from work_generation import STAR_FORMATION_FILE, INFRARED_FILE
from work_generation.create_file_details_mod import get_md5, get_redshift

parser = argparse.ArgumentParser()
parser.add_argument('input_dir', nargs=1, help='the directory containing the files')
parser.add_argument('output_dir', nargs=1, help='where the output file will be written')

args = vars(parser.parse_args())

INPUT_DIR = args['input_dir'][0]
OUTPUT_DIR = args['output_dir'][0]

# Check things exist
errors = []

if os.path.isdir(INPUT_DIR):
    # Check we have matching star formation and infrared files
    star_form_hist = glob.glob('{0}/starformhist_cb07_z*.lbr'.format(INPUT_DIR))
    infrared = glob.glob('{0}/infrared_dce08_z*.lbr'.format(INPUT_DIR))

    if len(star_form_hist) != len(infrared):
        errors.append('The number of starformhist files ({0}) does not match the number of infrared files ({1})'.format(len(star_form_hist), len(infrared)))
    elif not len(infrared):
        errors.append('There are no starformhist or infrared files')
    else:
        # Check we have matching files
        star_form_hist.sort()
        infrared.sort()

        for i in range(len(infrared)):
            (head, file_1) = os.path.split(star_form_hist[i])
            (head, file_2) = os.path.split(infrared[i])

            if file_1[18:] != file_2[15:]:
                errors.append('{0} does not match {1}'.format(file_1, file_2))

else:
    errors.append('The directory {0} does not exist.'.format(INPUT_DIR))

# we have errors
if len(errors) > 0:
    for error in errors:
        LOG.error(error)

else:
    if OUTPUT_DIR.endswith('/'):
        output = '{0}file_details.dat'.format(OUTPUT_DIR)
    else:
        output = '{0}/file_details.dat'.format(OUTPUT_DIR)
    file = open(output, "wb")

    # Add the star formation files
    star_form_hist_files = glob.glob('{0}/starformhist_cb07_z*.lbr'.format(INPUT_DIR))
    star_form_hist_files.sort()
    for star_form_hist in star_form_hist_files:
        (head, file_1) = os.path.split(star_form_hist)
        file.write('{0} {1} {2} {3} {4}\n'.format(file_1, STAR_FORMATION_FILE, get_md5(star_form_hist), get_redshift(file_1), os.path.getsize(star_form_hist)))

    # Add the infrared files
    infrared_files = glob.glob('{0}/infrared_dce08_z*.lbr'.format(INPUT_DIR))
    infrared_files.sort()
    for infrared in infrared_files:
        (head, file_1) = os.path.split(infrared)
        file.write('{0} {1} {2} {3} {4}\n'.format(file_1, INFRARED_FILE, get_md5(infrared), get_redshift(file_1), os.path.getsize(infrared)))

    file.close()
