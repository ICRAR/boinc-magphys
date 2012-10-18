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
Fabric file for installing the servers

Test is simple as it only runs on one server
fab test_env test_deploy_with_db

Production is more complex as we have three servers to configure.
Each needs the BOINC project structure installed, but that means recreating the database 3 times
so we must ensure the download server runs last as it actually adds things to the database

fab prod_env prod_deploy_stage01 prod_deploy_stage02 prod_deploy_stage03 prod_deploy_stage04
"""
import glob

import boto
import os
import time

from fabric.api import run, sudo, put, env, require
from fabric.context_managers import cd
from fabric.contrib.console import confirm
from fabric.contrib.files import append, sed, comment
from fabric.decorators import task, parallel, serial, roles
from fabric.operations import prompt
from fabric.utils import puts, abort, fastprint

USERNAME = 'ec2-user'
AMI_ID = 'ami-aecd60c7'
INSTANCE_TYPE = 't1.micro'
INSTANCES_FILE = os.path.expanduser('~/.aws/aws_instances')
AWS_KEY = os.path.expanduser('~/.ssh/icrar-boinc.pem')
KEY_NAME = 'icrar-boinc'
SECURITY_GROUPS = ['icrar-boinc-server'] # Security group allows SSH
PUBLIC_KEYS = os.path.expanduser('~/Documents/Keys')
WEB_HOST = 0
UPLOAD_HOST = 1
DOWNLOAD_HOST = 2

def create_instance(names, use_elastic_ip, public_ips):
    """Create the AWS instance

    :param names: the name to be used for this instance
    :type names: list of strings
    :param boolean use_elastic_ip: is this instance to use an Elastic IP address

    :rtype: string
    :return: The public host name of the AWS instance
    """

    puts('Creating instances {0} [{1}:{2}]'.format(names, use_elastic_ip, public_ips))
    number_instances = len(names)
    if number_instances != len(public_ips):
        abort('The lists do not match in length')

    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    conn = boto.connect_ec2()

    if use_elastic_ip:
        # Disassociate the public IP
        for public_ip in public_ips:
            if not conn.disassociate_address(public_ip=public_ip):
                abort('Could not disassociate the IP {0}'.format(public_ip))

    reservations = conn.run_instances(AMI_ID, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS, min_count=number_instances, max_count=number_instances)
    instances = reservations.instances
    # Sleep so Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)

    # Are we running yet?
    for i in range(number_instances):
        while not instances[i].update() == 'running':
            fastprint('.')
            time.sleep(5)

    # Sleep a bit more Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # Tag the instance
    for i in range(number_instances):
        conn.create_tags([instances[i].id], {'Name': names[i]})

    # Associate the IP if needed
    if use_elastic_ip:
        for i in range(number_instances):
            puts('Current DNS name is {0}. About to associate the Elastic IP'.format(instances[i].dns_name))
            if not conn.associate_address(instance_id=instances[i].id, public_ip=public_ips[i]):
                abort('Could not associate the IP {0} to the instance {1}'.format(public_ips[i], instances[i].id))

    # Give AWS time to switch everything over
    time.sleep(10)

    # Load the new instance data as the dns_name may have changed
    for i in range(number_instances):
        instances[i].update(True)
    if use_elastic_ip:
        for i in range(number_instances):
            puts('Current DNS name is {0} after associating the Elastic IP'.format(instances[i].dns_name))

    # The instance is started, but not useable (yet)
    puts('Started the instance(s) now waiting for the SSH daemon to start.')
    for i in range(12):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # we have to return an ASCII string
    host_names = []
    for i in range(number_instances):
        host_names.append(str(instances[i].dns_name))
    return host_names


def base_install():
    """
    Perform the basic install
    """
    # Update the AMI completely
    sudo('yum --assumeyes --quiet update')

    # Install puppet and git
    sudo('yum --assumeyes --quiet install puppet git')

    # Clone our code
    run('git clone git://github.com/ICRAR/boinc-magphys.git')

    # Puppet and git should be installed by the python
    with cd('/home/ec2-user/boinc-magphys/machine-setup'):
        sudo('puppet boinc-magphys.pp')

    # Recommended version per http://boinc.berkeley.edu/download_all.php on 2012-07-10
    run('svn co http://boinc.berkeley.edu/svn/trunk/boinc /home/ec2-user/boinc')

    with cd('/home/ec2-user/boinc'):
        run('./_autosetup')
        run('./configure --disable-client --disable-manager')
        run('make')

    # Setup the pythonpath
    append('/home/ec2-user/.bash_profile', ['', 'PYTHONPATH=/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src', 'export PYTHONPATH'])

    # Setup the python
    run('wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg')
    sudo('sh setuptools-0.6c11-py2.7.egg')
    run('rm setuptools-0.6c11-py2.7.egg')
    sudo('rm -f /usr/bin/easy_install')
    sudo('easy_install-2.7 pip')
    sudo('rm -f /usr/bin/pip')
    sudo('pip-2.7 install sqlalchemy')
    sudo('pip-2.7 install Numpy')
    sudo('pip-2.7 install pyfits')
    sudo('pip-2.7 install pil')
    sudo('pip-2.7 install django')
    sudo('pip-2.7 install fabric')
    sudo('pip-2.7 install configobj')
    sudo('pip-2.7 install MySQL-python')

    for user in env.list_of_users:
        sudo('useradd {0}'.format(user))
        sudo('mkdir /home/{0}/.ssh'.format(user))
        sudo('chmod 700 /home/{0}/.ssh'.format(user))
        sudo('chown {0}:{0} /home/{0}/.ssh'.format(user))
        sudo('mv /home/ec2-user/{0}.pub /home/{0}/.ssh/authorized_keys'.format(user))
        sudo('chmod 700 /home/{0}/.ssh/authorized_keys'.format(user))
        sudo('chown {0}:{0} /home/{0}/.ssh/authorized_keys'.format(user))

        # Add them to the sudoers
        sudo('''su -l root -c 'echo "{0} ALL = NOPASSWD: ALL" >> /etc/sudoers' '''.format(user))

