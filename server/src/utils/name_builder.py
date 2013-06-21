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
The various name builders used in the project
"""
from config import WG_PROJECT_NAME


def get_galaxy_image_bucket():
    """
    Return the name of the bucket to hold galaxy images

    :return: the bucket name
    """
    return 'icrar.{0}.galaxy-images'.format(WG_PROJECT_NAME)


def get_sed_file_bucket():
    """
    Return the name of the bucket to hold sed files

    :return: the bucket name
    """
    return 'icrar.{0}.sed-file'.format(WG_PROJECT_NAME)


def get_galaxy_file_name(galaxy_name, galaxy_id, run_id):
    """
    Return the fully formatted galaxy name

    :param galaxy_name:
    :param galaxy_id:
    :param run_id:
    :return: the galaxy name
    """
    return '{0}__{1}__{2}'.format(galaxy_name, run_id, galaxy_id)
