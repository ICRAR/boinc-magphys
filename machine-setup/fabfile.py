"""
Fabric file for installing the servers
"""
import glob

import boto
import os
import time
import sys

from fabric.api import run, sudo, put, env, require, local, settings
from fabric.contrib.files import comment, uncomment, contains, exists, append, sed
from fabric.decorators import task
from fabric.operations import prompt

USERNAME = 'ec2-user' # ubuntu
AMI_ID = 'ami-aecd60c7'
INSTANCE_TYPE = 't1.micro'
INSTANCES_FILE = os.path.expanduser('~/.aws/aws_instances')
AWS_KEY = os.path.expanduser('~/.ssh/icrar-boinc.pem')
KEY_NAME = 'icrar-boinc'
SECURITY_GROUPS = ['icrar-boinc-server'] # Security group allows SSH
PUBLIC_KEYS = os.path.expanduser('~/Documents/Keys')

def create_instance(name, use_elastic_ip, public_ip):
    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    conn = boto.connect_ec2()

    if use_elastic_ip:
        # Disassociate the public IP
        if not conn.disassociate_address(public_ip=public_ip):
            print 'Could not disassociate the IP {0}'.format(public_ip)

    reservation = conn.run_instances(AMI_ID, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS)
    instance = reservation.instances[0]
    # Sleep so Amazon recognizes the new instance
    for i in range(4):
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(5)

    # Are we running yet?
    while not instance.update() == 'running':
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(5)

    # Sleep a bit more Amazon recognizes the new instance
    for i in range(4):
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(5)
    print '.'

    # Tag the instance
    conn.create_tags([instance.id], {'Name': name})

    # Associate the IP if needed
    if use_elastic_ip:
        print 'Current DNS name is {0}. About to associate the Elastic IP'.format(instance.dns_name)
        if not conn.associate_address(instance_id=instance.id, public_ip=public_ip):
            print 'Could not associate the IP {0} to the instance {1}'.format(public_ip, instance.id)
            sys.exit()

    # Give AWS time to switch everything over
    time.sleep(10)

    # Load the new instance data as the dns_name may have changed
    instance.update(True)
    if use_elastic_ip:
        print 'Current DNS name is {0} after associating the Elastic IP'.format(instance.dns_name)

    # The instance is started, but not useable (yet)
    print 'Started the instance {0}; now waiting for the SSH daemon to start.'.format(instance.dns_name)
    for i in range(12):
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(5)
    print '.'

    # we have to return an ASCII string
    return str(instance.dns_name)


def to_boolean(choice, default=False):
    """
    Convert the yes/no to true/false
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    choice_lower = choice.lower()
    if choice_lower in valid:
        return valid[choice_lower]

    return default

@task
def copy_public_keys():
    """
    Copy the public keys to the remote servers
    """
    env.list_of_users = []
    for file in glob.glob(PUBLIC_KEYS + '/*.pub'):
        filename = os.path.basename(file)
        user, ext = os.path.splitext(filename)
        env.list_of_users.append(user)
        put(file, filename)

@task
def base_install():
    """
    Perform the basic install
    """

    # Update the AMI completely
    sudo('yum --assumeyes update')

    # Install puppet and git
    sudo('yum --assumeyes install puppet git')

    # Clone our code
    run('git clone git://github.com/ICRAR/boinc-magphys.git')

    # Puppet and git should be installed by the python
    sudo('cd /home/ec2-user/boinc-magphys/machine-setup; puppet boinc-magphys.pp')

    # Recommended version per http://boinc.berkeley.edu/download_all.php on 2012-07-10
    run('svn co http://boinc.berkeley.edu/svn/trunk/boinc /home/ec2-user/boinc')

    run('cd /home/ec2-user/boinc; ./_autosetup')
    run('cd /home/ec2-user/boinc; ./configure --disable-client --disable-manager')
    run('cd /home/ec2-user/boinc; make')

    # Setup the pythonpath
    append('/home/ec2-user/.bash_profile', ['', 'PYTHONPATH=$PYTHONPATH:/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src', 'export PYTHONPATH'])

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

    # Used by BOINC in the assimilator
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

@task
def single_install():
    """
    Perform the tasks to install the whole boinc server on a single machine
    """
    # Activate the DB
    sudo('mysql_install_db')
    sudo('chown -R mysql:mysql /var/lib/mysql/*')
    run('''echo "service { 'mysqld': ensure => running, enable => true }" | sudo puppet apply''')

    # Wait for it to start up
    time.sleep(15)

    # Make the POGS project
    run('cd /home/ec2-user/boinc/tools; yes | ./make_project -v --url_base http://{0} --db_user root pogs'.format(env.hosts[0]))

    # Setup the database for recording WU's
    run('mysql --user=root < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql')

    # Build the validator
    run('cd /home/ec2-user/boinc-magphys/server/src/Validator; make')

    # setup_website
    sudo('cd /home/ec2-user/boinc-magphys/machine-setup; rake setup_website')

    # This is needed because the files that Apache serve are inside the user's home directory.
    run('chmod 711 /home/ec2-user')
    run('chmod -R oug+r /home/ec2-user/projects/pogs')
    run('chmod -R oug+x /home/ec2-user/projects/pogs/html')
    run('chmod ug+w /home/ec2-user/projects/pogs/log_*')
    run('chmod ug+wx /home/ec2-user/projects/pogs/upload')

    # Edit the files
    run('cd /home/ec2-user/boinc-magphys/machine-setup; python2.7 file_editor_single.py')

    # Setup the forums
    run('cd /home/ec2-user/projects/pogs/html/ops; php create_forums.php')

    # Copy files into place
    run('cd /home/ec2-user/boinc-magphys/machine-setup; rake update_versions')
    run('cd /home/ec2-user/boinc-magphys/machine-setup; rake start_daemons')

    # Setup the crontab job to keep things ticking
    run('crontab -l > /tmp/crontab.txt')
    run('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt')
    run('crontab /tmp/crontab.txt')

    # Setup the ops area password
    run('cd /home/ec2-user/projects/pogs/html/ops; htpasswd -bc .htpasswd {0} {1}'.format(env.ops_username, env.ops_password))

@task
def test_env():
    """
    Configure the test environment in the AWS cloud
    """
    if 'use_elastic_ip' in env:
        use_elastic_ip = to_boolean(prompt('Do you want to assign an Elastic IP to this instance: ', default='no'))
    else:
        use_elastic_ip = to_boolean(env.use_elastic_ip)

    public_ip = None
    if use_elastic_ip:
        public_ip = prompt('What is the public IP address: ', 'public_ip')

    if 'ops_username' in env:
        prompt('Ops area username: ', 'ops_username')
    if 'ops_password' in env:
        prompt('Password: ', 'ops_password')
    if 'instance_name' in env:
        prompt('Instance name: ', 'instance_name')
    hostname = create_instance(env.instance_name, use_elastic_ip, public_ip)
    env.hosts = [hostname]
    env.user = USERNAME
    env.key_filename = AWS_KEY

@task
def test_deploy():
    """
    Deploy the test environment in the AWS cloud
    """
    require('hosts', provided_by=[test_env])

    copy_public_keys()
    base_install()
    single_install()

@task
def prod_deploy():
    """
    Deploy
    """
    require('hosts', provided_by=[prod_env])

    copy_public_keys()
    base_install()
