#! /usr/bin/env python2.7
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
Convert layers of the HDF5 file to FITS files
"""

# Setup the Python Path as we may be running this via ssh
import os
import sys

base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))

from config import DB_LOGIN
from database.database_support_core import HDF5_REQUEST
from sqlalchemy import create_engine, select
from hdf5_to_fits.hdf5_to_fits_mod import generate_files, get_features_and_layers
from utils.logging_helper import config_logger

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))

# First check the galaxy exists in the database
engine = create_engine(DB_LOGIN)
connection = engine.connect()

for request in connection.execute(select([HDF5_REQUEST]).where(HDF5_REQUEST.c.state == 0)):
    try:
        # Mark the request as being processed
        request_id = request[HDF5_REQUEST.c.hdf5_request_id]
        connection.execute(HDF5_REQUEST.update().where(HDF5_REQUEST.c.hdf5_request_id == request_id).values(state=1))
        features, layers = get_features_and_layers(connection, request_id)
        if len(features) > 0 and len(layers) > 0:
            url = generate_files(connection=connection,
                                 galaxy_id=request[HDF5_REQUEST.c.galaxy_id],
                                 email=request[HDF5_REQUEST.c.email],
                                 features=features,
                                 layers=layers)
            connection.execute(HDF5_REQUEST.update().where(HDF5_REQUEST.c.hdf5_request_id == request_id).values(state=2, link=url))
        else:
            connection.execute(HDF5_REQUEST.update().where(HDF5_REQUEST.c.hdf5_request_id == request_id).values(state=3))
    except Exception:
        LOG.exception('An exception occurred')
        connection.execute(HDF5_REQUEST.update().where(HDF5_REQUEST.c.hdf5_request_id == request_id).values(state=3))

LOG.info('All done')
connection.close()
