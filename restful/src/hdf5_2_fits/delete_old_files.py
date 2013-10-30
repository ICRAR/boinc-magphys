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
A scheduled task to delete old files
"""
import glob
import os
import time
from hdf5_2_fits import OUTPUT_DIRECTORY
from hdf5_2_fits.to_fits import SpecialTask
from start import celery

_1_DAY = 86400

@celery.task(base=SpecialTask, ignore_result=True, name='delete_old_files.delete')
def delete():
    """
    Delete any old files in the output directory

    :return:
    """
    print 'Delete called'
    now = time.time()
    file_pattern = os.path.join(OUTPUT_DIRECTORY, '*/*.tar.gz')
    for file_name in glob.glob(file_pattern):
        file_time = os.path.getmtime(file_name)

        if file_time < now - 5 * _1_DAY:
            print 'Deleting {0}'.format(file_name)
            os.remove(file_name)
            directory = os.path.dirname(file_name)
            os.rmdir(directory)
