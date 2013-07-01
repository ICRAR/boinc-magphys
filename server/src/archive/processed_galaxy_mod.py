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

def sort_data(current_jobs):
    """
    Sort the list of jobs
    :param current_jobs:
    :return:
    """
    return_data = {}
    for job_name in current_jobs:
        index = job_name.index('_area')
        galaxy_name = job_name[0:index]

        areas = return_data.get(galaxy_name)
        if areas is None:
            areas = []
            return_data[galaxy_name] = areas

        index1 = job_name.index('_', index + 5)
        area_number = job_name[index + 5 : index1]
        areas.append(area_number)

    return return_data


def finish_processing(galaxy_name, sorted_data):
    """
    Have we finished processing yet
    :param galaxy_name:
    :param sorted_data:
    :return:
    """
    return sorted_data.get(galaxy_name) is None

