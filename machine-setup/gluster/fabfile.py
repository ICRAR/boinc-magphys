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
Build the Gluster AMI we use
"""
import boto
import os
import time
from boto.ec2 import blockdevicemapping

from fabric.api import run, sudo, env, require
from fabric.decorators import task, serial
from fabric.operations import prompt
from fabric.utils import puts, fastprint


USERNAME = 'ec2-user'
AMI_ID = 'ami-05355a6c'
INSTANCE_TYPE = 'm1.small'
INSTANCES_FILE = os.path.expanduser('~/.aws/aws_instances')
AWS_KEY = os.path.expanduser('~/.ssh/icrar-boinc.pem')
KEY_NAME = 'icrar-boinc'
SECURITY_GROUPS = ['icrar-boinc-server']  # Security group allows SSH
YUM_BASE_PACKAGES = ' '


def base_install():
    """
    Perform the basic install
    """
    # Install the bits we need
    #sudo('yum --assumeyes --quiet install {0}'.format(YUM_BASE_PACKAGES))

    # Load the Gluster FS RPM's
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-3.3.1-1.el6.x86_64.rpm')
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-fuse-3.3.1-1.el6.x86_64.rpm')
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-geo-replication-3.3.1-1.el6.x86_64.rpm')
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-server-3.3.1-1.el6.x86_64.rpm')
    sudo('yum --assumeyes --quiet install glusterfs*.rpm')
    sudo('chkconfig glusterd --add')
    sudo('chkconfig glusterd on')
    #sudo('service glusterd start')
    run('rm glusterfs*.rpm')

    sudo('mkdir -p /mnt/brick01')


def create_instance(ebs_size, ami_name):
    """
    Create the AWS instance
    :param ebs_size:
    """
    puts('Creating the instance {1} with disk size {0} GB'.format(ebs_size, ami_name))

    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    ec2_connection = boto.connect_ec2()

    dev_sda1 = blockdevicemapping.EBSBlockDeviceType(delete_on_termination=True)
    dev_sda1.size = int(ebs_size)  # size in Gigabytes

    bdm = blockdevicemapping.BlockDeviceMapping()
    bdm['/dev/sda1'] = dev_sda1
    reservations = ec2_connection.run_instances(AMI_ID, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS, block_device_map=bdm)
    instance = reservations.instances[0]
    # Sleep so Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)

    # Are we running yet?
    while not instance.update() == 'running':
        fastprint('.')
        time.sleep(5)

    # Sleep a bit more Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)
    puts('.')

    ec2_connection.create_tags([instance.id], {'Name': '{0}'.format(ami_name)})

    # The instance is started, but not useable (yet)
    puts('Started the instance now waiting for the SSH daemon to start.')
    for i in range(12):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # Return the instance
    return instance, ec2_connection


def resize_file_system():
    """
    Resize the file system as AWS doesn't do that when you start an AMI
    """
    # Resize the file system
    sudo('resize2fs /dev/sda1')


def yum_update():
    """
    Make sure things are up to date
    """
    # Update the AMI completely
    sudo('yum --assumeyes --quiet update')


@task
@serial
def base_setup_env():
    """
    Ask a series of questions before deploying to the cloud.
    """
    if 'ebs_size' not in env:
        prompt('EBS Size (GB): ', 'ebs_size', default=40, validate=int)
    if 'ami_name' not in env:
        prompt('AMI Name: ', 'ami_name', default='BaseGlusterSetup')

    # Create the instance in AWS
    ec2_instance, ec2_connection = create_instance(env.ebs_size, env.ami_name)
    env.ec2_instance = ec2_instance
    env.ec2_connection = ec2_connection
    env.hosts = [ec2_instance.dns_name]

    # Add these to so we connect magically
    env.user = USERNAME
    env.key_filename = AWS_KEY


@task
@serial
def base_build_ami():
    """
    Build the base AMI
    """
    require('hosts', provided_by=[base_setup_env])

    # Make sure yum is up to date
    yum_update()

    # Perform the base install
    base_install()

    # When glusterfs-server package is first installed, it creates a node UUID file at /var/lib/glusterd/glusterd.info
    # So, when gluster resolves the hostname to a UUID, it creates a conflict.
    sudo('service glusterd stop')
    sudo('rm /var/lib/glusterd/glusterd.info')

    # Save the instance as an AMI
    puts("Stopping the instance")
    env.ec2_connection.stop_instances(env.ec2_instance.id, force=True)
    while not env.ec2_instance.update() == 'stopped':
        fastprint('.')
        time.sleep(5)

    puts("The AMI is being created. Don't forget to terminate the instance if not needed")
    env.ec2_connection.create_image(env.ec2_instance.id, env.ami_name, description='The base GlusterFS AMI')

    puts('All done')
