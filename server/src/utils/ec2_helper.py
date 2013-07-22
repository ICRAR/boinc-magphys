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
Helper functions for EC2
"""
import logging
import boto

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

def get_ec2_connection():
    """
    Get an EC2 connection
    :return:
    """
    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    return boto.connect_ec2()


def get_all_instances(ec2_connection, boinc_value):
    """
    Get any instances that are running with the specified BOINC tag

    :param ec2_connection:
    :param boinc_value: the tag value we are looking for
    :return: list of instances
    """
    return ec2_connection.get_all_instances(filters={'tag:BOINC': boinc_value})

def run_instance():
    ec2_connection.run_instances(ami_id, instance_type=INSTANCE_TYPE, subnet_id=env.subnet_id, key_name=KEY_NAME_VPC, security_group_ids=SECURITY_GROUPS_VPC)
