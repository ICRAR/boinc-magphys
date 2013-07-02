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

"""
import glob
import logging
import os

from sqlalchemy import create_engine
from config import DB_LOGIN, STORED
from database.database_support_core import GALAXY
from utils.name_builder import get_galaxy_image_bucket
from utils.s3_helper import get_s3_connection, get_bucket, add_file_to_bucket

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def get_galaxy_id(hdf5_file_name):
    """
    Get the galaxy id from the filename

    :param hdf5_file_name:       the filename
    :return:           the galaxy id
    """
    # Split the file name up
    (head, tail) = os.path.split(hdf5_file_name)
    (root, ext) = os.path.splitext(tail)

    # The format of the filename is NAME__RUNID__GALAXYID
    index = root.rfind('__')
    if index > 0:
        # Is the rest of the filename digits
        if root[index + 2:].isdigit():
            return int(root[index + 2:]), tail

    return -1, None


def store_files(hdf5_dir):
    """
    Scan a directory for files and send them to the archive

    :param hdf5_dir:  the directory to scan
    :return:
    """
    LOG.info('Directory: %s', hdf5_dir)

    # Get the work units still being processed
    ENGINE = create_engine(DB_LOGIN)
    connection = ENGINE.connect()

    files = os.path.join(hdf5_dir, '*.hdf5')
    file_count = 0

    try:
        s3_connection = get_s3_connection()
        bucket = get_bucket(s3_connection, get_galaxy_image_bucket())

        for file_name in glob.glob(files):
            size = os.path.getsize(file_name)
            galaxy_id, key = get_galaxy_id(file_name)
            if galaxy_id >= 0:
                LOG.info('File name: %s', file_name)
                LOG.info('File size: %d', size)

                add_file_to_bucket(bucket, key, file_name)
                file_count += 1
                os.remove(file_name)
                connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy_id).values(status_id=STORED))

            else:
                LOG.error('File name: %s', file_name)
                LOG.error('File size: %d', size)
                LOG.error('Could not get the galaxy id')

    except Exception:
        LOG.exception('Major error')

    finally:
        connection.close()

    return file_count
