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

Single server is simple as it only runs on one server
fab setup_env deploy_with_db

Production is more complex as we have three servers to configure.
Each needs the BOINC project structure installed, but that means recreating the database 3 times
so we must ensure the download server runs last as it actually adds things to the database

fab prod_env prod_deploy_stage01 prod_deploy_stage02 prod_deploy_stage03 prod_deploy_stage04
"""
import glob
import boto
import os
import time
import csv
from boto.ec2 import blockdevicemapping

from fabric.api import run, sudo, put, env, require
from fabric.context_managers import cd
from fabric.contrib.files import append, comment
from fabric.decorators import task, serial
from fabric.operations import prompt
from fabric.utils import puts, abort, fastprint

USERNAME = 'ec2-user'
AMI_ID = 'ami-05355a6c'
INSTANCE_TYPE = 'm1.small'
INSTANCES_FILE = os.path.expanduser('~/.aws/aws_instances')
AWS_KEY = os.path.expanduser('~/.ssh/icrar-boinc.pem')
KEY_NAME = 'icrar-boinc'
SECURITY_GROUPS = ['icrar-boinc-server']  # Security group allows SSH
BOINC_AWS_KEYS = os.path.expanduser('~/Documents/Keys/aws')
PUBLIC_KEYS = os.path.expanduser('~/Documents/Keys/magphys')
PIP_PACKAGES = 'sqlalchemy Numpy pyfits pil fabric configobj MySQL-python boto astropy'
YUM_BASE_PACKAGES = 'autoconf automake binutils gcc gcc-c++ libpng-devel libstdc++46-static gdb libtool gcc-gfortran git openssl-devel mysql mysql-devel python-devel python27 python27-devel '
YUM_BOINC_PACKAGES = 'httpd httpd-devel mysql-server php php-cli php-gd php-mysql mod_fcgid php-fpm postfix ca-certificates MySQL-python'


def base_install():
    """
    Perform the basic install
    """
    # Install the bits we need - we need the MySQL so the python connector will build
    sudo('yum --assumeyes --quiet install {0}'.format(YUM_BASE_PACKAGES))

    # Setup the python
    run('wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg')
    sudo('sh setuptools-0.6c11-py2.7.egg')
    run('rm setuptools-0.6c11-py2.7.egg')
    sudo('rm -f /usr/bin/easy_install')
    sudo('easy_install-2.7 pip')
    sudo('rm -f /usr/bin/pip')
    sudo('pip-2.7 install {0}'.format(PIP_PACKAGES))

    # Setup the pythonpath
    append('/home/ec2-user/.bash_profile',
           ['',
            'PYTHONPATH=/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src',
            'export PYTHONPATH'])

    # Setup the HDF5
    with cd('/usr/local/src'):
        sudo('wget http://www.hdfgroup.org/ftp/lib-external/szip/2.1/src/szip-2.1.tar.gz')
        sudo('tar -xvzf szip-2.1.tar.gz')
        sudo('wget http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.11.tar.gz')
        sudo('tar -xvzf hdf5-1.8.11.tar.gz')
        sudo('rm *.gz')
    with cd('/usr/local/src/szip-2.1'):
        sudo('./configure --prefix=/usr/local/szip')
        sudo('make')
        sudo('make install')
    with cd('/usr/local/src/hdf5-1.8.11'):
        sudo('./configure --prefix=/usr/local/hdf5 --with-szlib=/usr/local/szip --enable-production')
        sudo('make')
        sudo('make install')
    sudo('''echo "/usr/local/hdf5/lib
/usr/local/szip/lib" >> /etc/ld.so.conf.d/hdf5.conf''')
    sudo('ldconfig')

    # Now install the H5py
    with cd('/tmp'):
        run('wget https://h5py.googlecode.com/files/h5py-2.1.0.tar.gz')
        run('tar -xvzf h5py-2.1.0.tar.gz')
    with cd('/tmp/h5py-2.1.0'):
        sudo('python2.7 setup.py build --hdf5=/usr/local/hdf5')
        sudo('python2.7 setup.py install')

    # Load the Gluster FS RPM's
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-3.3.1-1.el6.x86_64.rpm')
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-fuse-3.3.1-1.el6.x86_64.rpm')
    sudo('yum --assumeyes --quiet install glusterfs*.rpm')
    run('rm glusterfs*.rpm')

    sudo('mkdir -p /mnt/data')



def copy_public_keys():
    """
    Copy the public keys to the remote servers
    """
    env.list_of_users = []
    for key_file in glob.glob(PUBLIC_KEYS + '/*.pub'):
        filename = os.path.basename(key_file)
        user, ext = os.path.splitext(filename)
        env.list_of_users.append(user)
        put(key_file, filename)


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


def start_ami_instance(ami_id, instance_name):
    """
    Start an AMI instance running
    :param ami_id:
    :param instance_name:
    """
    puts('Starting the instance {0} from id {0}'.format(instance_name, ami_id))

    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    ec2_connection = boto.connect_ec2()
    reservations = ec2_connection.run_instances(ami_id, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS)
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

    ec2_connection.create_tags([instance.id], {'Name': '{0}'.format(instance_name)})

    # The instance is started, but not useable (yet)
    puts('Started the instance(s) now waiting for the SSH daemon to start.')
    for i in range(12):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # Return the instance
    return instance


def get_aws_keyfile():
    """
    Get the aws key file

    :return:
    """
    return os.path.join(BOINC_AWS_KEYS, '{0}.credentials.csv.txt'.format(env.aws_user))


def make_swap():
    """
    Make the swap space
    """
    sudo('dd if=/dev/zero of=/swapfile bs=1M count=2048')
    sudo('mkswap /swapfile')
    sudo('swapon /swapfile')


def boinc_install(with_db):
    """
    Perform the tasks to install the whole BOINC server on a single machine
    """
    # Get the packages
    sudo('yum --assumeyes --quiet install {0}'.format(YUM_BOINC_PACKAGES))

    # Clone our code
    if env.branch == '':
        run('git clone git://github.com/ICRAR/boinc-magphys.git')
    else:
        run('git clone -b {0} git://github.com/ICRAR/boinc-magphys.git'.format(env.branch))

    run('mkdir /home/ec2-user/galaxies')
    run('mkdir -p /home/ec2-user/archive/to_store')

    # Create the .boto file
    file_name = get_aws_keyfile()
    with open(file_name, 'rb') as csv_file:
        reader = csv.reader(csv_file)
        # Skip the header
        reader.next()

        row = reader.next()
        run('''echo "[Credentials]
aws_access_key_id = {0}
aws_secret_access_key = {1}" >> /home/ec2-user/.boto'''.format(row[1], row[2]))

    # Setup postfix
    sudo('service sendmail stop')
    sudo('service postfix stop')
    sudo('chkconfig sendmail off')
    sudo('chkconfig sendmail --del')

    sudo('chkconfig postfix --add')
    sudo('chkconfig postfix on')

    sudo('service postfix start')

    sudo('''echo "relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_CAfile = /etc/postfix/cacert.pem
smtp_use_tls = yes

# smtp_generic_maps
smtp_generic_maps = hash:/etc/postfix/generic
default_destination_concurrency_limit = 1" >> /etc/postfix/main.cf''')

    sudo('echo "[smtp.gmail.com]:587 {0}@gmail.com:{1}" > /etc/postfix/sasl_passwd'.format(env.gmail_account, env.gmail_password))
    sudo('chmod 400 /etc/postfix/sasl_passwd')
    sudo('postmap /etc/postfix/sasl_passwd')

    # Setup the S3 environment
    if to_boolean(env.create_s3):
        with cd('/home/ec2-user/boinc-magphys/machine-setup/boinc'):
            run('fab --set project_name={0} create_s3'.format(env.project_name))

    # Setup Users
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

    # Grab the latest trunk from GIT
    run('git clone git://boinc.berkeley.edu/boinc-v2.git boinc')

    with cd('/home/ec2-user/boinc'):
        run('./_autosetup')
        run('./configure --disable-client --disable-manager')
        run('make')

    if with_db:
        # Activate the DB
        sudo('mysql_install_db')
        sudo('chown -R mysql:mysql /var/lib/mysql/*')
        sudo('chkconfig mysqld --add')
        sudo('chkconfig mysqld on')
        sudo('service mysqld start')

        # Wait for it to start up
        time.sleep(5)

        # Setup the database for recording WU's
        run('mysql --user=root < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql')

        # Make the BOINC project
        with cd('/home/ec2-user/boinc/tools'):
            run('./make_project -v --no_query --url_base http://{0} --db_user root {1}'.format(env.hosts[0], env.project_name))

        run('''echo 'databaseUserid = "root"
databasePassword = ""
databaseHostname = "localhost"
databaseName = "magphys"
boincDatabaseName = "{0}"' >> /home/ec2-user/boinc-magphys/server/src/config/database.settings'''.format(env.project_name))

    else:
        # Setup the database for recording WU's
        run('mysql --user={0} --host={1} --password={2} < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql'.format(env.db_username, env.db_host_name, env.db_password))

        # Make the BOINC project
        with cd('/home/ec2-user/boinc/tools'):
            run('./make_project -v --no_query --drop_db_first --url_base http://{0} --db_user {1} --db_host={2} --db_passwd={3} {4}'
                .format(env.hosts[0], env.db_username, env.db_host_name, env.db_password, env.project_name))

        run('''echo 'databaseUserid = "{0}"
databasePassword = "{1}"
databaseHostname = "{2}"
databaseName = "magphys"
boincDatabaseName = "{3}"' >> /home/ec2-user/boinc-magphys/server/src/config/database.settings'''.format(env.db_username, env.db_password, env.db_host_name, env.project_name))

    # Setup Docmosis files
    run('''echo 'docmosis_key = "{0}"
docmosis_render_url = "https://dws.docmosis.com/services/rs/render"
docmosis_template = "Report.doc"' >> /home/ec2-user/boinc-magphys/server/src/config/docmosis.settings'''.format(env.docmosis_key))

    # Setup Work Generation files
    run('''echo 'min_pixels_per_file = "15"
row_height = "6"
threshold = "1000"
high_water_mark = "400"
report_deadline = "7"
project_name = "{0}"
tmp = "/tmp"
boinc_project_root = "/home/ec2-user/projects/{0}"' >> /home/ec2-user/boinc-magphys/server/src/config/work_generation.settings'''.format(env.project_name))

    # Copy the config files
    run('cp /home/ec2-user/boinc-magphys/server/config/boinc_files/db_dump_spec.xml /home/ec2-user/projects/{0}/db_dump_spec.xml'.format(env.project_name))
    run('cp /home/ec2-user/boinc-magphys/server/config/boinc_files/html/user/* /home/ec2-user/projects/{0}/html/user/'.format(env.project_name))
    run('cp /home/ec2-user/boinc-magphys/server/config/boinc_files/hr_info.txt /home/ec2-user/projects/{0}/hr_info.txt'.format(env.project_name))
    run('mkdir -p /home/ec2-user/projects/{0}/html/stats_archive'.format(env.project_name))
    run('mkdir -p /home/ec2-user/projects/{0}/html/stats_tmp'.format(env.project_name))

    comment('/home/ec2-user/projects/{0}/html/ops/create_forums.php'.format(env.project_name), '^die', char='// ')

    run('mkdir -p /home/ec2-user/projects/{0}/html/user/logos'.format(env.project_name))
    run('cp /home/ec2-user/boinc-magphys/server/logos/* /home/ec2-user/projects/{0}/html/user/logos/'.format(env.project_name))

    # Build the validator
    with cd('/home/ec2-user/boinc-magphys/server/src/magphys_validator'):
        run('make')

    # setup_website
    if to_boolean(env.start_boinc):
        with cd('/home/ec2-user/boinc-magphys/machine-setup/boinc'):
            run('fab --set project_name={0} edit_files'.format(env.project_name))
            sudo('fab --set project_name={0} setup_website'.format(env.project_name))

        # This is needed because the files that Apache serve are inside the user's home directory.
        run('chmod 711 /home/ec2-user')
        run('chmod -R oug+r /home/ec2-user/projects/{0}'.format(env.project_name))
        run('chmod -R oug+x /home/ec2-user/projects/{0}/html'.format(env.project_name))
        run('chmod ug+w /home/ec2-user/projects/{0}/log_*'.format(env.project_name))
        run('chmod ug+wx /home/ec2-user/projects/{0}/upload'.format(env.project_name))

        # Setup the forums
        with cd('/home/ec2-user/projects/{0}/html/ops'.format(env.project_name)):
            run('php create_forums.php')

        # Copy files into place
        with cd('/home/ec2-user/boinc-magphys/machine-setup/boinc'):
            run('fab --set project_name={0},gmail_account={1} setup_postfix'.format(env.project_name, env.gmail_account))
            run('fab --set project_name={0} create_first_version'.format(env.project_name))
            run('fab --set project_name={0} start_daemons'.format(env.project_name))

        # Setup the crontab job to keep things ticking
        run('echo "PYTHONPATH=/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src" >> /tmp/crontab.txt')
        run('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/{0} ; /home/ec2-user/projects/{0}/bin/start --cron" >> /tmp/crontab.txt'.format(env.project_name))
        run('crontab /tmp/crontab.txt')

        # Setup the ops area password
        with cd('/home/ec2-user/projects/{0}/html/ops'.format(env.project_name)):
            run('htpasswd -bc .htpasswd {0} {1}'.format(env.ops_username, env.ops_password))

        # Create users and start services
        sudo('usermod -a -G ec2-user apache')
        sudo('chkconfig httpd --add')
        sudo('chkconfig httpd on')
        sudo('service httpd start')

    # Setup the logrotation
    sudo('''echo "/home/ec2-user/projects/{0}/log_*/*.log
/home/ec2-user/projects/{0}/log_*/*.out
{{
  notifempty
  daily
  compress
  rotate 10
  dateext
  copytruncate
}}" > /etc/logrotate.d/boinc'''.format(env.project_name))

    # Setup the ssh key
    run('ssh-keygen -t rsa -N "" -f /home/ec2-user/.ssh/id_rsa')
    run('cat /home/ec2-user/.ssh/id_rsa.pub >> /home/ec2-user/.ssh/authorized_keys')


def to_boolean(choice, default=False):
    """
    Convert the yes/no to true/false

    :param choice: the text string input
    :type choice: string
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    choice_lower = choice.lower()
    if choice_lower in valid:
        return valid[choice_lower]

    return default


