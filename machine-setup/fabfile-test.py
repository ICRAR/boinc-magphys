"""

"""
import os
import boto
from fabric.decorators import serial, task, parallel, roles
from fabric.operations import sudo, run, require
from fabric.state import env
from fabric.utils import puts, fastprint
import time

USERNAME = 'ec2-user'
AMI_ID = 'ami-aecd60c7'
INSTANCE_TYPE = 't1.micro'
INSTANCES_FILE = os.path.expanduser('~/.aws/aws_instances')
AWS_KEY = os.path.expanduser('~/.ssh/icrar-boinc.pem')
KEY_NAME = 'icrar-boinc'
SECURITY_GROUPS = ['icrar-boinc-server'] # Security group allows SSH
PUBLIC_KEYS = os.path.expanduser('~/Documents/Keys')

def create_instance(names):
    """Create the AWS instance

    :param names: the name to be used for this instance
    :type names: list of str

    :rtype: string
    :return: The public host name of the AWS instance
    """

    puts('Creating instances {0}'.format(names))
    number_instances = len(names)

    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    conn = boto.connect_ec2()

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

@task
@parallel
def base_install():
    print 'base_install Host: {0} Env: {1}'.format(env.host_string, env)
    # Update the AMI completely
    sudo('yum --assumeyes --quiet update')

    # Install puppet and git
    sudo('yum --assumeyes --quiet install puppet git')



@task
@parallel
def common_end_install():
    print 'common_end_install Host: {0} Env: {1}'.format(env.host_string, env)
    # Setup the crontab job to keep things ticking
    run('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt')
    run('crontab /tmp/crontab.txt')


@task
@serial
def get_hosts():
    # Create the instance in AWS
    host_names = create_instance(['Test01', 'Test02', 'Test03'])
    print '{0}'.format(host_names)
    env.hosts = host_names
    env.user = USERNAME
    env.key_filename = AWS_KEY
    env.roledefs = {
        'role01' : [host_names[0]],
        'role02' : [host_names[1]],
        'role03' : [host_names[2]],
        }

@task
@parallel
def prod_stage1():
    require('hosts', provided_by=[get_hosts])

    base_install()
    common_end_install()

@task
@serial
@roles('role01')
def prod_stage2():
    require('hosts', provided_by=[get_hosts])
    print 'serial_install01 Host: {0} Env: {1}'.format(env.host_string, env)
    run('git clone git://github.com/ICRAR/boinc-magphys.git')

@task
@serial
@roles('role02')
def prod_stage3():
    require('hosts', provided_by=[get_hosts])
    print 'serial_install02 Host: {0} Env: {1}'.format(env.host_string, env)
    run('git clone git://github.com/ICRAR/theSkyNet.git')

@task
@serial
@roles('role03')
def prod_stage4():
    require('hosts', provided_by=[get_hosts])
    print 'serial_install03 Host: {0} Env: {1}'.format(env.host_string, env)
    run('git clone git://github.com/ICRAR/machine-setup.git')
