"""
Fabric test against AWS
"""
import os
import boto
from fabric.context_managers import cd
from fabric.contrib.files import append
from fabric.decorators import task
from fabric.operations import prompt, require, sudo, run
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

def create_instance(name):
    """Create the AWS instance

    :param name: the name to be used for this instance

    :rtype: string
    :return: The public host name of the AWS instance
    """

    puts('Creating instance {0}'.format(name))

    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    conn = boto.connect_ec2()

    reservations = conn.run_instances(AMI_ID, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS, min_count=1, max_count=1)
    instances = reservations.instances
    # Sleep so Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)

    # Are we running yet?
    while not instances[0].update() == 'running':
        fastprint('.')
        time.sleep(5)

    # Sleep a bit more Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # Tag the instance
    conn.create_tags([instances[0].id], {'Name': name})

    # The instance is started, but not useable (yet)
    puts('Started the instance, now waiting for the SSH daemon to start.')
    for i in range(12):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # we have to return an ASCII string
    return str(instances[0].dns_name)

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

    # Setup the pythonpath
    append('/home/ec2-user/.bash_profile', ['', 'PYTHONPATH=/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src', 'export PYTHONPATH'])

    # Setup the python
    run('wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg')
    sudo('sh setuptools-0.6c11-py2.7.egg')
    run('rm setuptools-0.6c11-py2.7.egg')
    sudo('rm -f /usr/bin/easy_install')
    sudo('easy_install-2.7 pip')
    sudo('rm -f /usr/bin/pip')
    sudo('pip-2.7 install fabric')
    sudo('pip-2.7 install configobj')


def test01():
    run('mkdir test01')
    with cd('/home/ec2-user/test01'):
        run('''echo "123
456
789" > test1.echo''')
        run('''echo 'a = "123"
b = "456"
789' > test2.echo''')

def test02():
    run('mkdir test02')
    run('cp /home/ec2-user/boinc/html/project.sample/project.inc /home/ec2-user/test02')


@task
def environment():
    """
    Configure the test
    """
    prompt('AWS Instance name: ', 'instance_name')
    env.hosts = [create_instance(env.instance_name)]
    env.user = USERNAME
    env.key_filename = AWS_KEY

@task
def step01():
    require('hosts', provided_by=[environment])

    base_install()
    test01()
    test02()
