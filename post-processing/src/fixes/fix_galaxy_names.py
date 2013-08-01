#! /usr/bin/env python2.7
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
Fix the galaxy names
"""
import logging
import os
import sys

DRY_RUN = True
LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../server/src')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

from boto.s3.key import Key
from config import DB_LOGIN
from sqlalchemy import create_engine, select
from database.database_support_core import GALAXY
from utils.s3_helper import S3Helper
from utils.name_builder import get_files_bucket, get_galaxy_image_bucket, get_galaxy_file_name

# Connect to the database - the login string is set in the database package
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()


def needs_fixing(name):
    """
    Does the name need fixing?
    :param name:
    :return:
    """
    last_char = name[-1]
    if last_char == 'a' or last_char == 'b' or last_char == 'c' or last_char == 'd' or last_char == 'e' or last_char == 'f' or last_char == 'g':
        return True

    return False


def build_file_key(galaxy_name, run_id, galaxy_id, extension):
    """
    Build the key

    :param galaxy_name:
    :param run_id:
    :param galaxy_id:
    :param extension:
    :return:
    """
    return '{0}/{0}.{1}'.format(get_galaxy_file_name(galaxy_name, run_id, galaxy_id), extension)


def build_image_key(galaxy_name, run_id, galaxy_id, file_name):
    """
    Build the image key
    :param galaxy_name:
    :param run_id:
    :param galaxy_id:
    :param file_name:
    :return:
    """
    return '{0}/{1}'.format(get_galaxy_file_name(galaxy_name, run_id, galaxy_id), file_name)


def move_file(new_key, old_key, bucket):
    """
    Move the files

    :param new_key:
    :param old_key:
    :return:
    """
    key = Key(bucket)
    key.key = old_key
    if key.exists():
        if DRY_RUN:
            LOG.info('DRY_RUN: old: {0}, new: {1}'.format(old_key, new_key))
        else:
            key = Key(bucket)
            key.key = old_key
            key.copy(bucket, new_key)
            key.delete()
    else:
        LOG.warning('The key {0} does not exist'.format(old_key))


def copy_files(old_name, new_name, run_id, galaxy_id, extension, bucket):
    """
    Copy the file to a new key and delete the original

    :param old_name:
    :param new_name:
    :param run_id:
    :param galaxy_id:
    :param extension:
    :return:
    """
    old_key = build_file_key(old_name, run_id, galaxy_id, extension)
    new_key = build_file_key(new_name, run_id, galaxy_id, extension)
    move_file(new_key, old_key, bucket)


def copy_galaxy_images(old_name, new_name, run_id, galaxy_id, file_name, bucket):
    """
    Copy galaxy images

    :param old_name:
    :param new_name:
    :param run_id:
    :param galaxy_id:
    :param file_name:
    :return:
    """
    old_key = build_image_key(old_name, run_id, galaxy_id, file_name)
    new_key = build_image_key(new_name, run_id, galaxy_id, file_name)
    move_file(new_key, old_key, bucket)


def remove_folder(bucket, folder):
    key = Key(bucket)
    key.key = folder
    if key.exists():
        if DRY_RUN:
            LOG.info('DRY_RUN: Removing {0}'.format(folder))
        else:
            key.delete()
    else:
        LOG.warning('The key {0} does not exist'.format(folder))


def remove_files_folder(old_name, run_id, galaxy_id, bucket):
    """
    Remove the folder
    :param old_name:
    :param run_id:
    :param galaxy_id:
    :return:
    """
    remove_folder(bucket, get_galaxy_file_name(old_name, run_id, galaxy_id) + '/')


def remove_galaxy_images_folder(old_name, run_id, galaxy_id, bucket):
    """
    Remove the folder
    :param old_name:
    :param run_id:
    :param galaxy_id:
    :return:
    """
    remove_folder(bucket, get_galaxy_file_name(old_name, run_id, galaxy_id) + '/')


def fix_galaxy(galaxy, bucket_files, bucket_galaxy_image):
    """
    Fix the galaxy name

    :param galaxy:
    :return:
    """
    old_name = galaxy[GALAXY.c.name]
    new_name = old_name[:-1]
    galaxy_id = galaxy[GALAXY.c.galaxy_id]
    run_id = galaxy[GALAXY.c.run_id]
    LOG.info('Fixing {0}({1}) t0 {2}'.format(old_name, galaxy_id, new_name))
    for extension in ['fits', 'hdf5']:
        copy_files(old_name, new_name, run_id, galaxy_id, extension, bucket_files)
    remove_files_folder(old_name, run_id, galaxy_id, bucket_files)

    for file_name in ['colour_1.png', 'colour_2.png', 'colour_3.png', 'colour_4.png', 'ldust.png', 'm.png', 'mu.png', 'sfr.png', 'tn_colour_1.png']:
        copy_galaxy_images(old_name, new_name, run_id, galaxy_id, file_name, bucket_galaxy_image)
    remove_galaxy_images_folder(old_name, run_id, galaxy_id, bucket_galaxy_image)

    if DRY_RUN:
        LOG.info('Updating {0} to {1}'.format(galaxy_id, new_name))
    else:
        connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy_id).values(name=new_name))


for galaxy in connection.execute(select([GALAXY])):
    s3helper = S3Helper()
    bucket_files = s3helper.get_bucket(get_files_bucket())
    bucket_galaxy_image = s3helper.get_bucket(get_galaxy_image_bucket())

    if needs_fixing(galaxy[GALAXY.c.name]):
        fix_galaxy(galaxy, bucket_files, bucket_galaxy_image)

connection.close()
