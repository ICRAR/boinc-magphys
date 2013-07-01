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

"""
import glob
import logging
import os
import shlex

from sqlalchemy import create_engine, and_
from sqlalchemy.sql import select
import subprocess
from config import DB_LOGIN, STORED
from database.database_support_core import GALAXY

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def get_galaxy_id(file, connection):
    """
    Get the galaxy id from the filename

    :param file:       the filename
    :param connection: the database connection to use
    :return:           the galaxy id
    """
    # Split the file name up
    (head, tail) = os.path.split(file)
    (root, ext) = os.path.splitext(tail)

    # Does the file name end with _V{0-9}
    version_number = 1
    galaxy_name = root
    index = root.rfind('_V')
    if index > 0:
        # Is the rest of the filename digits
        if root[index + 2:].isdigit():
            version_number = int(root[index + 2:])
            galaxy_name = root[:index]

    galaxy = connection.execute(select([GALAXY]).where(and_(GALAXY.c.name == galaxy_name, GALAXY.c.version_number == version_number))).first()
    if galaxy is None:
        return -1

    return galaxy[GALAXY.c.galaxy_id]


def check_ngas_output(output, file):
    """
    Process the output which should look like this

Status of request:

Host:           cortex
Port:           7780
Command:        ARCHIVE

Date:           2013-01-21T09:33:31.696
Error Code:     0
Host ID:        cortex
Message:        Successfully handled Archive Push Request for data file with URI: UGC12000d.hdf5
Status:         SUCCESS
State:          ONLINE
Sub-State:      IDLE
NG/AMS Version: v1.0-MMA/2012-07-27T08:00:00


    :param output: the out put to be processed
    :return:
    """
    lines_processed = 0
    for line in output.split('\n'):
        line1 = line.strip()
        if len(line1) > 0:
            lines_processed += 1
            elements = line1.split(':')

            if line.startswith('Status of request:') :
                # Ignore
                pass
            elif line.startswith('Host:') :
                # Ignore
                pass
            elif line.startswith('Port:') :
                # Ignore
                pass
            elif line.startswith('Command:') :
                if elements[1].strip() != 'ARCHIVE':
                    return False
            elif line.startswith('Date:') :
                # Ignore
                pass
            elif line.startswith('Error Code:') :
                if elements[1].strip() != '0':
                    return False
            elif line.startswith('Host ID:') :
                # Ignore
                pass
            elif line.startswith('Message:') :
                if elements[1].strip() != 'Successfully handled Archive Push Request for data file with URI':
                    return False
                # Second element should be the
                (head, tail) = os.path.split(file)
                if elements[2].strip() != tail:
                    return False
            elif line.startswith('Status:') :
                if elements[1].strip() != 'SUCCESS':
                    return False
            elif line.startswith('State:') :
                if elements[1].strip() != 'ONLINE':
                    return False
            elif line.startswith('Sub-State:') :
                if elements[1].strip() != 'IDLE':
                    return False
            elif line.startswith('NG/AMS Version:') :
                # Ignore
                pass
            else:
                return False

    return lines_processed == 12


def run_command(command, file):
    """
    Execute a command

    :param command: the command to execute
    :return: True if we successfully stored the data
    """
    args = shlex.split(command)
    try:
        output = subprocess.check_output(args)
        LOG.info(output)
        return check_ngas_output(output, file)

    except subprocess.CalledProcessError, e:
        LOG.error(command)
        LOG.error(e.output)
        return False


def store_files(dir, host):
    """
    Scan a directory for files and send them to the archive

    :param dir:  the directory to scan
    :param host: the host to send the file to
    :return:
    """
    LOG.info('Directory: %s', dir)
    LOG.info('Host:      %s', host)

    # Get the work units still being processed
    ENGINE = create_engine(DB_LOGIN)
    connection = ENGINE.connect()

    files = os.path.join(dir, '*.hdf5')
    file_count = 0

    try:
        for file_name in glob.glob(files):
            size = os.path.getsize(file_name)
            galaxy_id = get_galaxy_id(file_name, connection)
            if galaxy_id >= 0:
                LOG.info('File name: %s', file_name)
                LOG.info('File size: %d', size)

                command = '/home/ec2-user/ngas_rt/bin/ngamsCClient -host {0} -port 7780 -cmd ARCHIVE -fileUri {1} -mimeType application/octet-stream'.format(host, file_name)
                LOG.info(command)

                if run_command(command, file_name):
                    LOG.info('File successfully loaded')

                    os.remove(file_name)
                    connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy_id).values(status_id = STORED))
                    file_count += 1

            else:
                LOG.error('File name: %s', file_name)
                LOG.error('File size: %d', size)
                LOG.error('Could not get the galaxy id')

    except Exception:
        LOG.exception('Major error')

    finally:
        connection.close()

    return file_count
