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

import datetime
from config import DB_LOGIN
from database.database_support_core import HDF5_REQUEST, HDF5_REQUEST_GALAXY
from sqlalchemy import create_engine, select
from hdf5_to_fits.hdf5_to_fits_mod import generate_files, get_features_layers_galaxies
from utils.logging_helper import config_logger

LOG = config_logger(__name__)
LOG.info('Starting HDF5 to FITS')
LOG.info('PYTHONPATH = {0}'.format(sys.path))

# First check the galaxy exists in the database
engine = create_engine(DB_LOGIN)
connection = engine.connect()

for request in connection.execute(select([HDF5_REQUEST], distinct=True, from_obj=HDF5_REQUEST.join(HDF5_REQUEST_GALAXY)).where(HDF5_REQUEST_GALAXY.c.state == 0)):
    # Mark the request as being processed
    request_id = request[HDF5_REQUEST.c.hdf5_request_id]
    features, layers, hdf5_request_galaxy_ids = get_features_layers_galaxies(connection, request_id)
    if len(features) > 0 and len(layers) > 0 and len(hdf5_request_galaxy_ids) > 0:
        LOG.info('Processing request from profile id: {0}, request made at {1}'.format(request[HDF5_REQUEST.c.profile_id], request[HDF5_REQUEST.c.created_at]))
        LOG.info('{0} features, {1} layers {2} galaxies'.format(len(features), len(layers), len(hdf5_request_galaxy_ids)))
        generate_files(connection=connection,
                       hdf5_request_galaxy_ids=hdf5_request_galaxy_ids,
                       email=request[HDF5_REQUEST.c.email],
                       features=features,
                       layers=layers)
        connection.execute(HDF5_REQUEST.update().where(HDF5_REQUEST.c.hdf5_request_id == request_id).values(updated_at=datetime.datetime.now()))
    else:
        LOG.info('Nothing to do')
LOG.info('All done')
connection.close()
