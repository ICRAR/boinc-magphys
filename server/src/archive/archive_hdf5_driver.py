#
#    Copyright (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
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
For testing the archiver on a single SED file.
"""

from config import DB_LOGIN
from sqlalchemy import create_engine
from sqlalchemy import select
from database.database_support_core import GALAXY
from archive_hdf5_mod import archive_to_hdf5
import h5py

galaxy_id = 94655
h5_file = h5py.File('testfile', 'w')
galaxy_group = h5_file.create_group('galaxy')
area_group = galaxy_group.create_group('area')
pixel_group = galaxy_group.create_group('pixel')

engine = create_engine(DB_LOGIN)
connection = engine.connect()
galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()

archive_to_hdf5(connection, None, None)

"""
map_parameter_name = {}
for parameter_name in connection.execute(select([PARAMETER_NAME])):
    map_parameter_name[parameter_name[PARAMETER_NAME.c.name]] = parameter_name[PARAMETER_NAME.c.parameter_name_id]

number_filters = get_number_filters(connection, galaxy[GALAXY.c.run_id])

galaxy_file_name = get_galaxy_file_name(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id])

area_count, rad_area_count, int_flux_count = store_area(connection, galaxy_id, area_group)

pixel_count = store_pixels(connection,
                           galaxy_file_name,
                           pixel_group,
                           galaxy[GALAXY.c.dimension_x],
                           galaxy[GALAXY.c.dimension_y],
                           number_filters,
                           area_count, rad_area_count, int_flux_count,  # Now send through the number of other areas
                           galaxy[GALAXY.c.galaxy_id],
                           map_parameter_name)

h5_file.flush()
h5_file.close()
"""
