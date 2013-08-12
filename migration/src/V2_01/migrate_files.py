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
Some of the HDF5 files did not migrate properly
"""
import logging
import os
import shlex
import tempfile
from sqlalchemy import select
import urllib
import subprocess
from database.database_support_core import GALAXY
from utils.name_builder import get_files_bucket, get_key_hdf5
from utils.s3_helper import S3Helper

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def get_temp_file(extension):
    """
    Get a temporary file
    """
    tmp = tempfile.mkstemp(extension, 'pogs', None, False)
    tmp_file = tmp[0]
    os.close(tmp_file)
    return tmp[1]


def check_results(output, path_name):
    """
    Check the output from the command to get a file

    :param output: the text
    :param path_name: the file that should have been written
    :return: True if the files was downloaded correctly
    """
    print('checking file transfer')
    if output.find('HTTP request sent, awaiting response... 200 OK') >= 0 \
            and output.find('Length:') >= 0 \
            and output.find('Saving to:') >= 0 \
            and os.path.exists(path_name) \
            and os.path.getsize(path_name) > 510:
        return True
    return output


def add_file_to_bucket1(file_bucket_name, key, path_name, s3helper):
    LOG.info('bucket: {0}, key: {1}, file: {2}'.format(file_bucket_name, key, path_name))
    s3helper.add_file_to_bucket(file_bucket_name, key, path_name)


def get_galaxy_number(bad_galaxy_name):
    """
    Get the galaxy number
    """
    elements = bad_galaxy_name.split('__')
    galaxy_number = int(elements[2])
    return galaxy_number


def migrate_hdf5_files(bad_galaxies, connection, file_bucket_name, s3helper):
    for bad_galaxy_name in bad_galaxies:
        LOG.info('Migrating {0}'.format(bad_galaxy_name))

        # extract the galaxy
        galaxy_number = get_galaxy_number(bad_galaxy_name)
        galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_number)).first()

        # Get the hdf5 file
        if galaxy[GALAXY.c.version_number] > 1:
            ngas_file_name = '{0}_V{1}.hdf5'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number])
        else:
            ngas_file_name = '{0}.hdf5'.format(galaxy[GALAXY.c.name])
        path_name = get_temp_file('hdf5')
        command_string = 'wget -O {0} http://cortex.ivec.org:7780/RETRIEVE?file_id={1}&processing=ngamsMWACortexStageDppi'.format(path_name, urllib.quote(ngas_file_name, ''))
        print(command_string)
        try:
            output = subprocess.check_output(shlex.split(command_string), stderr=subprocess.STDOUT)
            if check_results(output, path_name):
                add_file_to_bucket1(file_bucket_name, get_key_hdf5(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id]), path_name, s3helper)
            else:
                LOG.error('Big error with {0}'.format(ngas_file_name))
                raise Exception('wget failed')
        except subprocess.CalledProcessError as e:
            LOG.exception('Big error')
            raise


def find_bad_hdf5_files(s3helper, files_bucket):
    list_bad_files = []

    bucket = s3helper.get_bucket(files_bucket)
    for galaxy_key in bucket.list(prefix='', delimiter='/'):
        # We got the galaxy details - now see if an hdf5 file exists
        galaxy_name = galaxy_key.name[:-1]
        key_name = '{0}/{0}.hdf5'.format(galaxy_name)
        key = bucket.get_key(key_name)
        if key is not None:
            size = key.size
            if size == 499:
                list_bad_files.append(galaxy_name)

    return list_bad_files


def remigrate_files(connection):
    """
    Migrate the various files to S3
    """
    LOG.info('Migrating the files')

    s3helper = S3Helper()
    files_bucket = get_files_bucket()
    bad_galaxies = find_bad_hdf5_files(s3helper, files_bucket)
    migrate_hdf5_files(bad_galaxies, connection, files_bucket, s3helper)
