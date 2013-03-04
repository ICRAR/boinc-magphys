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
Put back the area user details deleted by accident

http://cortex.ivec.org:7780/QUERY?query=files_list&format=list
cortex.ivec.org:7780/REtrieVE?file_id=NGC3055.hdf5
"""
import logging
import os
import sys

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../server/src')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import argparse
import h5py
from glob import glob
from sqlalchemy import create_engine, func, select
from config import DB_LOGIN
from database.database_support_core import AREA_USER, AREA

class ReadableDir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) != 1:
            raise argparse.ArgumentTypeError("ReadableDir:{0} is not a valid path".format(values))
        prospective_dir=values[0]
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("ReadableDir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("ReadableDir:{0} is not a writeable dir".format(prospective_dir))

parser = argparse.ArgumentParser('Read HDF5 files and put back ')
parser.add_argument('-d','--dir', action=ReadableDir, nargs=1, help='where the HDF5 files are')
args = vars(parser.parse_args())

DIR = args['dir']
if DIR is None:
    parser.print_help()
    exit(1)

# Connect to the databases
engine_aws = create_engine(DB_LOGIN)
connection = engine_aws.connect()

# List the files
path_name = os.path.join(DIR, "*.hdf5")
for file in glob(path_name):
    if os.path.isfile(file):
        LOG.info("Processing {0}".format(file))
        h5_file = h5py.File(file, 'r')
        galaxy_group = h5_file['galaxy']
        galaxy_id = galaxy_group.attrs['galaxy_id']

        # Do we need to do this file
        count = connection.execute(select([func.count(AREA_USER.c.areauser_id)], from_obj=AREA_USER.join(AREA)).where(AREA.c.galaxy_id == galaxy_id)).first()[0]
        if count > 0:
            LOG.info("{0}({1}) has {2} area_user records".format(file, galaxy_id, count))

        else:
            LOG.info("Adding {0}({1})".format(file, galaxy_id, count))
            area_group = galaxy_group['area']
            area_user = area_group['area_user']

            transaction = connection.begin()
            insert = AREA_USER.insert()
            for item in area_user:
                # area_id - 0
                # user_id - 1
                # create_time - 2
                connection.execute(insert, area_id=item[0], userid=item[1], create_time=item[2])
            transaction.commit()

        h5_file.close()
