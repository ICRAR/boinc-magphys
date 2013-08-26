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
Plot data about usage from the BOINC stats
"""
import logging
import argparse
from plots.usage_mod import get_data

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Get all the stats data from theSkyNet POGS data ')
parser.add_argument('output_directory', nargs=1, help='where to put the output files')
args = vars(parser.parse_args())

#ENGINE = create_engine("mysql://" + DB_USER_ID + ":" + DB_PASSWORD + "@127.0.0.1:9870/pogs")
#connection = ENGINE.connect()
#max_id = connection.execute(select([func.max(USER.c.id)])).first()[0]
#connection.close()
#LOG.info('Max Id: %d', max_id)

get_data(args['output_directory'][0])

LOG.info('All Done.')
