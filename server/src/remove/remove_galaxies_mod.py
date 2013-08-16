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
Functions used to delete a galaxy
"""
from utils.name_builder import get_galaxy_image_bucket, get_galaxy_file_name, get_files_bucket
from utils.s3_helper import S3Helper
from boto.s3.key import Key


def remove_database_entries(connection, galaxy_name, run_id, galaxy_id):
    pass


def remove_files_with_key(bucket, galaxy_name, run_id, galaxy_id):
    full_key_name = get_galaxy_file_name(galaxy_name, run_id, galaxy_id) + '/'
    for key in bucket.list(prefix=full_key_name):
        # Ignore the key
        if key.key.endswith('/'):
            continue

        bucket.delete_key(key)

    # Now the folder
    key = Key(bucket)
    key.key = full_key_name
    bucket.delete_key(key)


def remove_s3_files(galaxy_name, run_id, galaxy_id):
    """
    Remove the files from S3

    :return:
    """
    s3_helper = S3Helper()
    remove_files_with_key(s3_helper.get_bucket(get_galaxy_image_bucket()), galaxy_name, run_id, galaxy_id)
    remove_files_with_key(s3_helper.get_bucket(get_files_bucket()), galaxy_name, run_id, galaxy_id)
