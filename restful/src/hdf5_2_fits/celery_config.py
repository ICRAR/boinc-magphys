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
The Configuration of the celery system
"""


class Config:
    """
    The configuration class
    """
    ## Broker settings.
    BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://'

    # List of modules to import when celery starts.
    CELERY_IMPORTS = ('hdf5_2_fits.to_fits', 'hdf5_2_fits.delete_old_files',)

    # General options
    CELERY_ENABLE_UTC = True
    CELERY_CHORD_PROPAGATES = True
    CELERY_TASK_PUBLISH_RETRY = True
    CELERY_TASK_PUBLISH_RETRY_POLICY = {
        'max_retries': 2,
        'interval_start': 10,
        'interval_step': 10,
        'interval_max': 10,
        }
#    CELERY_TASK_PUBLISH_RETRY_POLICY = {
#        'max_retries': 10,
#        'interval_start': 300,
#        'interval_step': 7200,
#        'interval_max': 86400,
#        }
    CELERYBEAT_SCHEDULE = {
        'delete-old-files': {
            'task': 'delete_old_files.delete',
            'schedule': 21600,
#            'schedule': 30,
            'args': ()
        },
    }
