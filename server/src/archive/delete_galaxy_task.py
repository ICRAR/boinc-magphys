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
Delete a galaxy and all it's related data.
"""
from __future__ import print_function
import logging
from archive.delete_galaxy_mod import delete_galaxy
from config import DB_LOGIN, STORED
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from database.database_support_core import GALAXY

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# First check the galaxy exists in the database
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()

galaxy_ids = []
for galaxy in connection.execute(select([GALAXY]).where(GALAXY.c.status_id == STORED)):
    galaxy_ids.append(galaxy[GALAXY.c.galaxy_id])

delete_galaxy(connection, galaxy_ids, False)
connection.close()
