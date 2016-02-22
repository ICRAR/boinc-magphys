#! /usr/bin/env python2.7
#
#    Copyright (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
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

import os
import sys

base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))

import argparse
import time
import shutil
import pyfits

from utils.logging_helper import config_logger

from sqlalchemy.engine import create_engine
from config import DB_LOGIN

from work_generation.register_fits_file_mod import fix_redshift, \
    decompress_gz_files, extract_tar_file, find_files, add_to_database, \
    clean_unused_fits, move_fits_files

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('working_directory', nargs=1, help='galaxies directory')
    parser.add_argument('TAR_file', nargs=1, help='the input tar containing the galaxies')
    parser.add_argument('priority', type=int, nargs=1, help='the higher the number the higher the priority')
    parser.add_argument('run_id', type=int, nargs=1, help='the run id to be used')
    parser.add_argument('tags', nargs='*', help='any tags to be associated with the galaxy')

    args = vars(parser.parse_args())
    working_directory = args['working_directory'][0]
    input_file = args['TAR_file'][0]
    priority = args['priority'][0]
    run_id = args['run_id'][0]
    tags = args['tags']

    # Make sure the file exists
    if not os.path.isfile(input_file):
        LOG.error('The file %s does not exist', input_file)
        exit(1)

    if not working_directory.endswith('/'):
        working_directory += '/'

    (head, tail) = os.path.split(input_file)

    tar_extract_location = working_directory + os.path.splitext(tail)[0]
    LOG.info('Working Directory: {0}'.format(working_directory))
    LOG.info('TAR Extract Location: {0}'.format(tar_extract_location))
    time.sleep(5)

    # Extract all fits.gz files from the specified TAR archive
    num_files_extracted, galaxy_names = extract_tar_file(input_file, tar_extract_location)
    num_galaxies_in_tar = len(galaxy_names)

    # Decompress all the fits.gz files that are in the extract location
    num_files_decompressed = decompress_gz_files(tar_extract_location)

    # Delete any fits files that do not have an entry
    num_unused_fits = clean_unused_fits(tar_extract_location, galaxy_names)

    # Move all of the fits files into the working directory
    move_fits_files(tar_extract_location, working_directory)

    # Remove all remaining files from the extract location
    shutil.rmtree(tar_extract_location)

    all_galaxy_data = []

    num_galaxies_without_file = 0
    num_galaxies_without_sigma = 0

    # Loop through each of the galaxies
    for galaxy_name in galaxy_names:
        single_galaxy_data = dict()
        single_galaxy_data['name'] = galaxy_name

        input_files = find_files(galaxy_name, working_directory)

        # Confirming that we have what we need.
        try:
            single_galaxy_data['img'] = input_files['img']
        except KeyError:
            single_galaxy_data['img'] = None

        try:
            single_galaxy_data['img_snr'] = input_files['img_snr']
        except KeyError:
            single_galaxy_data['img_snr'] = None

        try:
            single_galaxy_data['int'] = input_files['int']
        except KeyError:
            single_galaxy_data['int'] = None

        try:
            single_galaxy_data['int_snr'] = input_files['int_snr']
        except KeyError:
            single_galaxy_data['int_snr'] = None

        try:
            single_galaxy_data['rad'] = input_files['rad']
        except KeyError:
            single_galaxy_data['rad'] = None

        try:
            single_galaxy_data['rad_snr'] = input_files['rad_snr']
        except KeyError:
            single_galaxy_data['rad_snr'] = None

        if single_galaxy_data['img'] is None:
            LOG.error('Galaxy {0} has an input file of None!'.format(single_galaxy_data['name']))
            num_galaxies_without_file += 1
            continue

        if single_galaxy_data['img_snr'] is None:
            LOG.error('Galaxy {0} has a sigma file of None!'.format(single_galaxy_data['name']))
            sigma = 0.1
            num_galaxies_without_sigma += 1
        else:
            sigma = input_files['img_snr']

        # Open the fits file and read the values
        img_hdu_list = pyfits.open(single_galaxy_data['img'], memmap=True)
        hdu = img_hdu_list[0]
        gal_type = hdu.header['POGSOBJT'].strip()
        if gal_type is '':
            gal_type = 'Unk'

        single_galaxy_data['sigma'] = sigma
        single_galaxy_data['redshift'] = float(fix_redshift(hdu.header['POGSZ']))
        single_galaxy_data['input_file'] = single_galaxy_data['img']
        single_galaxy_data['type'] = gal_type
        single_galaxy_data['priority'] = priority
        single_galaxy_data['run_id'] = run_id
        single_galaxy_data['tags'] = tags

        all_galaxy_data.append(single_galaxy_data)

    # Connect to the database - the login string is set in the database package
    engine = create_engine(DB_LOGIN)
    connection = engine.connect()

    num_galaxies_inserted = 0

    # Loop through all the galaxies and add them to the db
    for galaxy in all_galaxy_data:
        # noinspection PyBroadException
        try:
            add_to_database(connection, galaxy)
            num_galaxies_inserted += 1
        except Exception:
            LOG.exception('An error occurred adding {0} to the database'.format(galaxy['name']))

    connection.close()

    LOG.info('Summary information: ')
    LOG.info('Total files extracted from tar: {0}'.format(num_files_extracted))
    LOG.info('Total gz files decompressed: {0}'.format(num_files_decompressed))
    LOG.info('Total galaxies defined in tar file: {0}'.format(num_galaxies_in_tar))
    LOG.info('Total fits files without an entry in text file: {0}'.format(num_unused_fits))
    LOG.info('Total galaxies in text document with no fits file: {0}'.format(num_galaxies_without_file))
    LOG.info('Total galaxies without a sigma file: {0}'.format(num_galaxies_without_sigma))
    LOG.info('Total galaxies inserted into database: {0}'.format(num_galaxies_inserted))


if __name__ == "__main__":
    main()
