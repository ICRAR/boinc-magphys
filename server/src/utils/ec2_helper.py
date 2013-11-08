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
Helper functions for EC2
"""
import random
import boto
import time
import datetime
from boto.utils import get_instance_metadata
from utils.logging_helper import config_logger
from config import AWS_AMI_ID, AWS_KEY_NAME, AWS_SECURITY_GROUPS, AWS_SUBNET_IDS, AWS_M1_SMALL_DICT, AWS_SUBNET_DICT, AWS_M1_MEDIUM_DICT, M1_MEDIUM, M1_SMALL

LOG = config_logger(__name__)


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

    def run_instance(self, user_data, boinc_value, instance_type):
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
                                                         instance_type=instance_type,
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

        LOG.info('Allocating a VPC public IP address')
        allocation = self.ec2_connection.allocate_address('vpc')
        while not instance.update() == 'running':
            LOG.info('Not running yet')
            time.sleep(1)

        if self.ec2_connection.associate_address(public_ip=None, instance_id=instance.id, allocation_id=allocation.allocation_id):
            LOG.info('Allocated a VPC public IP address')
        else:
            LOG.error('Could not associate the IP to the instance {0}'.format(instance.id))
            self.ec2_connection.release_address(allocation_id=allocation.allocation_id)

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

    def release_public_ip(self):
        """
        Release the public IP

        :return:
        """
        association_id, allocation_id = self.get_allocation_id()

        if allocation_id is not None and association_id is not None:
            self.ec2_connection.disassociate_address(association_id=association_id)
            self.ec2_connection.release_address(allocation_id=allocation_id)

    def get_allocation_id(self):
        """
        Get the allocation id
        :return:
        """
        metadata = get_instance_metadata()
        for address in self.ec2_connection.get_all_addresses():
            if address.public_ip == metadata['public-ipv4']:
                return address.association_id, address.allocation_id

        return None, None

    def run_spot_instance(self, spot_price, subnet_id, user_data, boinc_value, instance_type):
        """
        Run the ami as a spot instance

        :param spot_price: The best spot price history
        :param user_data:
        :param boinc_value:
        :return:
        """
        now_plus = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        spot_request = self.ec2_connection.request_spot_instances(spot_price,
                                                                  image_id=AWS_AMI_ID,
                                                                  count=1,
                                                                  valid_until=now_plus.isoformat(),
                                                                  instance_type=instance_type,
                                                                  subnet_id=subnet_id,
                                                                  key_name=AWS_KEY_NAME,
                                                                  security_group_ids=AWS_SECURITY_GROUPS,
                                                                  user_data=user_data)

        # Wait for EC2 to provision the instance
        instance_id = None
        while instance_id is None:
            spot_request_id = spot_request[0].id
            requests = self.ec2_connection.get_all_spot_instance_requests(request_ids=[spot_request_id])
            LOG.info('{0}, state: {1}, status:{2}'.format(spot_request_id, requests[0].state, requests[0].status))
            if requests[0].state == 'active' and requests[0].status.code == 'fulfilled':
                instance_id = requests[0].instance_id
            elif requests[0].state == 'cancelled':
                raise CancelledException('Request {0} cancelled. Status: {1}'.format(spot_request_id, requests[0].status))
            else:
                time.sleep(10)

        # Give it time to settle down
        LOG.info('Assigning the tags')
        self.ec2_connection.create_tags([instance_id],
                                        {'BOINC': '{0}'.format(boinc_value),
                                         'Name': 'pogs-{0}'.format(boinc_value),
                                         'Created By': 'pogs'})

        reservations = self.ec2_connection.get_all_instances(instance_ids=[instance_id])
        instance = reservations[0].instances[0]

        LOG.info('Allocating a VPC public IP address')
        allocation = self.ec2_connection.allocate_address('vpc')
        while not instance.update() == 'running':
            LOG.info('Not running yet')
            time.sleep(1)

        if self.ec2_connection.associate_address(public_ip=None, instance_id=instance_id, allocation_id=allocation.allocation_id):
            LOG.info('Allocated a VPC public IP address')
        else:
            LOG.error('Could not associate the IP to the instance {0}'.format(instance_id))
            self.ec2_connection.release_address(allocation_id=allocation.allocation_id)

    def get_cheapest_spot_price(self, instance_type):
        """
        Find the cheapest spot price in a zone we use

        :param instance_type:
        :return:
        """
        LOG.info('instance_type: {0}'.format(instance_type))
        prices = self.ec2_connection.get_spot_price_history(start_time=datetime.datetime.now().isoformat(),
                                                            instance_type=instance_type,
                                                            product_description='Linux/UNIX (Amazon VPC)')

        # Get the zones we have subnets in
        availability_zones = []
        for key, value in AWS_SUBNET_DICT.iteritems():
            availability_zones.append(value['availability_zone'])

        best_price = None
        for spot_price in prices:
            LOG.info('Spot Price {0} - {1}'.format(spot_price.price, spot_price.availability_zone))
            if spot_price.availability_zone not in availability_zones:
                # Ignore this one
                LOG.info('Ignoring spot price {0} - {1}'.format(spot_price.price, spot_price.availability_zone))
            elif spot_price.price != 0.0 and best_price is None:
                best_price = spot_price
            elif spot_price.price != 0.0 and spot_price.price < best_price.price:
                best_price = spot_price
        if best_price is None:
            LOG.info('No Spot Price')
            return None, None

        # put the bid price at 20% more than the current price
        bid_price = best_price.price * 1.2
        if instance_type == M1_SMALL:
            max_price = float(AWS_M1_SMALL_DICT['price'])
        elif instance_type == M1_MEDIUM:
            max_price = float(AWS_M1_MEDIUM_DICT['price'])
        else:
            max_price = 0.0

        # The spot price is too high
        LOG.info('bid_price: {0}, max_price: {1}, instance: {2}'.format(bid_price, max_price, instance_type))
        if bid_price > max_price:
            LOG.info('Spot Price too high')
            return None, None

        LOG.info('Spot Price {0} - {1}'.format(best_price.price, best_price.availability_zone))

        # Now get the subnet id
        subnet_id = None
        for key, value in AWS_SUBNET_DICT.iteritems():
            if value['availability_zone'] == best_price.availability_zone:
                subnet_id = key
                break

        LOG.info('bid_price: {0}, subnet_id: {1}'.format(bid_price, subnet_id))
        return bid_price, subnet_id


class CancelledException(Exception):
    """
    The request has been cancelled
    """
    pass