def yum_update():
    """
    Make sure things are up to date
    """
    # Update the AMI completely
    sudo('yum --assumeyes --quiet update')


def resize_file_system():
    """
    Resize the file system as AWS doesn't do that when you start an AMI
    """
    # Resize the file system
    sudo('resize2fs /dev/sda1')


def yum_pip_update():
    """
    Make sure things are up to date
    """
    # Update the AMI completely
    sudo('yum --assumeyes --quiet update')

    # Update the pip install
    sudo('pip-2.7 install -U {0}'.format(PIP_PACKAGES))


@task
@serial
def base_setup_env():
    """
    Ask a series of questions before deploying to the cloud.
    """
    if 'ebs_size' not in env:
        prompt('EBS Size (GB): ', 'ebs_size', default=20, validate=int)
    if 'ami_name' not in env:
        prompt('AMI Name: ', 'ami_name', default='BasePythonSetup')

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

    # Make the swap we might need
    make_swap()

    # Perform the base install
    base_install()

    # Save the instance as an AMI
    puts("Stopping the instance")
    env.ec2_connection.stop_instances(env.ec2_instance.id, force=True)
    while not env.ec2_instance.update() == 'stopped':
        fastprint('.')
        time.sleep(5)

    puts("The AMI is being created. Don't forget to terminate the instance if not needed")
    env.ec2_connection.create_image(env.ec2_instance.id, env.ami_name, description='The base BOINC-MAGPHYS AMI')

    puts('All done')

