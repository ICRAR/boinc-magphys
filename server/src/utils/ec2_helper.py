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
import random
import boto
import time
from boto.utils import get_instance_metadata
from config import AWS_AMI_ID, AWS_INSTANCE_TYPE, AWS_KEY_NAME, AWS_SECURITY_GROUPS, AWS_SUBNET_IDS

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


class EC2Helper:
    def __init__(self):
        """
        Get an EC2 connection
        :return:
        """
        # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
        self.ec2_connection = boto.connect_ec2()

    def get_all_instances(self, boinc_value):
        """
        Get any instances that are running with the specified BOINC tag

        :param boinc_value: the tag value we are looking for
        :return: list of instances
        """
        return self.ec2_connection.get_all_instances(filters={'tag:BOINC': boinc_value})

    def run_instance(self, user_data, boinc_value):
        """
        Run up an instance

        :param user_data:
        :return:
        """
        random.seed()
        index = random.randint(0, len(AWS_SUBNET_IDS) - 1)
        subnet_id = AWS_SUBNET_IDS[index]
        LOG.info('Running instance: ami: {0}, boinc_value: {1}, subnet_id: {2}'.format(AWS_AMI_ID, boinc_value, subnet_id))
        reservations = self.ec2_connection.run_instances(AWS_AMI_ID,
                                                         instance_type=AWS_INSTANCE_TYPE,
                                                         instance_initiated_shutdown_behavior='terminate',
                                                         subnet_id=subnet_id,
                                                         key_name=AWS_KEY_NAME,
                                                         security_group_ids=AWS_SECURITY_GROUPS,
                                                         user_data=user_data)
        instance = reservations.instances[0]
        time.sleep(5)
        LOG.info('Assigning the tags')
        self.ec2_connection.create_tags([instance.id],
                                        {'BOINC': '{0}'.format(boinc_value),
                                         'Name': 'pogs-{0}'.format(boinc_value),
                                         'Created By': 'pogs'})
        while not instance.update() == 'running':
            LOG.info('Not running yet')
            time.sleep(1)

        LOG.info('Allocating a VPC public IP address')
        allocation = self.ec2_connection.allocate_address('vpc')
        if self.ec2_connection.associate_address(public_ip=None, instance_id=instance.id, allocation_id=allocation.allocation_id):
            LOG.info('Allocated a VPC public IP address')
        else:
            LOG.error('Could not associate the IP to the instance {0}'.format(instance.id))

    def boinc_instance_running(self, boinc_value):
        """
        Is an instance running with this tag?
        :param boinc_value:
        :return:
        """
        reservations = self.get_all_instances(boinc_value)
        count = 0
        for reservation in reservations:
            for instance in reservation.instances:
                LOG.info('instance: {0}, state: {1}'.format(instance.id, instance.state))
                if instance.state == 'pending' or instance.state == 'running':
                    count += 1
        return count > 0

    def release_public_ip(self, boinc_value):
        """
        Release the public IP

        :return:
        """
        association_id, allocation_id = self.get_allocation_id(boinc_value)

        if allocation_id is not None and association_id is not None:
            self.ec2_connection.disassociate_address(association_id=association_id)
            self.ec2_connection.release_address(allocation_id=allocation_id)

    def get_allocation_id(self, boinc_value):
        """
        Get the allocation id
        :return:
        """
        metadata = get_instance_metadata()
        for address in self.ec2_connection.get_all_addresses(filters={'tag:BOINC': boinc_value}):
            if address.public_ip == metadata['public-ipv4']:
                return address.association_id, address.allocation_id

        return None, None
