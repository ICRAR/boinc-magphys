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
Functions used my register
"""
from decimal import Decimal
import os, gzip, tarfile, shutil
from utils.logging_helper import config_logger
from datetime import datetime
from sqlalchemy import select
from database.database_support_core import REGISTER, TAG_REGISTER, TAG

LOG = config_logger(__name__)
FOUR_PLACES = Decimal('.0001')
FIVE_PLACES = Decimal('.00001')


def fix_redshift(redshift_in):
    """
    Fix the redshift if it happens to be exactly on the boundary between two models.

    0.005, 0.015 - need to be nudged down to make sure they work proper


    >>> fix_redshift('0.00')
    Decimal('0.00000')

    >>> fix_redshift('0.005')
    Decimal('0.00490')
    """
    redshift = Decimal(redshift_in).quantize(FIVE_PLACES)
    if str(redshift)[-3:] == '500':
        redshift -= FOUR_PLACES

    return redshift


def get_data_from_galaxy_txt(text_file):
    """
    Gets galaxy names and redshifts from the specified input file.
    :param text_file:
    :return:
    """
    LOG.info('Extracting lines from {0}'.format(text_file))
    galaxy_txt = open(text_file, 'r')

    line = galaxy_txt.readline()
    all_txt_file_data = []
    while line != '':

        txt_line_info = ['']*5
        curr_field = 0
        next_blank_is_delimit = False
        for char in line:
            if char == ' ' or char == '\t' or char == '\r' or char == '\n':
                if next_blank_is_delimit:
                    curr_field += 1
                    next_blank_is_delimit = False

            else:
                txt_line_info[curr_field] += char
                next_blank_is_delimit = True

        all_txt_file_data.append(txt_line_info)

        line = galaxy_txt.readline()

    return all_txt_file_data


def decompress_gz_files(location):
    """
    Decompresses all gz files in the specified location and deletes them once decompressed
    :param location:
    :return:
    """
    num_files_decompressed = 0
    files = os.listdir(location)
    LOG.info('Decompressing now...')
    
    files_to_decompress = []
    for f in files:
        if f.endswith('gz'):
            files_to_decompress.append(f)
    
    if len(files_to_decompress) is 0:
        LOG.info('No gz files to extract in {0}'.format(location))
    else:
        for f in files_to_decompress:
            f = location + '/' + f
            # Check if decompressed copy exists
            if os.path.exists(f[:-3]):
                LOG.info('{0} already exists!'.format(f))
            else:
                LOG.info('Decompressing {0}...'.format(f))
                compressed = None
                decompressed = None
                try:
                    compressed = gzip.open(f, 'rb')
                    decompressed = open(f[:-3], 'w')
                    decompressed.write(compressed.read())

                    compressed.close()
                    decompressed.close()
                    os.remove(f)
                    num_files_decompressed += 1
                except Exception:
                    LOG.exception("Error decompressing {0}".format(f))
                    if compressed is not None:
                        compressed.close()
                    if decompressed is not None:
                        decompressed.close()

    return num_files_decompressed


def extract_tar_file(tar_file, location):
    """
    Exctracts the specified tar file to the specified location
    :param tar_file:
    :param location:
    :return:
    """
    num_files_extracted = 0
    galaxy_archive = tarfile.open(tar_file, 'r')
    
    LOG.info('{0} total files (approx {1} galaxies) to extract'.format(len(galaxy_archive.getnames()), len(galaxy_archive.getnames())/2))
    LOG.info('Extracting now...')
    
    if os.path.isdir(location):
        LOG.info('{0} directory already exists'.format(location))
    else:
        os.mkdir(location)
    
    for f in galaxy_archive.getmembers():
        if os.path.exists('{0}/{1}'.format(location, f.name)) or os.path.exists('{0}/{1}'.format(location, f.name[:-3])):
            LOG.info('{0} already exists'.format(f.name))
        else:
            galaxy_archive.extract(f, location)
            LOG.info('Extracting...{0}'.format(f.name))
            num_files_extracted += 1

    galaxy_archive.close()
    return num_files_extracted

def find_input_filename(galaxy_name, location):
    """
    Finds the main fits file for the specified galaxy name
    :param galaxy_name:
    :param location:
    :return:
    """
    all_files = os.listdir(location)

    for one_file in all_files:
        if one_file.startswith('POGS_'):
            ext_start = one_file.rfind('.')
            if one_file[:ext_start].endswith(galaxy_name):
                return os.path.abspath(location + '/' + one_file)

    return None


def find_sigma_filename(galaxy_name, location):
    """
    Finds the sigma filename for the specified galaxy name
    :param galaxy_name:
    :param location:
    :return:
    """
    all_files = os.listdir(location)

    for one_file in all_files:
        if one_file.startswith('POGSSNR_'):
            ext_start = one_file.find('.')
            if one_file[:ext_start].endswith(galaxy_name):
                return os.path.abspath(location + '/' + one_file)


def save_data_to_file(galaxies, filename):
    """
    Debugging function that prints all galaxies to a file.
    :param galaxies:
    :param filename:
    :return:
    """
    output = open(filename, 'w')
    output.write('Filename   Redshift   Galaxy   Type   Sigma   Priority   Run_Id   Tags\n')
    for item in galaxies:
        output.write(item['input_file'])
        output.write('   ')
        output.write(str(item['redshift']))
        output.write('   ')
        output.write(item['name'])
        output.write('   ')
        output.write(item['type'])
        output.write('   ')
        output.write(item['sigma'])
        output.write('   ')
        output.write(str(item['priority']))
        output.write('   ')
        output.write(str(item['run_id']))
        output.write('   ')
        for tag in item['tags']:
            output.write(tag)
            output.write(' ')
        output.write('\n')


def move_fits_files(from_location, to_location):
    """
    Moves all of the fits files in 'from_location' to 'to_location'
    :param from_location:
    :param to_location:
    :return:
    """
    files = os.listdir(from_location)

    for item in files:
        if item.endswith('.fits'):
            try:
                if os.path.exists(to_location + '/' + item):
                    os.remove(to_location + '/' + item)
                shutil.move(from_location + '/' + item, to_location)
                LOG.info('Moved {0} to {1}'.format(item, os.path.abspath(to_location)))
            except Exception:
                LOG.exception('Could not move file {0} to location {1}'.format(item, to_location))


def clean_unused_fits(location, galaxies):
    """
    Will delete any fits files in a directory that do NOT have a galaxy in the 'galaxies' dict
    :param location:
    :param galaxies:
    :return:
    """

    files = os.listdir(location)
    files_to_delete = []

    for f_file in files:
        found = False
        for galaxy in galaxies:
            if f_file[:-5].endswith(galaxy[0]):
                found = True
                break

        if not found:
            files_to_delete.append(f_file)

    if len(files_to_delete) > 0:
        LOG.info('The following fits files do not have entries in the txt file. Deleting...')
        for item in files_to_delete:
            LOG.info('Deleting {0}'.format(item))
            os.remove(location + '/' + item)

    return len(files_to_delete)


def add_to_database(connection, galaxy):
    """
    Adds the specified galaxies to the database
    :param connection:
    :param galaxy:
    :return:
    """
    GALAXY_NAME = galaxy['name']
    REDSHIFT = galaxy['redshift']
    GALAXY_TYPE = galaxy['type']
    INPUT_FILE = galaxy['input_file']
    PRIORITY = galaxy['priority']
    RUN_ID = galaxy['run_id']
    SIGMA = galaxy['sigma']
    TAGS = galaxy['tags']

    transaction = connection.begin()
    try:
        try:
            sigma = float(SIGMA)
            sigma_filename = None
        except ValueError:
            sigma = 0.0
            sigma_filename = SIGMA

        result = connection.execute(REGISTER.insert(),
                                    galaxy_name=GALAXY_NAME,
                                    redshift=REDSHIFT,
                                    galaxy_type=GALAXY_TYPE,
                                    filename=INPUT_FILE,
                                    priority=PRIORITY,
                                    register_time=datetime.now(),
                                    run_id=RUN_ID,
                                    sigma=sigma,
                                    sigma_filename=sigma_filename)

        register_id = result.inserted_primary_key[0]

        # Get the tag ids
        tag_ids = set()
        for tag_text in TAGS:
            tag_text = tag_text.strip()
            if len(tag_text) > 0:
                tag = connection.execute(select([TAG]).where(TAG.c.tag_text == tag_text)).first()
                if tag is None:
                    result = connection.execute(TAG.insert(),
                                                tag_text=tag_text)
                    tag_id = result.inserted_primary_key[0]
                else:
                    tag_id = tag[TAG.c.tag_id]

                tag_ids.add(tag_id)

        # Add the tag ids
        for tag_id in tag_ids:
            connection.execute(TAG_REGISTER.insert(),
                               tag_id=tag_id,
                               register_id=register_id)

        transaction.commit()
        LOG.info('Registered %s %s %f %s %d %d', GALAXY_NAME, GALAXY_TYPE, REDSHIFT, INPUT_FILE, PRIORITY, RUN_ID)
        for tag_text in TAGS:
            LOG.info('Tag: {0}'.format(tag_text))
    except Exception:
        transaction.rollback()
        raise