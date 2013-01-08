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
import logging
import os
import sys
import time
from config import WG_IMAGE_DIRECTORY
from sqlalchemy.sql import select
from database.database_support_core import GALAXY, AREA, PIXEL_RESULT, PIXEL_FILTER, PIXEL_PARAMETER, PIXEL_HISTOGRAM, AREA_USER, FITS_HEADER
from image import directory_mod

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

def remove_file(file):
    """
    Remove a file after checking it exists
    """
    if os.path.isfile(file):
        LOG.info('Removing file {0}'.format(file))
        os.remove(file)
    else:
        LOG.warning('The file {0} does not exist'.format(file))

def delete_galaxy(connection, galaxy_ids, delete_all):
    try:
        for galaxy_id_str in galaxy_ids:
            transaction = connection.begin()
            galaxy_id1 = int(galaxy_id_str)
            galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id1)).first()
            if galaxy is None:
                LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
            else:
                LOG.info('Deleting Galaxy with galaxy_id of %d - %s', galaxy_id1, galaxy[GALAXY.c.name])

                for area_id1 in connection.execute(select([AREA.c.area_id]).where(AREA.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]).order_by(AREA.c.area_id)):
                    LOG.info("Deleting galaxy {0} area {1}".format(galaxy_id_str, area_id1[0]))
                    for pxresult_id1 in connection.execute(select([PIXEL_RESULT.c.pxresult_id]).where(PIXEL_RESULT.c.area_id == area_id1[0]).order_by(PIXEL_RESULT.c.pxresult_id)):
                        sys.stdout.flush()

                        connection.execute(PIXEL_FILTER.delete().where(PIXEL_FILTER.c.pxresult_id == pxresult_id1[0]))
                        connection.execute(PIXEL_PARAMETER.delete().where(PIXEL_PARAMETER.c.pxresult_id == pxresult_id1[0]))
                        connection.execute(PIXEL_HISTOGRAM.delete().where(PIXEL_HISTOGRAM.c.pxresult_id == pxresult_id1[0]))

                    connection.execute(PIXEL_RESULT.delete().where(PIXEL_RESULT.c.area_id == area_id1[0]))
                    connection.execute(AREA_USER.delete().where(AREA_USER.c.area_id == area_id1[0]))

                    transaction.commit()
                    transaction = connection.begin()

                    # Give the rest of the world a chance to access the database
                    time.sleep(10)

                if delete_all:
                    connection.execute(AREA.delete().where(AREA.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]))
                    connection.execute(FITS_HEADER.delete().where(FITS_HEADER.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]))
                    connection.execute(GALAXY.delete().where(GALAXY.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]))

                    file_prefix_name = galaxy[GALAXY.c.name] + "_" + str(galaxy[GALAXY.c.version_number])
                    for i in [1, 2, 3, 4]:
                        file_name = directory_mod.get_colour_image_path(WG_IMAGE_DIRECTORY, file_prefix_name, i, False)
                        remove_file(file_name)

                        file_name = directory_mod.get_thumbnail_colour_image_path(WG_IMAGE_DIRECTORY, file_prefix_name, i, False)
                        remove_file(file_name)

                    fits_file_name = directory_mod.get_file_path(WG_IMAGE_DIRECTORY, file_prefix_name + '.fits', False)
                    remove_file(fits_file_name)

                connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy_id1).values(status_id = 4))

            LOG.info('Galaxy with galaxy_id of %d was deleted', galaxy_id1)
            transaction.commit()

    except Exception:
        LOG.exception('Major error')
