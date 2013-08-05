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
The function used to process a galaxy
"""
from sqlalchemy import select
from database.database_support_core import AREA


def build_key(galaxy_name, galaxy_id):
    return '{0}_{1}'.format(galaxy_name, galaxy_id)


def sort_data(connection, current_jobs):
    """
    Sort the list of jobs
    :param current_jobs:
    :return:
    """
    return_data = {}
    for job_name in current_jobs:
        index = job_name.index('_area')
        galaxy_name = job_name[0:index]

        index1 = job_name.index('_', index + 5)
        area_number = job_name[index + 5: index1]

        # Get the area
        area = connection.execute(select([AREA]).where(AREA.c.area_id == area_number)).first()

        key = build_key(galaxy_name, area[AREA.c.galaxy_id])
        areas = return_data.get(key)
        if areas is None:
            areas = []
            return_data[key] = areas

        areas.append(area_number)

    return return_data


def finish_processing(galaxy_name, galaxy_id, sorted_data):
    """
    Have we finished processing yet
    :param galaxy_id:
    :param galaxy_name:
    :param sorted_data:
    :return:
    """
    return sorted_data.get(build_key(galaxy_name, galaxy_id)) is None
