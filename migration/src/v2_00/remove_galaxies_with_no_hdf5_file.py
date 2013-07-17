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
Remove any galaxies that do not have an HDF5 file
"""
import urllib2
import StringIO
import logging
from sqlalchemy import select, create_engine
from config import DB_LOGIN, DELETED
from database.database_support_core import GALAXY, AREA, PIXEL_RESULT, AREA_USER, FITS_HEADER
from v2_00 import DRY_RUN

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def delete_galaxy(connection, galaxy_id):
    if DRY_RUN:
        LOG.info('DRY_RUN: deleting galaxy_id: {0}'.format(galaxy_id))
    else:
        transaction = connection.begin()
        for area_id1 in connection.execute(select([AREA.c.area_id]).where(AREA.c.galaxy_id == galaxy_id).order_by(AREA.c.area_id)):
            connection.execute(PIXEL_RESULT.delete().where(PIXEL_RESULT.c.area_id == area_id1[0]))
            connection.execute(AREA_USER.delete().where(AREA_USER.c.area_id == area_id1[0]))

        connection.execute(AREA.delete().where(AREA.c.galaxy_id == galaxy_id))
        connection.execute(FITS_HEADER.delete().where(FITS_HEADER.c.galaxy_id == galaxy_id))
        connection.execute(GALAXY.delete().where(GALAXY.c.galaxy_id == galaxy_id))

        LOG.info('Galaxy with galaxy_id of %d was deleted', galaxy_id)
        transaction.commit()


def remove_galaxies_with_no_hdf5_file(connection):
    # Get the list of files
    response = urllib2.urlopen("http://cortex.ivec.org:7780/QUERY?query=files_list&format=list")
    web_page = response.read()
    file_set = set()

    # Process each line
    for line in StringIO.StringIO(web_page):
        items = line.split()

        file_name = items[2]
        file_size = items[5]

        if int(file_size) > 0 and file_name not in file_set:
            LOG.info("{0} - {1}".format(file_name, file_size))
            file_set.add(file_name)

    # Check each galaxy
    list_of_galaxies_to_delete = []
    for galaxy in connection.execute(select([GALAXY]).where(GALAXY.c.status_id == DELETED)):
        if galaxy[GALAXY.c.version_number] > 1:
            file_name = '{0}_V{1}.hdf5'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number])
        else:
            file_name = '{0}.hdf5'.format(galaxy[GALAXY.c.name])

        if file_name not in file_set:
            list_of_galaxies_to_delete.append(galaxy[GALAXY.c.galaxy_id])

    for galaxy_id in list_of_galaxies_to_delete:
        delete_galaxy(connection, galaxy_id)

if __name__ == '__main__':
    ENGINE = create_engine(DB_LOGIN)
    connection = ENGINE.connect()

    remove_galaxies_with_no_hdf5_file(connection)

    connection.close()
