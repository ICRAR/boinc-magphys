#! /usr/bin/env python2.7
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
Get an HDF5 galaxy from S3
"""
import argparse
import logging
import os

from sqlalchemy import create_engine, select

from config import DB_LOGIN
from database.database_support_core import GALAXY
from utils.name_builder import get_saved_files_bucket, get_key_hdf5, get_galaxy_file_name
from utils.s3_helper import S3Helper

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def get_hdf5_from_s3(galaxy, directory):
    bucket_name = get_saved_files_bucket()
    key = get_key_hdf5(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id])
    s3_helper = S3Helper()
    if s3_helper.file_exists(bucket_name, key):
        if s3_helper.file_archived(bucket_name, key):
            # file is archived
            if s3_helper.file_restoring(bucket_name, key):
                # if file is restoring, just need to wait for it
                LOG.info(
                    'Galaxy {0} ({1}) is still restoring from glacier'.format(
                        galaxy[GALAXY.c.name],
                        galaxy[GALAXY.c.run_id]
                    )
                )
            else:
                # if file is not restoring, need to request.
                LOG.info('Making request for archived galaxy {0} ({1})'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id]))
                s3_helper.restore_archived_file(bucket_name, key, days=10)
        else:
            # file is not archived
            LOG.info('Galaxy {0} ({1}) is available in s3'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id]))
            filename = os.path.join(
                directory,
                get_galaxy_file_name(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id])) + '.hdf5'
            s3_helper.get_file_from_bucket(bucket_name=bucket_name, key_name=key, file_name=filename)

    else:
        LOG.info('The key {0} in bucket {1} does not exist'.format(key, bucket_name))


def process_galaxies(args):
    galaxy_ids = []
    for galaxy_id in args.galaxy_ids:
        if galaxy_id.find('-') > 1:
            list_range = galaxy_id.split('-')
            galaxy_ids.extend(range(int(list_range[0]), int(list_range[1]) + 1))
        else:
            galaxy_ids.append(int(galaxy_id))

    galaxies = []

    engine = create_engine(DB_LOGIN)
    connection = engine.connect()

    for galaxy_id in galaxy_ids:
        galaxy = connection.execute(
            select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)
        ).first()
        if galaxy is not None:
            galaxies.append(galaxy)

    connection.close()

    # Now fetch the details
    if len(galaxies) > 0:
        for galaxy in galaxies:
            get_hdf5_from_s3(galaxy, args.directory)


def main():
    parser = argparse.ArgumentParser('Get the MD5 of a file')
    parser.add_argument('directory', help='the directory to copy the files to')
    parser.add_argument('galaxy_ids', nargs='+', help='the galaxy ids or 4-30 if you need a range')
    args = parser.parse_args()

    if os.path.exists(args.directory) and os.path.isdir(args.directory):
        process_galaxies(args)
        LOG.info('All done')
    else:
        LOG.error('The directory {0} does not exist'.format(args.directory))


if __name__ == "__main__":
    main()