@task
@serial
def boinc_setup_env():
    """
    Ask a series of questions before deploying to the cloud.

    Allow the user to select if a Elastic IP address is to be used
    """
    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    ec2_connection = boto.connect_ec2()
    images = ec2_connection.get_all_images(owners=['self'])
    puts('Available images')
    for image in images:
        puts('Image: {0: <15} {1: <35} {2}'.format(image.id, image.name, image.description))

    if 'ami_name' not in env:
        prompt('AMI id to build from: ', 'ami_id')
    if 'ops_username' not in env:
        prompt('Ops area username: ', 'ops_username', default='user')
    if 'ops_password' not in env:
        prompt('Password: ', 'ops_password')
    if 'project_name' not in env:
        prompt('BOINC project name: ', 'project_name')

    # Check the names supplied
    for char in ['_', '.', ',', '-', '+']:
        if char in env.project_name:
            abort('The project name must just contain [A-Z][a-z][0-9]')

    if 'instance_name' not in env:
        prompt('AWS Instance name: ', 'instance_name', default=env.project_name)
    if 'aws_user' not in env:
        prompt('AWS User:', 'aws_user', default='pogs_test')
    if 'gmail_account' not in env:
        prompt('GMail Account:', 'gmail_account', default=env.project_name)
    if 'gmail_password' not in env:
        prompt('GMail Password:', 'gmail_password')
    if 'docmosis_key' not in env:
        prompt('Docmosis Key:', 'docmosis_key')
    if 'branch' not in env:
        prompt('Git Branch <return> for master:', 'branch')
    if 'create_s3' not in env:
        prompt('Create S3 Buckets:', 'create_s3', default='Y')
    if 'start_boinc' not in env:
        prompt('Start the BOINC system:', 'start_boinc', default='Y')

    # Check the aws key exists
    file_name = get_aws_keyfile()
    if not os.path.exists(file_name):
        abort('Could not find the file {0}'.format(file_name))

    # Create the instance in AWS
    ec2_instance = start_ami_instance(env.ami_id, env.instance_name)
    env.hosts = [ec2_instance.dns_name]
    env.user = USERNAME
    env.key_filename = AWS_KEY


