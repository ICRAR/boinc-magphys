#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2016
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
import os
import gzip
import tarfile
import shutil
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

        LOG.info(txt_line_info)

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
                # noinspection PyBroadException
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
    galaxy_names = set()
    galaxy_archive = tarfile.open(tar_file, 'r')

    LOG.info('{0} total files (approx {1} galaxies) to extract'.format(len(galaxy_archive.getnames()), len(galaxy_archive.getnames())/6))
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

            if f.name.startswith('POGS_'):
                galaxy_name = f.name[5:-8]
                galaxy_names.add(galaxy_name)

    galaxy_archive.close()
    return num_files_extracted, galaxy_names


def noext(filename):
    """
    Remove the extension from a filename
    :param filename:
    :return:
    """
    ext_start = filename.find('.')
    return filename[:ext_start]


def find_files(galaxy_name, location):
    """
    Finds any input files
    :param galaxy_name:
    :param location:
    :return:
    """
    galaxy_data = {}

    all_files = os.listdir(location)

    for one_file in all_files:
        filename = noext(one_file)
        if filename.startswith('POGS_'):
            if filename.endswith(galaxy_name):
                galaxy_data['img'] = os.path.abspath(location + '/' + one_file)
                LOG.info('{0} Found image'.format(galaxy_name))

        if filename.startswith('POGSSNR_'):
            if filename.endswith(galaxy_name):
                galaxy_data['img_snr'] = os.path.abspath(location + '/' + one_file)
                LOG.info('{0} Found image snr'.format(galaxy_name))

        if filename.startswith('POGSint_'):
            if filename.endswith(galaxy_name):
                galaxy_data['int'] = os.path.abspath(location + '/' + one_file)
                LOG.info('{0} Found int flux'.format(galaxy_name))

        if filename.startswith('POGSintSNR_'):
            if filename.endswith(galaxy_name):
                galaxy_data['int_snr'] = os.path.abspath(location + '/' + one_file)
                LOG.info('{0} Found int flux snr'.format(galaxy_name))

        if filename.startswith('POGSrad_'):
            if filename.endswith(galaxy_name):
                galaxy_data['rad'] = os.path.abspath(location + '/' + one_file)
                LOG.info('{0} Found rad'.format(galaxy_name))

        if filename.startswith('POGSradSNR_'):
            if filename.endswith(galaxy_name):
                galaxy_data['rad_snr'] = os.path.abspath(location + '/' + one_file)
                LOG.info('{0} Found rad snr'.format(galaxy_name))

    return galaxy_data


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
            # noinspection PyBroadException
            try:
                if os.path.exists(to_location + '/' + item):
                    os.remove(to_location + '/' + item)
                shutil.move(from_location + '/' + item, to_location)
                LOG.info('Moved {0} to {1}'.format(item, os.path.abspath(to_location)))
            except Exception:
                LOG.exception('Could not move file {0} to location {1}'.format(item, to_location))


def clean_unused_fits(location, galaxy_names):
    """
    Will delete any fits files in a directory that do NOT have a galaxy in the 'galaxies' dict
    :param location:
    :param galaxy_names:
    :return:
    """

    files = os.listdir(location)
    files_to_delete = []

    for item in files:
        found = False
        for galaxy_name in galaxy_names:
            if item.endswith('.fits') and item[:-5].endswith(galaxy_name):
                found = True
                break
        if found is False:
            if item.endswith('.fits'):
                files_to_delete.append(item)

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
    galaxy_name = galaxy['name']
    redshift = galaxy['redshift']
    galaxy_type = galaxy['type']
    input_file = galaxy['input_file']
    priority = galaxy['priority']
    run_id = galaxy['run_id']
    sigma_in = galaxy['sigma']
    tags = galaxy['tags']
    integrated = galaxy['int']
    integrated_snr = galaxy['int_snr']
    rad = galaxy['rad']
    rad_snr = galaxy['rad_snr']

    transaction = connection.begin()
    try:
        try:
            sigma = float(sigma_in)
            sigma_filename = None
        except ValueError:
            sigma = 0.0
            sigma_filename = sigma_in

        result = connection.execute(
            REGISTER.insert(),
            galaxy_name=galaxy_name,
            redshift=redshift,
            galaxy_type=galaxy_type,
            filename=input_file,
            priority=priority,
            register_time=datetime.now(),
            run_id=run_id,
            sigma=sigma,
            sigma_filename=sigma_filename,
            int_filename=integrated,
            int_sigma_filename=integrated_snr,
            rad_filename=rad,
            rad_sigma_filename=rad_snr
        )

        register_id = result.inserted_primary_key[0]

        # Get the tag ids
        tag_ids = set()
        for tag_text in tags:
            tag_text = tag_text.strip()
            if len(tag_text) > 0:
                tag = connection.execute(select([TAG]).where(TAG.c.tag_text == tag_text)).first()
                if tag is None:
                    result = connection.execute(
                        TAG.insert(),
                        tag_text=tag_text
                    )
                    tag_id = result.inserted_primary_key[0]
                else:
                    tag_id = tag[TAG.c.tag_id]

                tag_ids.add(tag_id)

        # Add the tag ids
        for tag_id in tag_ids:
            connection.execute(
                TAG_REGISTER.insert(),
                tag_id=tag_id,
                register_id=register_id
            )

        transaction.commit()
        LOG.info('Registered %s %s %f %s %d %d', galaxy_name, galaxy_type, redshift, input_file, priority, run_id)
        for tag_text in tags:
            LOG.info('Tag: {0}'.format(tag_text))
    except Exception:
        transaction.rollback()
        raise
