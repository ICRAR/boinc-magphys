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
Register a FITS file ready to be converted into Work Units
"""

import os, sys, shutil
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))

import argparse, time

from utils.logging_helper import config_logger

from sqlalchemy.engine import create_engine
from config import DB_LOGIN

from work_generation.register_fits_file_mod import fix_redshift, get_data_from_galaxy_txt, \
    decompress_gz_files, extract_tar_file, find_input_filename, find_sigma_filename, add_to_database, \
    save_data_to_file, clean_unused_fits, move_fits_files

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))

parser = argparse.ArgumentParser()
parser.add_argument('working_directory', nargs=1, help='galaxies directory')
parser.add_argument('TAR_file', nargs=1, help='the input tar containing the galaxies')
parser.add_argument('TXT_file', nargs=1, help='the input text file containing galaxy summaries')
parser.add_argument('priority', type=int, nargs=1, help='the higher the number the higher the priority')
parser.add_argument('run_id', type=int, nargs=1, help='the run id to be used')
parser.add_argument('tags', nargs='*', help='any tags to be associated with the galaxy')

args = vars(parser.parse_args())
WORKING_DIRECTORY = args['working_directory'][0]
INPUT_FILE = args['TAR_file'][0]
PRIORITY = args['priority'][0]
RUN_ID = args['run_id'][0]
GALAXY_TEXT_FILE = args['TXT_file'][0]
TAGS = args['tags']

# Make sure the file exists
if not os.path.isfile(INPUT_FILE):
    LOG.error('The file %s does not exist', INPUT_FILE)
    exit(1)

if not WORKING_DIRECTORY.endswith('/'):
    WORKING_DIRECTORY += '/'

# Extract all files from the tar file if they are not already extracted
(head, tail) = os.path.split(INPUT_FILE)

TAR_EXTRACT_LOCATION = WORKING_DIRECTORY + os.path.splitext(tail)[0]
LOG.info('Working Directory: {0}'.format(WORKING_DIRECTORY))
LOG.info('TAR Extract Location: {0}'.format(TAR_EXTRACT_LOCATION))
time.sleep(5)

num_files_extracted = extract_tar_file(INPUT_FILE, TAR_EXTRACT_LOCATION)

num_files_decompressed = decompress_gz_files(TAR_EXTRACT_LOCATION)

all_txt_file_data = get_data_from_galaxy_txt(GALAXY_TEXT_FILE)
num_galaxies_in_txt = len(all_txt_file_data)

num_unused_fits = clean_unused_fits(TAR_EXTRACT_LOCATION, all_txt_file_data)

move_fits_files(TAR_EXTRACT_LOCATION, WORKING_DIRECTORY)

shutil.rmtree(TAR_EXTRACT_LOCATION)

all_galaxy_data = []

num_galaxies_without_file = 0
num_galaxies_without_sigma = 0

for txt_line_info in all_txt_file_data:
    single_galaxy_data = dict()
    single_galaxy_data['name'] = txt_line_info[0]

    input_file = find_input_filename(txt_line_info[0], WORKING_DIRECTORY)
    if input_file is None:
        LOG.error('Galaxy {0} has an input file of None!'.format(single_galaxy_data['name']))
        num_galaxies_without_file += 1
        continue

    sigma = find_sigma_filename(txt_line_info[0], WORKING_DIRECTORY)
    if sigma is None:
        LOG.error('Galaxy {0} has a sigma file of None!'.format(single_galaxy_data['name']))
        sigma = 0.1
        num_galaxies_without_sigma += 1


    gal_type = txt_line_info[4]
    if gal_type is '':
        gal_type = 'Unk'

    single_galaxy_data['sigma'] = sigma
    single_galaxy_data['redshift'] = float(fix_redshift(txt_line_info[3]))
    single_galaxy_data['input_file'] = input_file
    single_galaxy_data['type'] = gal_type
    single_galaxy_data['priority'] = PRIORITY
    single_galaxy_data['run_id'] = RUN_ID
    single_galaxy_data['tags'] = TAGS

    all_galaxy_data.append(single_galaxy_data)

# Connect to the database - the login string is set in the database package
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

num_galaxies_inserted = 0

for galaxy in all_galaxy_data:
    try:
        add_to_database(connection, galaxy)
        num_galaxies_inserted += 1
    except Exception:
        LOG.exception('An error occurred adding {0} to the database'.format(galaxy['name']))

connection.close()

LOG.info('Summary information: ')
LOG.info('Total files extracted from tar: {0}'.format(num_files_extracted))
LOG.info('Total gz files decompressed: {0}'.format(num_files_decompressed))
LOG.info('Total galaxies defined in text file: {0}'.format(num_galaxies_in_txt))
LOG.info('Total fits files without an entry in text file: {0}'.format(num_unused_fits))
LOG.info('Total galaxies in text document with no fits file: {0}'.format(num_galaxies_without_file))
LOG.info('Total galaxies without a sigma file: {0}'.format(num_galaxies_without_sigma))
LOG.info('Total galaxies inserted into database: {0}'.format(num_galaxies_inserted))