@task
@serial
def boinc_deploy_with_db():
    """
    Deploy the single server environment

    Deploy the single server system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[boinc_setup_env])

    resize_file_system()
    yum_pip_update()
    copy_public_keys()

    # Wait for things to settle down
    time.sleep(5)
    boinc_install(True)


@task
@serial
def boinc_deploy_without_db():
    """
    Deploy the single server environment

    Deploy the single server system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[boinc_setup_env])

    resize_file_system()
    yum_pip_update()
    copy_public_keys()

    # Wait for things to settle down
    time.sleep(5)
    boinc_install(False)


@task
@serial
def boinc_final_messages():
    """
    Print the final messages
    """
    if env.host_string == env.hosts[0]:
        puts('''


##########################################################################
##########################################################################

##########################################################################


You need to do the following manual steps:

SSH
1) Edit the /etc/hosts file on each server and put in the hostname used
   by BOINC for each server
   Like this:
   127.0.0.1   localhost localhost.localdomain
    23.23.126.96 ip-10-80-75-121 ec2-23-23-126.96.compute-1.amazonaws.com
    23.21.118.134 ip-10-83-98-164 ec2-23-21-188-134.compute-1.amazonaws.com
2) Connect to each of the servers from the other to ensure they can connect

MYSQL
1) Modify the database.settings file to have the private hostname for the
   DB server
2) Allow DB root access from the other servers
      create user 'root'@'hostname';
      grant all privileges on *.* to 'root'@'hostname' with grant option;

BOINC
1) Modify the config.xml to run tasks on the other nodes
2) If the database is on one of the servers setup the DB host in
   config.xml


##########################################################################

##########################################################################
##########################################################################
''')
