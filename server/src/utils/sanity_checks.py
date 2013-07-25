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
When an AMI is spun up we need to make sure that things have started properly, database connections etc.
The bash script should check to make sure the NFS is working as this code is on the NFS

This module contains the code to do this
"""
import logging
import socket
from boto.utils import get_instance_metadata
from sqlalchemy import create_engine, select, func
import time
from config import DB_LOGIN
from database.database_support_core import REGISTER
from utils.name_builder import get_archive_bucket
from utils.s3_helper import S3Helper

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def check_database_connection():
    """
    Check we can connect to the database
    :return:
    """
    try:
        engine = create_engine(DB_LOGIN)
        connection = engine.connect()

        # Read some data
        count = connection.execute(select([func.count(REGISTER.c.register_id)]).where(REGISTER.c.create_time == None)).first()[0]
        LOG.info('DB test count: {0}'.format(count))

        connection.close()

    except Exception:
        # Something when wrong
        LOG.exception('check_database_connection')
        return False

    return True


def access_s3():
    """
    Check we can access the archive bucket
    :return:
    """
    try:
        s3helper = S3Helper()
        bucket = s3helper.get_bucket(get_archive_bucket())
        LOG.info('Access S3 bucket name: {0}'.format(bucket.name))
    except Exception:
        LOG.exception('check_database_connection')
        return False

    return True


def public_ip():
    """
    Check we have a public ip address

    :return:
    """
    found_public_ip = False
    try:
        metadata = get_instance_metadata()
        for key, value in metadata:
            if not value:
                value = "unavailable"

            LOG.info("{0}: {1}".format(key, value))

            if key == 'public-ipv4':
                try:
                    socket.inet_aton(value)
                    found_public_ip = True
                except socket.error:
                    found_public_ip = False

    except Exception:
        LOG.exception('check_database_connection')
        return False
    return found_public_ip


def pass_sanity_checks():
    """
    Do we pass the sanity checks
    :return: True if we pass the sanity checks
    """
    if not check_database_connection():
        return False

    # The IP address might take some time to arrive
    have_public_ip = False
    for i in range(10):
        if public_ip():
            have_public_ip = True
            break
        else:
            time.sleep(5)

    if not have_public_ip:
        return False

    if not access_s3():
        return False

    # If we get here we're good
    return True
