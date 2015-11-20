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
Functions used to delete a galaxy
"""
import time
from boto.s3.key import Key
import datetime
from sqlalchemy.sql import select, func, and_
from utils.logging_helper import config_logger
from config import DELETED, ARC_DELETE_DELAY, STORED
from database.database_support_core import GALAXY, AREA, PIXEL_RESULT, FITS_HEADER, REGISTER, TAG_REGISTER
from utils.name_builder import get_galaxy_file_name, get_sed_files_bucket
from utils.s3_helper import S3Helper
from utils.shutdown_detection import shutdown

LOG = config_logger(__name__)


def delete_galaxy(connection, galaxy_ids):
    for galaxy_id in galaxy_ids:
        transaction = connection.begin()
        galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()
        if galaxy is None:
            LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id)
        else:
            LOG.info('Deleting Galaxy with galaxy_id of %d - %s', galaxy_id, galaxy[GALAXY.c.name])
            area_count = connection.execute(select([func.count(AREA.c.area_id)]).where(AREA.c.galaxy_id == galaxy[GALAXY.c.galaxy_id])).first()[0]
            counter = 1

            for area_id1 in connection.execute(select([AREA.c.area_id]).where(AREA.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]).order_by(AREA.c.area_id)):
                LOG.info("Deleting galaxy {0} area {1}. {2} of {3}".format(galaxy_id, area_id1[0], counter, area_count))
                connection.execute(PIXEL_RESULT.delete().where(PIXEL_RESULT.c.area_id == area_id1[0]))

                # Give the rest of the world a chance to access the database
                time.sleep(0.1)
                counter += 1

                if shutdown() is True:
                    transaction.rollback()
                    raise SystemExit

            LOG.info("Deleting FITS headers for galaxy {0}".format(galaxy_id))
            connection.execute(FITS_HEADER.delete().where(FITS_HEADER.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]))

            # Now empty the bucket of the sed files
            s3helper = S3Helper()
            bucket = s3helper.get_bucket(get_sed_files_bucket())
            galaxy_file_name = get_galaxy_file_name(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id])
            for key in bucket.list(prefix='{0}/'.format(galaxy_file_name)):
                # Ignore the key
                if key.key.endswith('/'):
                    continue

                bucket.delete_key(key)

                if shutdown() is True:
                    transaction.rollback()
                    raise SystemExit

            # Now the folder
            key = Key(bucket)
            key.key = '{0}/'.format(galaxy_file_name)
            bucket.delete_key(key)

        LOG.info('Galaxy with galaxy_id of %d was deleted', galaxy_id)
        connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy_id).values(status_id=DELETED, status_time=datetime.datetime.now()))

        if shutdown() is True:
            transaction.rollback()
            raise SystemExit

        transaction.commit()


def delete_galaxy_data(connection, modulus, remainder):
    """
    Delete galaxies after a period of time

    :param connection:
    :return:
    """
    delete_delay_ago = datetime.datetime.now() - datetime.timedelta(days=float(ARC_DELETE_DELAY))
    LOG.info('Deleting galaxies: {0} days ago ({1})'.format(ARC_DELETE_DELAY, delete_delay_ago))

    galaxy_ids = []
    for galaxy in connection.execute(select([GALAXY]).where(and_(GALAXY.c.status_id == STORED, GALAXY.c.status_time < delete_delay_ago)).order_by(GALAXY.c.galaxy_id)):
        galaxy_id = int(galaxy[GALAXY.c.galaxy_id])
        if modulus is None or galaxy_id % modulus == remainder:
            galaxy_ids.append(galaxy_id)

    if shutdown() is True:
        raise SystemExit

    delete_galaxy(connection, galaxy_ids)


def delete_register_entries(connection, register_ids):
    for register_id in register_ids:
        transaction = connection.begin()
        register = connection.execute(select([REGISTER]).where(REGISTER.c.register_id == register_id)).first()
        if register is None:
            LOG.info('Error: Register entry with register_id of %d was not found', register_id)
        else:
            LOG.info("Deleting tags for register entry {0}".format(register_id))
            connection.execute(TAG_REGISTER.delete().where(TAG_REGISTER.c.register_id == register_id))

            LOG.info('Deleting register entry with register_id of %d - %s', register_id, register[REGISTER.c.galaxy_name])
            connection.execute(REGISTER.delete().where(REGISTER.c.register_id == register_id))

        transaction.commit()


def delete_register_data(connection, modulus, remainder):
    """
    Delete register entries

    :param connection:
    :param modulus:
    :param remainder:
    :return:
    """
    delete_delay_ago = datetime.datetime.now() - datetime.timedelta(days=float(ARC_DELETE_DELAY))
    LOG.info('Deleting registrations: {0} days ago ({1})'.format(ARC_DELETE_DELAY, delete_delay_ago))

    register_ids = []
    for register in connection.execute(select([REGISTER]).where(and_(REGISTER.c.create_time is not None, REGISTER.c.create_time < delete_delay_ago)).order_by(REGISTER.c.register_id)):
        register_id = int(register[REGISTER.c.register_id])

        if modulus is None or register_id % modulus == remainder:
            register_ids.append(register_id)

        if shutdown() is True:
            raise SystemExit

    delete_register_entries(connection, register_ids)
