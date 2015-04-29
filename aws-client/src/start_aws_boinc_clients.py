#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2015
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
Start up a number of AMI's to run as BOINC clients
"""

import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import boto
import boto.ec2
from boto.exception import EC2ResponseError
from os.path import exists, join, expanduser
import datetime
import time


AWS_REGION = 'ap-southeast-2'
AWS_SUBNETS = {
    'ap-southeast-2a': 'subnet-878cc2ee',
    'ap-southeast-2b': 'subnet-848cc2ed'
}
AWS_KEY_NAME = 'icrar_sydney'
AWS_SECURITY_GROUPS = ['sg-be7ccfdb']


LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


class CancelledException(Exception):
    """
    The request has been cancelled
    """
    pass


class EC2Helper:
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        """
        Get an EC2 connection
        """
        if aws_access_key_id is not None and aws_secret_access_key is not None:
            LOG.info("Using user provided keys")
            self.ec2_connection = boto.ec2.connect_to_region(AWS_REGION, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        elif exists(join(expanduser('~'), '.aws/credentials')):
            # This relies on a ~/.aws/credentials file holding the '<aws access key>', '<aws secret key>'
            LOG.info("Using ~/.aws/credentials")
            self.ec2_connection = boto.ec2.connect_to_region(AWS_REGION, profile_name='theSkyNet')
        else:
            # This relies on a ~/.boto or /etc/boto.cfg file holding the '<aws access key>', '<aws secret key>'
            LOG.info("Using ~/.boto or /etc/boto.cfg")
            self.ec2_connection = boto.ec2.connect_to_region(AWS_REGION)

    def get_cheapest_spot_price(self, instance_type, max_price):
        """
        Find the cheapest spot price in a zone we use

        :param instance_type:
        :return:
        """
        LOG.info('instance_type: {0}'.format(instance_type))
        # Get the zones we have subnets in
        availability_zones = []
        for key, value in AWS_SUBNETS.iteritems():
            availability_zones.append(key)

        prices = self.ec2_connection.get_spot_price_history(
            start_time=datetime.datetime.now().isoformat(),
            instance_type=instance_type,
            product_description='Linux/UNIX (Amazon VPC)')

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
            return None
        elif best_price.price > max_price:
            LOG.info('Spot Price too high')
            return None

        LOG.info('bid_price: {0}, spot_price: {2}, zone: {1}'.format(max_price, best_price.availability_zone, best_price.price))
        return best_price.availability_zone

    def run_spot_instance(
            self,
            ami_id,
            spot_price,
            user_data,
            instance_type,
            created_by,
            name,
            zone,
            number):
        """
        Run the ami as a spot instance
        """
        subnet_id = AWS_SUBNETS[zone]
        now_plus = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        spot_requests = self.ec2_connection.request_spot_instances(
            spot_price,
            image_id=ami_id,
            count=number,
            valid_until=now_plus.isoformat(),
            instance_type=instance_type,
            subnet_id=subnet_id,
            key_name=AWS_KEY_NAME,
            security_group_ids=AWS_SECURITY_GROUPS,
            user_data=user_data)

        # Wait for EC2 to provision the instance
        time.sleep(10)
        instances = []

        # Has it been provisioned yet - we allow 3 errors before aborting
        for spot_request in spot_requests:
            error_count = 0
            instance_id = None
            while instance_id is None and error_count < 3:
                spot_request_id = spot_request.id
                requests = None
                try:
                    requests = self.ec2_connection.get_all_spot_instance_requests(request_ids=[spot_request_id])
                except EC2ResponseError:
                    LOG.exception('Error count = {0}'.format(error_count))
                    error_count += 1

                if requests is None:
                    # Wait for AWS to catch up
                    time.sleep(10)
                else:
                    LOG.info('{0}, state: {1}, status:{2}'.format(spot_request_id, requests[0].state, requests[0].status))
                    if requests[0].state == 'active' and requests[0].status.code == 'fulfilled':
                        instance_id = requests[0].instance_id
                    elif requests[0].state == 'cancelled':
                        raise CancelledException('Request {0} cancelled. Status: {1}'.format(spot_request_id, requests[0].status))
                    elif requests[0].state == 'failed':
                        raise CancelledException('Request {0} failed. Status: {1}. Fault: {2}'.format(spot_request_id, requests[0].status, requests[0].fault))
                    else:
                        time.sleep(10)

            reservations = self.ec2_connection.get_all_instances(instance_ids=[instance_id])
            instances.append(reservations[0].instances[0])

        LOG.info('Waiting to start up')
        for instance in instances:
            while not instance.update() == 'running':
                LOG.info('Not running yet')
                time.sleep(5)

        # Give it time to settle down
        LOG.info('Assigning the tags')
        for instance in instances:
            self.ec2_connection.create_tags(
                [instance.id],
                {
                    'AMI': '{0}'.format(ami_id),
                    'Name': '{0}'.format(name),
                    'Created By': '{0}'.format(created_by)
                })


def user_data_mime(url, authenticator):
    user_data = MIMEMultipart()
    user_data.attach(MIMEText('''#cloud-config
repo_update: true
repo_upgrade: all

# Install additional packages on first boot
packages:
 - boinc-client

# Log all cloud-init process output (info & errors) to a logfile
output: { all : ">> /var/log/boinc-output.log" }

# Final_message written to log when cloud-init processes are finished
final_message: "System boot (via cloud-init) is COMPLETE, after $UPTIME seconds. Finished at $TIMESTAMP"
'''))
    user_data.attach(MIMEText('''#!/bin/bash -vx
#  _   _  ___ _____ _____
# | \ | |/ _ \_   _| ____|
# |  \| | | | || | |  _|
# | |\  | |_| || | | |___
# |_| \_|\___/ |_| |_____|
#
# When this is run as a user data start up script is is run as root - BE CAREFUL!!!
# Setup the ephemeral disks

/bin/dd if=/dev/zero of=/tmp/swapfile bs=256M count=4
chown root:root /tmp/swapfile
chmod 600 /tmp/swapfile
/sbin/mkswap /tmp/swapfile
/sbin/swapon /tmp/swapfile

# Attach
boinccmd --project_attach {0} {1}

'''.format(url, authenticator)))
    return user_data.as_string()


def start_servers(args):
    ec2_helper = EC2Helper()
    zone = ec2_helper.get_cheapest_spot_price(args.instance_type, args.spot_price)

    # Do we have a zone?
    if zone is not None:
        user_data = user_data_mime(args.url, args.authenticator)
        LOG.info(user_data)
        ec2_helper.run_spot_instance(
            args.ami_id,
            args.spot_price,
            user_data,
            args.instance_type,
            args.created_by,
            args.name,
            zone,
            args.number)

        LOG.info('All Done')


def main():
    parser = argparse.ArgumentParser('Start a number of BOINC Clients')
    parser.add_argument('ami_id', help='the AMI id to use')
    parser.add_argument('instance_type', help='the instance type to use')
    parser.add_argument('created_by', help='the username to use')
    parser.add_argument('name', help='the instance name to use')
    parser.add_argument('spot_price', type=float, help='the spot price to use')
    parser.add_argument('number', type=int, help='the number of instances to run')
    parser.add_argument('url', help='the number of instances to run')
    parser.add_argument('authenticator', help='the number of instances to run')

    start_servers(parser.parse_args())

if __name__ == "__main__":
    # ami-69631053 c4.xlarge kevin 'BOINC Client' 0.05 3 http://pogs.theskynet.org/pogs/ <weak-auth>
    main()
