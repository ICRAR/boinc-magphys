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
The module to convert text to CSV
"""
import logging
import csv
from sqlalchemy import create_engine, select, and_
from config import DB_LOGIN
from database.database_support_core import GALAXY

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def correct_name(galaxy_name):
    """
    Corect the name by removing [
    :param galaxy_name:
    :return:
    """
    galaxy_name = galaxy_name.replace('[', '')
    galaxy_name = galaxy_name.replace(']', '')
    return galaxy_name


def convert_file(text_file_name, csv_file_name, run_id, batch_size):
    # Connect to the database
    ENGINE = create_engine(DB_LOGIN)
    connection = ENGINE.connect()

    result_map = {}
    try:
        index = 1
        # Open the text file
        with open(text_file_name, 'r') as text_file:
            results = []
            result_map['{0:03d}'.format(index)] = results
            # For each line
            for line in text_file.readlines():
                elements = line.split()

                galaxy_name = correct_name(elements[0].strip())

                # First check the galaxy exists in the database
                for galaxy in connection.execute(select([GALAXY]).where(and_(GALAXY.c.name == galaxy_name, GALAXY.c.run_id == run_id))):

                    if galaxy is None:
                        LOG.warning('Could not find the galaxy {0}'.format(elements[0].strip()))
                    elif galaxy[GALAXY.c.pixels_processed] == 0:
                        LOG.warning('The galaxy {0} did not have any processed pixels'.format(elements[0].strip()))
                    else:
                        results.append([galaxy_name, galaxy[GALAXY.c.version_number]])

                if len(results) > batch_size:
                    index += 1
                    results = []
                    result_map['{0:03d}'.format(index)] = results
                    LOG.info('Moving to batch {0:03d}'.format(index))

    except Exception as e:
        LOG.exception('Major error', e)

    connection.close()

    # Now write the results
    for key, results in result_map.iteritems():
        with open(csv_file_name.format(key), 'w') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(['Galaxy','ID'])

            for result in results:
                writer.writerow(result)
