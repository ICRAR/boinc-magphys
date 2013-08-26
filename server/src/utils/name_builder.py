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
The various name builders used in the project
"""
import datetime
from config import POGS_PROJECT_NAME


def get_galaxy_image_bucket():
    """
    Return the name of the bucket to hold galaxy images

    :return: the bucket name
    """
    return 'icrar.{0}.galaxy-images'.format(POGS_PROJECT_NAME)


def get_files_bucket():
    """
    Return the name of the bucket to hold sed files

    :return: the bucket name
    """
    return 'icrar.{0}.files'.format(POGS_PROJECT_NAME)


def get_archive_bucket():
    """
    Return the name of the bucket to hold sed files

    :return: the bucket name
    """
    return 'icrar.{0}.archive'.format(POGS_PROJECT_NAME)


def get_stats_archive_key(key1, key2):
    """
    Return the key to the S3 element
    :param key1:
    :param key2:
    :return:
    """
    return 'stats/{0}/{1}'.format(key1, key2)


def get_log_archive_key(key1, key2):
    """
    Return the key to the S3 element
    :param key1:
    :param key2:
    :return:
    """
    return 'logs/{0}/{1}'.format(key1, key2)


def get_galaxy_file_name(galaxy_name, run_id, galaxy_id):
    """
    Return the fully formatted galaxy name

    :param galaxy_name:
    :param galaxy_id:
    :param run_id:
    :return: the galaxy name
    """
    return '{0}__{1}__{2}'.format(galaxy_name, run_id, galaxy_id)


def get_key_fits(galaxy_name, run_id, galaxy_id):
    """
    Get the key for a fits file

    :param galaxy_name:
    :param galaxy_id:
    :param run_id:
    :return: the key to the fits file
    """
    return '{0}/{0}.fits'.format(get_galaxy_file_name(galaxy_name, run_id, galaxy_id))


def get_key_sigma_fits(galaxy_name, run_id, galaxy_id):
    """
    Get the key for a fits sigma file

    :param galaxy_name:
    :param galaxy_id:
    :param run_id:
    :return: the key to the fits file
    """
    return '{0}/{0}.sigma.fits'.format(get_galaxy_file_name(galaxy_name, run_id, galaxy_id))


def get_key_hdf5(galaxy_name, run_id, galaxy_id):
    """
    Get the key for an HDF5 file

    :param galaxy_name:
    :param galaxy_id:
    :param run_id:
    :return: the key to the fits file
    """
    return '{0}/{0}.hdf5'.format(get_galaxy_file_name(galaxy_name, run_id, galaxy_id))


def get_key_sed(galaxy_name, run_id, galaxy_id, area_id):
    """
    Get the key for an SED file

    :param area_id:
    :param galaxy_name:
    :param galaxy_id:
    :param run_id:
    :return: the key to the fits file
    """
    return '{0}/sed/{1}.sed'.format(get_galaxy_file_name(galaxy_name, run_id, galaxy_id), area_id)


def get_colour_image_key(galaxy_key_prefix, colour):
    """
    Generates the key to the file given by the colour id
    :param galaxy_key_prefix:
    :param colour:
    """
    return galaxy_key_prefix + "/colour_" + str(colour) + ".png"


def get_thumbnail_colour_image_key(galaxy_key_prefix, colour):
    """
    Generates the thumbnail key
    :param galaxy_key_prefix:
    :param colour:
    """
    return galaxy_key_prefix + "/tn_colour_" + str(colour) + ".png"


def get_build_png_name(galaxy_key_prefix, parameter):
    """
    Generates the dynamic build png name

    :param galaxy_key_prefix:
    :param parameter:
    :return:
    """
    return galaxy_key_prefix + "/" + parameter + ".png"


def get_ami_log_file(name):
    filename = '{0}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    full_filename = '/home/ec2-user/logs_ami/{0}_{1}'.format(name, filename)
    return filename, full_filename
