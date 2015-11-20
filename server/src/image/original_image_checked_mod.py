#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2016
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
The code to check the original images created correctly
"""
import datetime
import os
import tempfile
from sqlalchemy import create_engine, select, and_, func
from config import DB_LOGIN, ORIGINAL_IMAGE_CHECKED_DICT, ORIGINAL_IMAGE_CHECKED
from database.database_support_core import GALAXY
from image.fitsimage import FitsImage
from utils.ec2_helper import EC2Helper
from utils.logging_helper import config_logger
from utils.name_builder import get_galaxy_file_name, get_galaxy_image_bucket, get_saved_files_bucket
from utils.s3_helper import S3Helper


LOG = config_logger(__name__)

USER_DATA = '''#!/bin/bash

# Sleep for a while to let everything settle down
sleep 10s

# Has the NFS mounted properly?
if [ -d '/home/ec2-user/boinc-magphys/server' ]
then
    # We are root so we have to run this via sudo to get access to the ec2-user details
    su -l ec2-user -c 'python2.7 /home/ec2-user/boinc-magphys/server/src/image/original_image_checked.py ami'
fi

# All done terminate
shutdown -h now
'''
IMAGE_FILES = ['colour_1.png', 'colour_2.png', 'colour_3.png', 'colour_4.png', 'tn_colour_1.png']


def original_image_checked_boinc():
    """
    We're running the process on the BOINC server.

    Check if an instance is still running, if not start it up.
    :return:
    """
    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    ec2_helper = EC2Helper()

    if ec2_helper.boinc_instance_running(ORIGINAL_IMAGE_CHECKED_DICT):
        LOG.info('A previous instance is still running')
    else:
        # Connect to the database - the login string is set in the database package
        engine = create_engine(DB_LOGIN)
        connection = engine.connect()

        try:
            count = connection.execute(select([func.count(GALAXY.c.galaxy_id)]).where(and_(GALAXY.c.original_image_checked == None, GALAXY.c.pixel_count > 0))).first()[0]
            LOG.info('{0} images to check'.format(count))
            if count > 0:
                LOG.info('Starting up the instance')
                instance_type = ORIGINAL_IMAGE_CHECKED_DICT['instance_type']
                if instance_type is None:
                    LOG.error('Instance type not set up correctly')
                else:
                    ec2_helper.run_instance(USER_DATA, ORIGINAL_IMAGE_CHECKED, instance_type)
        except Exception:
            LOG.exception('Major error')

        finally:
            connection.close()


def image_files_exist(galaxy_name, run_id, galaxy_id, s3_helper):
    """
    Check if the images exist
    :param galaxy_name:
    :param run_id:
    :param galaxy_id:
    :return:
    """
    bucket = s3_helper.get_bucket(get_galaxy_image_bucket())
    galaxy_file_name = get_galaxy_file_name(galaxy_name, run_id, galaxy_id)
    for image_file in IMAGE_FILES:
        key_name = '{0}/{1}'.format(galaxy_file_name, image_file)
        key = bucket.get_key(key_name)
        if key is None:
            return False

    # if we get here we found them all
    return True


def regenerated_original_images(galaxy_name, run_id, galaxy_id, s3_helper, connection):
    """
    We need to regenerate the image
    :param galaxy_name:
    :param run_id:
    :param galaxy_id:
    :return: if we succeed
    """
    all_ok = False

    # Get the fits file
    bucket = s3_helper.get_bucket(get_saved_files_bucket())
    galaxy_file_name = get_galaxy_file_name(galaxy_name, run_id, galaxy_id)
    key_name = '{0}/{0}.fits'.format(galaxy_name)
    key = bucket.get_key(key_name)
    if key is None:
        LOG.error('The fits file does not seem to exists')
        return all_ok

    path_name = get_temp_file('fits')
    key.get_contents_to_filename(path_name)

    # Now regenerate
    try:
        image = FitsImage(connection)
        image.build_image(path_name, galaxy_file_name, galaxy_id, get_galaxy_image_bucket())
        all_ok = True
    except Exception:
        LOG.exception('Major error')
        all_ok = False
    finally:
        os.remove(path_name)
    return all_ok


def get_temp_file(extension):
    """
    Get a temporary file
    """
    tmp = tempfile.mkstemp(extension, 'galaxy', None, False)
    tmp_file = tmp[0]
    os.close(tmp_file)
    return tmp[1]


def original_image_checked_ami():
    """
    We're running in the AMI instance - so do the actual work

    Check the newly created images to make sure the images have been created
    :return:
    """
    # Connect to the database - the login string is set in the database package
    engine = create_engine(DB_LOGIN)
    connection = engine.connect()

    s3helper = S3Helper()
    try:
        # Look in the database for the galaxies
        galaxy_ids = []
        for galaxy in connection.execute(select([GALAXY]).where(and_(GALAXY.c.original_image_checked == None, GALAXY.c.pixel_count > 0)).order_by(GALAXY.c.galaxy_id)):
            galaxy_ids.append(galaxy[GALAXY.c.galaxy_id])

        for galaxy_id in galaxy_ids:
            galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == galaxy_id)).first()

            if not image_files_exist(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id], s3helper):
                mark_as_checked = regenerated_original_images(galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id], s3helper, connection)
            else:
                mark_as_checked = True

            if mark_as_checked:
                connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy_id).values(original_image_checked=datetime.datetime.now()))

    except Exception:
        LOG.exception('Major error')

    finally:
        connection.close()
