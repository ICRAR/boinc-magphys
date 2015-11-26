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
The routines used to archive the data
"""
from sqlalchemy import create_engine
from archive.archive_hdf5_mod import archive_to_hdf5 #TODO Change back to archive_hdf5_mod
from archive.delete_galaxy_mod import delete_galaxy_data, delete_register_data
from archive.processed_galaxy_mod import processed_data
from archive.store_files_mod import store_files
from utils.logging_helper import config_logger
from config import DB_LOGIN, ARCHIVE_DATA_DICT
from utils.ec2_helper import EC2Helper
from utils.shutdown_detection import start_poll

LOG = config_logger(__name__)
ARCHIVE_DATA = 'archive_data_{0}'

USER_DATA = '''#!/bin/bash

# Sleep for a while to let everything settle down
sleep 10s

# Has the NFS mounted properly?
if [ -d '/home/ec2-user/boinc-magphys/server' ]
then
    # We are root so we have to run this via sudo to get access to the ec2-user details
    su -l ec2-user -c 'python2.7 /home/ec2-user/boinc-magphys/server/src/archive/archive_task.py ami {0}'
fi

# All done terminate
shutdown -h now
'''


def process_boinc(modulus, remainder):
    """
    We're running the process on the BOINC server.

    Check if an instance is still running, if not start it up.
    :return:
    """
    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    ec2_helper = EC2Helper()

    archive_data_format = ARCHIVE_DATA.format(remainder)
    if ec2_helper.boinc_instance_running(archive_data_format):
        LOG.info('A previous instance is still running')
    else:
        LOG.info('Starting up the instance')
        instance_type = ARCHIVE_DATA_DICT['instance_type']
        max_price = float(ARCHIVE_DATA_DICT['price'])
        if instance_type is None or max_price is None:
            LOG.error('Instance type and price not set up correctly')
        else:
            bid_price, subnet_id = ec2_helper.get_cheapest_spot_price(instance_type, max_price)
            # Do we need remainder text?
            if modulus is None:
                mod_text = ''
            else:
                mod_text = '-mod {0} {1}'.format(modulus, remainder)

            if bid_price is not None and subnet_id is not None:
                ec2_helper.run_spot_instance(bid_price, subnet_id, USER_DATA.format(mod_text), archive_data_format, instance_type, remainder)


def process_ami(modulus, remainder):
    """
    We're running on the AMI instance - so actually do the work

    Find the files and move them to S3
    :return:
    """
    # Connect to the database - the login string is set in the database package

    # Start the shutdown signal poller to check when this instance must close
    start_poll()

    engine = create_engine(DB_LOGIN)
    connection = engine.connect()
    try:
        # Check the processed data
        try:
            LOG.info('Updating state information')
            processed_data(connection, modulus, remainder)
        except Exception:
            LOG.exception('processed_data(): an exception occurred')

        # Store files
        try:
            LOG.info('Storing files')
            store_files(connection, modulus, remainder)
        except Exception:
            LOG.exception('store_files(): an exception occurred')

        # Delete galaxy data - commits happen inside
        try:
            LOG.info('Deleting galaxy data')
            delete_galaxy_data(connection, modulus, remainder)
        except Exception:
            LOG.exception('delete_galaxy_data(): an exception occurred')

        # Delete register data - commits happen inside
        try:
            LOG.info('Deleting register data')
            delete_register_data(connection, modulus, remainder)
        except Exception:
            LOG.exception('delete_register_data(): an exception occurred')

        # Archive to HDF5
        try:
            LOG.info('Archiving to HDF5')
            archive_to_hdf5(connection, modulus, remainder)
        except Exception:
            LOG.exception('archive_to_hdf5(): an exception occurred')

    except SystemExit:
        LOG.info('Spot Instance Terminate Notice received, archive_task is shutting down')

    finally:
        connection.close()
