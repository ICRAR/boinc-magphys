#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2015
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
Test the FITS extraction locally
"""
import argparse
import logging
import os

from sqlalchemy import create_engine, select

from config import DB_LOGIN
from database.database_support_core import GALAXY

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


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


def main():
    parser = argparse.ArgumentParser('Get the MD5 of a file')
    parser.add_argument('directory', help='the directory the HDF5 files are in')
    parser.add_argument('galaxy_ids', nargs='+', help='the galaxy ids or 4-30 if you need a range')
    args = parser.parse_args()

    if os.path.exists(args.directory) and os.path.isdir(args.directory):
        process_galaxies(args)
    else:
        LOG.error('The directory {0} does not exist'.format(args.directory))


if __name__ == "__main__":
    main()
