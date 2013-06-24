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
A helper for putting files into S3 and getting them out again
"""
import logging
import boto
from boto.s3.key import Key

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def get_s3_connection():
    """
    Get an S3 connection
    :return:
    """
    return boto.connect_s3()


def get_bucket(s3_connection, bucket_name):
    """
    Get a S3 bucket

    :param s3_connection:
    :param bucket_name:
    :return:
    """
    return s3_connection.get_bucket(bucket_name)


def add_file_to_bucket(bucket, key_name, filename):
    """
    Add file to a bucket

    :param bucket:
    :param key_name:
    :param filename:
    :return:
    """
    key = Key(bucket)
    key.key = key_name
    key.set_contents_from_filename(filename)
