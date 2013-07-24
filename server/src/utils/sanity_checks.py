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
import urllib
from sqlalchemy import create_engine, select, func
import time
from config import DB_LOGIN
from database.database_support_core import REGISTER
from utils.name_builder import get_archive_bucket
from utils.s3_helper import S3Helper

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


###############################################################################
##
## This code taken from ec2-metadata
##
###############################################################################

METAOPTS = ['ami-id', 'ami-launch-index', 'ami-manifest-path',
            'ancestor-ami-id', 'availability-zone', 'block-device-mapping',
            'instance-id', 'instance-type', 'local-hostname', 'local-ipv4',
            'kernel-id', 'product-codes', 'public-hostname', 'public-ipv4',
            'public-keys', 'ramdisk-id', 'reserveration-id', 'security-groups',
            'user-data']


class Error(Exception):
    pass


class EC2Metadata:
    """Class for querying metadata from EC2"""

    def __init__(self, addr='169.254.169.254', api='2008-02-01'):
        self.addr = addr
        self.api = api

        if not self._test_connectivity(self.addr, 80):
            raise Error("could not establish connection to: %s" % self.addr)

    @staticmethod
    def _test_connectivity(addr, port):
        for i in range(6):
            s = socket.socket()
            try:
                s.connect((addr, port))
                s.close()
                return True
            except socket.error:
                time.sleep(1)

        return False

    def _get(self, uri):
        url = 'http://%s/%s/%s/' % (self.addr, self.api, uri)
        value = urllib.urlopen(url).read()
        if "404 - Not Found" in value:
            return None

        return value

    def get(self, metaopt):
        """return value of metaopt"""

        if metaopt not in METAOPTS:
            raise Error('unknown metaopt', metaopt, METAOPTS)

        if metaopt == 'availability-zone':
            return self._get('meta-data/placement/availability-zone')

        if metaopt == 'public-keys':
            data = self._get('meta-data/public-keys')
            keyids = [line.split('=')[0] for line in data.splitlines()]

            public_keys = []
            for keyid in keyids:
                uri = 'meta-data/public-keys/%d/openssh-key' % int(keyid)
                public_keys.append(self._get(uri).rstrip())

            return public_keys

        if metaopt == 'user-data':
            return self._get('user-data')

        return self._get('meta-data/' + metaopt)

###############################################################################
###############################################################################


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
        m = EC2Metadata()
        for metaopt in METAOPTS:
            value = m.get(metaopt)
            if not value:
                value = "unavailable"

            LOG.info("{0}: {1}".format(metaopt, value))

            if metaopt == 'public-ipv4':
                try:
                    socket.inet_aton(value)
                    found_public_ip = True
                except socket.error:
                    found_public_ip = False

    except Exception:
        LOG.exception('check_database_connection')
        return False
    return found_public_ip


def pass_sanity_checks(logging_file_handler):
    """
    Do we pass the sanity checks
    :return: True if we pass the sanity checks
    """
    LOG.addHandler(logging_file_handler)
    if not check_database_connection():
        return False

    if not public_ip():
        return False

    if not access_s3():
        return False

    # If we get here we're good
    return True
