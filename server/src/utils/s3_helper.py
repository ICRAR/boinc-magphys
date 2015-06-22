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
A helper for putting files into S3 and getting them out again
"""
import ssl
import boto
from boto.s3.key import Key
from utils.logging_helper import config_logger
from config import S3_FILE_RESTORE_TIME

LOG = config_logger(__name__)


# There is a bug in BOTO at the moment
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context


class S3Helper:
    def __init__(self):
        """
        Get an S3 connection
        :return:
        """
        self.s3_connection = boto.connect_s3()

    def get_bucket(self, bucket_name):
        """
        Get a S3 bucket

        :param bucket_name:
        :return:
        """
        return self.s3_connection.get_bucket(bucket_name)

    def add_file_to_bucket(self, bucket_name, key_name, filename, reduced_redundancy=False):
        """
        Add file to a bucket

        :param bucket_name:
        :param key_name:
        :param filename:
        """
        bucket = self.get_bucket(bucket_name)
        key = Key(bucket)
        key.key = key_name
        key.set_contents_from_filename(filename, reduced_redundancy=reduced_redundancy)

    def get_file_from_bucket(self, bucket_name, key_name, file_name):
        """
        Get a file from S3 into a local file

        :param bucket_name:
        :param key_name:
        :param file_name:
        :return:
        """
        bucket = self.get_bucket(bucket_name)
        key = Key(bucket)
        key.key = key_name
        key.get_contents_to_filename(file_name)

    def file_exists(self, bucket_name, key_name):
        """
        Check whether a file exists on s3 by key name.
        :param bucket_name:
        :param key_name:
        :return:
        """

        bucket = self.get_bucket(bucket_name)
        key = Key(bucket)
        key.key = key_name

        return key.exists()

    def file_archived(self, bucket_name, key_name):
        """
        Check whether a file is currenly archived on glacier and NOT available on s3
        :param bucket_name:
        :param key_name:
        :return:
        """
        bucket = self.get_bucket(bucket_name)
        key = Key(bucket)
        key.key = key_name

        if key.storage_class == 'GLACIER' and key.expiry_date is None:
            return True
        else:
            return False

    def file_restoring(self, bucket_name, key_name):
        """
        Check whether a file is currently being restored from glacier to s3
        :param bucket_name:
        :param key_name:
        :return:
        """
        bucket = self.get_bucket(bucket_name)
        key = Key(bucket)
        key.key = key_name

        # Work around to silly bug in boto
        key = bucket.get_key(key_name)

        return key.ongoing_restore

    def restore_archived_file(self, bucket_name, key_name):
        """
        Restores a file that has been archived to glacier back to s3. Can take up to 4 hours
        :param bucket_name:
        :param key_name:
        :return:
        """
        bucket = self.get_bucket(bucket_name)
        key = Key(bucket)
        key.key = key_name

        key.restore(days=S3_FILE_RESTORE_TIME)