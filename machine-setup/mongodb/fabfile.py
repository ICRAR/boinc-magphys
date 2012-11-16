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
Create a MongoDB cluster inside a VPC
"""
import collections
import os
import time

from boto import connect_ec2
from boto.vpc import VPCConnection
from fabric.decorators import serial, task
from fabric.api import run, sudo, put, env, require
from fabric.utils import abort, puts, fastprint

AMI_ID = 'ami-1624987f'
INSTANCE_TYPE = 'm1.small'
AWS_KEY = os.path.expanduser('~/.ssh/icrar-boinc.pem')
KEY_NAME = 'icrar-boinc'

SecurityGroupRule = collections.namedtuple("SecurityGroupRule", ["ip_protocol", "from_port", "to_port", "cidr_ip", "src_group_name"])

MONGODB_RULES = [
    SecurityGroupRule("tcp", "27017", "27017", "0.0.0.0/0", None),
    SecurityGroupRule("tcp", "27018", "27018", "0.0.0.0/0", None),
    SecurityGroupRule("tcp", "27019", "27019", "0.0.0.0/0", None),
    ]

GENERAL_RULES = [
    # ssh makes life possible
    SecurityGroupRule("tcp", "22", "22", "0.0.0.0/0", None),
    # http to download things
    SecurityGroupRule("tcp", "80", "80", "0.0.0.0/0", None),
]

SECURITY_GROUPS = [("Mongo-Rules", MONGODB_RULES),
                   ("General-Rules", GENERAL_RULES),
]

def authorize(c, group, rule):
    """
    Authorize 'rule' on 'group'.
    """
    return modify_security_group(c, group, rule, authorize=True)

def create_instances():
    """
    Create EC2 instances
    """
    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    connection = connect_ec2()

    # Create the security groups
    security_groups = []
    for group_name, rules in SECURITY_GROUPS:
        group = get_or_create_security_group(connection, group_name)
        update_security_group(connection, group, rules)
        security_groups.append(group_name)

    reservations = connection.run_instances(AMI_ID, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS, subnet_id=env.subnet_id)
    instances = reservations.instances
    # Sleep so Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)

    # Are we running yet?
    for i in range(len(instances)):
        while not instances[i].update() == 'running':
            fastprint('.')
            time.sleep(5)

    # Sleep a bit more Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)
    puts('.')

def create_vpc():
    """
    Create a simple VPC to hold the MongoDB
    """
    puts('Creating the VPC')
    connection = VPCConnection()
    vpc = connection.create_vpc('10.0.0.0/23')
    subnet = connection.create_subnet(vpc.id, '10.0.0.0/25')
    route_table = connection.create_route_table(vpc.id)
    connection.associate_route_table(route_table.id, subnet.id)
    internet_gateway = connection.create_internet_gateway()
    if not connection.attach_internet_gateway(internet_gateway.id, vpc.id):
        abort('Could not attach the internet gateway')
    if not connection.create_route(route_table.id, '0.0.0.0/0', internet_gateway.id):
        abort('Could not create the route to the internet gateway')

    env.subnet_id = subnet.id
    env.vpc_id = vpc.id

def get_or_create_security_group(connection, group_name):
    """
    Create or update a security group
    """
    groups = [g for g in connection.get_all_security_groups() if g.name == group_name and g.vpc_id == env.vpc_id]
    group = groups[0] if groups else None
    if not group:
        puts('Creating group "{0}"...'.format(group_name,))
        group = connection.create_security_group(group_name, "A group for {0}".format(group_name,), vpc_id=env.vpc_id)
    return group

def modify_security_group(connection, group, rule, authorize=False, revoke=False):
    """
    Modify the security group
    """
    src_group = None
    if rule.src_group_name:
        src_group = connection.get_all_security_groups([rule.src_group_name,])[0]

    if authorize and not revoke:
        puts("Authorizing missing rule {0}...".format(rule,))
        group.authorize(ip_protocol=rule.ip_protocol,
            from_port=rule.from_port,
            to_port=rule.to_port,
            cidr_ip=rule.cidr_ip,
            src_group=src_group)
    elif not authorize and revoke:
        puts("Revoking unexpected rule {0}...".format(rule,))
        group.revoke(ip_protocol=rule.ip_protocol,
            from_port=rule.from_port,
            to_port=rule.to_port,
            cidr_ip=rule.cidr_ip,
            src_group=src_group)

def revoke(c, group, rule):
    """
    Revoke 'rule' on 'group'.
    """
    return modify_security_group(c, group, rule, revoke=True)


def update_security_group(c, group, expected_rules):
    """
    Update the group
    """
    puts('Updating group "{0}"...'.format(group.name))
    puts("Expected Rules: {0}".format(expected_rules))

    current_rules = []
    for rule in group.rules:
        if not rule.grants[0].cidr_ip:
            current_rule = SecurityGroupRule(rule.ip_protocol,
                rule.from_port,
                rule.to_port,
                "0.0.0.0/0",
                rule.grants[0].name)
        else:
            current_rule = SecurityGroupRule(rule.ip_protocol,
                rule.from_port,
                rule.to_port,
                rule.grants[0].cidr_ip,
                None)

        if current_rule not in expected_rules:
            revoke(c, group, current_rule)
        else:
            current_rules.append(current_rule)

    puts("Current Rules:".format(current_rules))

    for rule in expected_rules:
        if rule not in current_rules:
            authorize(c, group, rule)

@task
@serial
def create_mongos():
    create_vpc()
    create_instances()

@task
@serial
def setup_env():
    env.key_filename = AWS_KEY

