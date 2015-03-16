#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013-2013
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
from os.path import expanduser, join, exists
import boto
import os
import time
from boto.ec2 import blockdevicemapping

from fabric.api import run, sudo, put, env, require
from fabric.context_managers import cd
from fabric.contrib.files import append, comment
from fabric.decorators import task, serial
from fabric.operations import prompt
from fabric.utils import puts, abort, fastprint

USERNAME = 'ec2-user'
AMI_ID = 'ami-05355a6c'
INSTANCE_TYPE = 't2.small'
INSTANCES_FILE = os.path.expanduser('~/.aws/aws_instances')
AWS_KEY = os.path.expanduser('~/.ssh/icrar-boinc.pem')
KEY_NAME = 'icrar-boinc'
KEY_NAME_VPC = 'icrar_theskynet_public_prod'
SECURITY_GROUPS = ['icrar-boinc-server']  # Security group allows SSH
SYDNEY_AWS_KEY = os.path.expanduser('~/.ssh/icrar_sydney.pem')
SYDNEY_REGION = 'ap-southeast-2'
SYDNEY_AMI_ID = 'ami-d50773ef'
SYDNEY_KEY_NAME = 'icrar_sydney'
SYDNEY_SECURITY_GROUPS = ['sg-be7ccfdb']
SYDNEY_SUBNET = 'subnet-878cc2ee'
PROD_SECURITY_GROUPS_VPC = ['sg-d608dbb9', 'sg-b23defdd']  # Security group for the VPC
TEST_SECURITY_GROUPS_VPC = ['sg-dd33e0b2', 'sg-9408dbfb']  # Security group for the VPC
PUBLIC_KEYS = os.path.expanduser('~/Keys/magphys')
PIP_PACKAGES = 'sqlalchemy pyfits Pillow fabric configobj MySQL-python boto astropy cython'
YUM_BASE_PACKAGES = 'autoconf automake binutils gcc gcc-c++ libpng-devel libstdc++46-static gdb libtool gcc-gfortran git openssl-devel python-devel python27 python27-devel curl-devel '
YUM_BOINC_PACKAGES = 'httpd httpd-devel php php-cli php-gd php-mysql mod_fcgid php-fpm postfix ca-certificates MySQL-python'
YUM_BOINC_PACKAGES_TEST = 'httpd httpd-devel php php-cli php-gd php-mysqlnd mod_fcgid php-fpm ca-certificates'


def base_install():
    """
    Perform the basic install
    """
    # Install the 5.6 version of MySQL
    sudo('sudo yum --assumeyes --quiet localinstall http://repo.mysql.com/mysql-community-release-el6-5.noarch.rpm')
    sudo('sudo yum --assumeyes --quiet install mysql-community-server mysql-community-devel')

    # Install the bits we need - we need the so the python connector will build
    sudo('yum --assumeyes --quiet install {0}'.format(YUM_BASE_PACKAGES))

    # Setup the python
    sudo('wget https://bootstrap.pypa.io/ez_setup.py -O - | python2.7')
    sudo('rm -f /usr/bin/easy_install')
    sudo('easy_install-2.7 pip')
    sudo('rm -f /usr/bin/pip')
    sudo('pip2.7 install --quiet Numpy')
    sudo('pip2.7 install --quiet {0}'.format(PIP_PACKAGES))

    # Setup the pythonpath
    append('/home/ec2-user/.bash_profile',
           ['',
            'PYTHONPATH=/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src',
            'export PYTHONPATH'])

    # Setup the HDF5
    with cd('/usr/local/src'):
        sudo('wget --no-verbose http://www.hdfgroup.org/ftp/lib-external/szip/2.1/src/szip-2.1.tar.gz')
        sudo('tar -xvzf szip-2.1.tar.gz')
        sudo('wget --no-verbose http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.14.tar.gz')
        sudo('tar -xvzf hdf5-1.8.14.tar.gz')
        sudo('rm *.gz')
    with cd('/usr/local/src/szip-2.1'):
        sudo('./configure --prefix=/usr/local/szip')
        sudo('make')
        sudo('make install')
    with cd('/usr/local/src/hdf5-1.8.14'):
        sudo('./configure --prefix=/usr/local/hdf5 --with-szlib=/usr/local/szip --enable-production')
        sudo('make')
        sudo('make install')
    sudo('''echo "/usr/local/hdf5/lib
/usr/local/szip/lib" >> /etc/ld.so.conf.d/hdf5.conf''')
    sudo('ldconfig')

    # Now install the H5py
    with cd('/tmp'):
        run('wget --no-verbose https://pypi.python.org/packages/source/h/h5py/h5py-2.4.0.tar.gz')
        run('tar -xvzf h5py-2.4.0.tar.gz')
    with cd('/tmp/h5py-2.4.0'):
        sudo('python2.7 setup.py configure --hdf5=/usr/local/hdf5')
        sudo('python2.7 setup.py build')
        sudo('python2.7 setup.py install')


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


def create_instance(ebs_size, ami_name, sydney=False):
    """
    Create the AWS instance
    :param ebs_size:
    """
    puts('Creating the instance {1} with disk size {0} GB'.format(ebs_size, ami_name))

    if exists(join(expanduser('~'), '.aws/credentials')):
        # This relies on a ~/.aws/credentials file holding the '<aws access key>', '<aws secret key>'
        puts("Using ~/.aws/credentials")
        if sydney:
            ec2_connection = boto.ec2.connect_to_region(SYDNEY_REGION, profile_name='theSkyNet')
        else:
            ec2_connection = boto.connect_ec2(profile_name='theSkyNet')
    else:
        # This relies on a ~/.boto or /etc/boto.cfg file holding the '<aws access key>', '<aws secret key>'
        puts("Using ~/.boto or /etc/boto.cfg")
        ec2_connection = boto.connect_ec2()

    dev_xvda = blockdevicemapping.EBSBlockDeviceType(delete_on_termination=True)
    dev_xvda.size = int(ebs_size)  # size in Gigabytes
    bdm = blockdevicemapping.BlockDeviceMapping()
    bdm['/dev/xvda'] = dev_xvda
    if sydney:
        reservations = ec2_connection.run_instances(
            SYDNEY_AMI_ID,
            subnet_id=SYDNEY_SUBNET,
            instance_type=INSTANCE_TYPE,
            key_name=SYDNEY_KEY_NAME,
            security_group_ids=SYDNEY_SECURITY_GROUPS,
            block_device_map=bdm)
    else:
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
    puts('Starting the instance {0} from id {1}'.format(instance_name, ami_id))

    if exists(join(expanduser('~'), '.aws/credentials')):
        # This relies on a ~/.aws/credentials file holding the '<aws access key>', '<aws secret key>'
        puts("Using ~/.aws/credentials")
        ec2_connection = boto.connect_ec2(profile_name='theSkyNet')
    else:
        # This relies on a ~/.boto or /etc/boto.cfg file holding the '<aws access key>', '<aws secret key>'
        puts("Using ~/.boto or /etc/boto.cfg")
        ec2_connection = boto.connect_ec2()

    if env.subnet_id == '':
        reservations = ec2_connection.run_instances(ami_id, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS)
    elif env.subnet_id == 'subnet-85af9fea':
        reservations = ec2_connection.run_instances(ami_id, instance_type=INSTANCE_TYPE, subnet_id=env.subnet_id, key_name=KEY_NAME_VPC, security_group_ids=PROD_SECURITY_GROUPS_VPC)
    else:
        reservations = ec2_connection.run_instances(ami_id, instance_type=INSTANCE_TYPE, subnet_id=env.subnet_id, key_name=KEY_NAME_VPC, security_group_ids=TEST_SECURITY_GROUPS_VPC)

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

    if env.subnet_id != '':
        puts('Allocating public IP address.')
        allocation = ec2_connection.allocate_address('vpc')
        time.sleep(5)
        if not ec2_connection.associate_address(public_ip=None, instance_id=instance.id, allocation_id=allocation.allocation_id):
            abort('Could not associate the IP to the instance {0}'.format(instance.id))

        # Give AWS time to switch everything over
        time.sleep(10)
        instance.update(True)

    # The instance is started, but not useable (yet)
    puts('Started the instance(s) now waiting for the SSH daemon to start.')
    for i in range(12):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # Return the instance
    return instance, ec2_connection


def make_swap():
    """
    Make the swap space
    """
    sudo('dd if=/dev/zero of=/swapfile bs=1M count=2048')
    sudo('mkswap /swapfile')
    sudo('swapon /swapfile')


def boinc_install(test_server=False):
    """
    Perform the tasks to install the whole BOINC server on a single machine
    """
    # Get the packages
    if test_server:
        sudo('yum --assumeyes --quiet install {0}'.format(YUM_BOINC_PACKAGES_TEST))
    else:
        sudo('yum --assumeyes --quiet install {0}'.format(YUM_BOINC_PACKAGES))

    if not test_server:
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

    # Grab the latest trunk from GIT
    run('git clone --quiet git://boinc.berkeley.edu/boinc-v2.git boinc')

    with cd('/home/ec2-user/boinc'):
        run('./_autosetup')
        run('./configure --disable-client --disable-manager')
        run('make')

    # Create users and services
    sudo('usermod -a -G ec2-user apache')


def pogs_install(with_db, test_server=False):
    """
    Perform the tasks to install the whole BOINC server on a single machine
    """
    # Get the packages
    if test_server:
        sudo('yum --assumeyes --quiet install {0}'.format(YUM_BOINC_PACKAGES_TEST))
    else:
        sudo('yum --assumeyes --quiet install {0}'.format(YUM_BOINC_PACKAGES))

    # Setup Users
    if test_server:
        puts('No users on the test server')
    else:
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

    if test_server:
        run('mkdir -p /home/ec2-user/archive')
        run('mkdir -p /home/ec2-user/boinc-magphys')
        run('mkdir -p /home/ec2-user/galaxies')
        run('mkdir -p /home/ec2-user/projects')
    else:
        nfs_mkdir('archive')
        nfs_mkdir('boinc-magphys')
        nfs_mkdir('galaxies')
        nfs_mkdir('projects')
    run('mkdir -p /home/ec2-user/archive/to_store')

    # Clone our code
    if env.branch == '':
        run('git clone --quiet git://github.com/ICRAR/boinc-magphys.git')
    else:
        run('git clone --quiet -b {0} git://github.com/ICRAR/boinc-magphys.git'.format(env.branch))

    # Create the .boto file
    run('''echo "[Credentials]
aws_access_key_id = {0}
aws_secret_access_key = {1}" >> /home/ec2-user/.boto'''.format(env.aws_access_key_id, env.aws_secret_access_key))

    # Setup the S3 environment
    if to_boolean(env.create_s3):
        with cd('/home/ec2-user/boinc-magphys/machine-setup/boinc-pogs'):
            run('fab --set project_name={0} create_s3'.format(env.project_name))

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

        run('''echo '# DB Settings
databaseUserid = "root"
databasePassword = ""
databaseHostname = "localhost"
databaseName = "magphys"
boincDatabaseName = "{0}"' > /home/ec2-user/boinc-magphys/server/src/config/pogs.settings'''.format(env.project_name))

    else:
        # Setup the database for recording WU's
        run('mysql --user={0} --host={1} --password={2} < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql'.format(env.db_username, env.db_host_name, env.db_password))

        # Make the BOINC project
        with cd('/home/ec2-user/boinc/tools'):
            run('./make_project -v --no_query --drop_db_first --url_base http://{0} --db_user {1} --db_host={2} --db_passwd={3} {4}'
                .format(env.hosts[0], env.db_username, env.db_host_name, env.db_password, env.project_name))

        run('''echo '# DB Settings
databaseUserid = "{0}"
databasePassword = "{1}"
databaseHostname = "{2}"
databaseName = "magphys"
boincDatabaseName = "{3}"' > /home/ec2-user/boinc-magphys/server/src/config/pogs.settings'''.format(env.db_username, env.db_password, env.db_host_name, env.project_name))

    run('''echo '
# Work Generation settings
min_pixels_per_file = "15"
row_height = "7"
threshold = "1000"
high_water_mark = "400"
report_deadline = "7"

# Archive settings
delete_delay = "5"
boinc_statistics_delay = "2"

# POGS Settings
tmp = "/tmp"
boinc_project_root = "/home/ec2-user/projects/{0}"
project_name = "{0}"
hdf5_output_directory = "/home/ec2-user/archive"

# AWS settings
ami_id = "XXX"
instance_type = "m1.small"
key_name = "XXX"
security_groups = "XXX","YYY"
subnet_ids = "XXX","YYY"

[build_png_image]
    instance_type = "m1.small"
    price = 0.060

[original_image_checked]
    instance_type = "m1.small"
    price = 0.060

[archive_data]
    price = 0.120
    instance_type = "m1.medium"

[XXX]
    availability_zone = "us-east-1b"

[YYY]
    availability_zone = "us-east-1c"

' >> /home/ec2-user/boinc-magphys/server/src/config/pogs.settings'''.format(env.project_name))

    # Copy the config files
    if not test_server:
        run('cp /home/ec2-user/boinc-magphys/server/config/boinc_files/db_dump_spec.xml /home/ec2-user/projects/{0}/db_dump_spec.xml'.format(env.project_name))
        run('cp /home/ec2-user/boinc-magphys/server/config/boinc_files/html/user/* /home/ec2-user/projects/{0}/html/user/'.format(env.project_name))
        run('cp /home/ec2-user/boinc-magphys/server/config/boinc_files/hr_info.txt /home/ec2-user/projects/{0}/hr_info.txt'.format(env.project_name))
        run('cp /home/ec2-user/boinc-magphys/server/config/boinc_files/project_files.xml /home/ec2-user/projects/{0}/project_files.xml'.format(env.project_name))

    # Create the directories we need
    run('mkdir -p /home/ec2-user/projects/{0}/html/stats_archive'.format(env.project_name))
    run('mkdir -p /home/ec2-user/projects/{0}/html/stats_tmp'.format(env.project_name))

    comment('/home/ec2-user/projects/{0}/html/ops/create_forums.php'.format(env.project_name), '^die', char='// ')

    run('mkdir -p /home/ec2-user/projects/{0}/html/user/logos'.format(env.project_name))
    run('cp /home/ec2-user/boinc-magphys/server/logos/* /home/ec2-user/projects/{0}/html/user/logos/'.format(env.project_name))

    # Build the validator
    with cd('/home/ec2-user/boinc-magphys/server/src/magphys_validator'):
        run('make')

    # Setup the ops area password
    with cd('/home/ec2-user/projects/{0}/html/ops'.format(env.project_name)):
        run('htpasswd -bc .htpasswd {0} {1}'.format(env.ops_username, env.ops_password))

    if test_server:
        with cd('/home/ec2-user/boinc-magphys/machine-setup/boinc-pogs'):
            sudo('fab --set project_name={0} setup_website'.format(env.project_name))
    else:
        with cd('/home/ec2-user/boinc-magphys/machine-setup/boinc-pogs'):
            run('fab --set project_name={0},gmail_account={1} setup_postfix'.format(env.project_name, env.gmail_account))
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

    if not test_server:
        # Save the instance as an AMI
        puts("Stopping the instance")
        env.ec2_connection.stop_instances(env.ec2_instance.id, force=True)
        while not env.ec2_instance.update() == 'stopped':
            fastprint('.')
            time.sleep(5)

        puts("The AMI is being created. Don't forget to terminate the instance if not needed")
        env.ec2_connection.create_image(env.ec2_instance.id, env.ami_name, description='The base MAGPHYS AMI')

    puts('All done')


def mount_nfs():
    """
    We have a NFS server so mount it
    :return:
    """
    sudo('yum install nfs-utils')
    sudo('mkdir -p /mnt/disk0')
    sudo('mount -t nfs {0}:/mnt/disk0 /mnt/disk0'.format(env.nfs_server))
    sudo('''echo '
# NFS
{0}:/mnt/disk0    /mnt/disk0       nfs rsize=8192,wsize=8192,timeo=14,intr 0 0' >> /etc/fstab'''.format(env.nfs_server))
    nfs_mkdir('boinc')


def nfs_mkdir(directory):
    """
    Create a directory on the NFS share

    :param directory:
    :return:
    """
    run('mkdir /mnt/disk0/{0}'.format(directory))
    run('ln -s /mnt/disk0/{0} /home/ec2-user/{0}'.format(directory))


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
    sudo('pip2.7 install -U {0}'.format(PIP_PACKAGES))


@task
@serial
def base_setup_env():
    """
    Ask a series of questions before deploying to the cloud.
    """
    if 'ebs_size' not in env:
        prompt('EBS Size (GB): ', 'ebs_size', default=20, validate=int)
    if 'ami_name' not in env:
        prompt('AMI Name: ', 'ami_name', default='base-python-ami')

    # Create the instance in AWS
    ec2_instance, ec2_connection = create_instance(env.ebs_size, env.ami_name)
    env.ec2_instance = ec2_instance
    env.ec2_connection = ec2_connection
    env.hosts = [ec2_instance.ip_address]

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
    env.ec2_connection.create_image(env.ec2_instance.id, env.ami_name, description='The base python AMI')

    puts('All done')


@task
@serial
def boinc_setup_env():
    """
    Ask a series of questions before deploying to the cloud.

    Allow the user to select if a Elastic IP address is to be used
    """
    if exists(join(expanduser('~'), '.aws/credentials')):
        # This relies on a ~/.aws/credentials file holding the '<aws access key>', '<aws secret key>'
        puts("Using ~/.aws/credentials")
        ec2_connection = boto.connect_ec2(profile_name='theSkyNet')
    else:
        # This relies on a ~/.boto or /etc/boto.cfg file holding the '<aws access key>', '<aws secret key>'
        puts("Using ~/.boto or /etc/boto.cfg")
        ec2_connection = boto.connect_ec2()

    if 'ami_id' not in env:
        images = ec2_connection.get_all_images(owners=['self'])
        puts('Available images')
        for image in images:
            puts('Image: {0: <15} {1: <35} {2}'.format(image.id, image.name, image.description))
        prompt('AMI id to build from: ', 'ami_id')
    if 'ami_name' not in env:
        prompt('AMI Name: ', 'ami_name', default='base-boinc-ami')
    if 'instance_name' not in env:
        prompt('AWS Instance name: ', 'instance_name', default='base-boinc-ami')
    if 'gmail_account' not in env:
        prompt('GMail Account:', 'gmail_account', default='theSkyNet.BOINC')
    if 'gmail_password' not in env:
        prompt('GMail Password:', 'gmail_password')
    if 'nfs_server' not in env:
        prompt('NFS Server:', 'nfs_server', default='')
    if 'subnet_id' not in env:
        prompt('Subnet id:', 'subnet_id', default='')

    # Create the instance in AWS
    ec2_instance, ec2_connection = start_ami_instance(env.ami_id, env.instance_name)
    env.ec2_instance = ec2_instance
    env.ec2_connection = ec2_connection
    env.hosts = [ec2_instance.ip_address]

    # Add these to so we connect magically
    env.user = USERNAME
    env.key_filename = AWS_KEY


@task
@serial
def boinc_build_ami():
    """
    Deploy the single server environment

    Deploy the single server system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[boinc_setup_env])

    resize_file_system()
    yum_pip_update()

    # Wait for things to settle down
    time.sleep(5)

    # Do we need to mount the NFS system?
    mount_nfs()
    boinc_install()

    # Save the instance as an AMI
    puts("Stopping the instance")
    env.ec2_connection.stop_instances(env.ec2_instance.id, force=True)
    while not env.ec2_instance.update() == 'stopped':
        fastprint('.')
        time.sleep(5)

    puts("The AMI is being created. Don't forget to terminate the instance if not needed")
    env.ec2_connection.create_image(env.ec2_instance.id, env.ami_name, description='The base BOINC AMI')

    puts('All done')


@task
@serial
def build_test_server():
    """
    Build a test server in the Sydney region
    """
    # Create the instance in AWS
    ec2_instance, ec2_connection = create_instance(15, 'POGS Test Server', True)
    env.ec2_instance = ec2_instance
    env.ec2_connection = ec2_connection
    env.host_string = 'ec2-user@{0}'.format(ec2_instance.ip_address)
    # env.hosts = [ec2_instance.ip_address]
    env.branch = 'develop'
    env.create_s3 = 'no'
    env.aws_access_key_id = 'key_id'
    env.aws_secret_access_key = 'secret_access_key'
    env.project_name = 'pogs_test'
    env.ops_username = 'user'
    env.ops_password = 'user'

    # Add these to so we connect magically
    env.user = USERNAME
    env.key_filename = SYDNEY_AWS_KEY

    puts('env: {0}'.format(env))

    # Make sure the FS is resized
    resize_file_system()

    # Make the swap we might need
    make_swap()

    # Perform the base install
    base_install()
    yum_pip_update()

    # Wait for things to settle down
    time.sleep(5)

    boinc_install(test_server=True)

    # Wait for things to settle down
    time.sleep(5)
    pogs_install(with_db=True, test_server=True)

    # Now set up the remain POGS bits
    start_pogs()


@task
@serial
def pogs_setup_env():
    """
    Ask a series of questions before deploying to the cloud.

    Allow the user to select if a Elastic IP address is to be used
    """
    if exists(join(expanduser('~'), '.aws/credentials')):
        # This relies on a ~/.aws/credentials file holding the '<aws access key>', '<aws secret key>'
        puts("Using ~/.aws/credentials")
        ec2_connection = boto.connect_ec2(profile_name='theSkyNet')
    else:
        # This relies on a ~/.boto or /etc/boto.cfg file holding the '<aws access key>', '<aws secret key>'
        puts("Using ~/.boto or /etc/boto.cfg")
        ec2_connection = boto.connect_ec2()

    if 'ami_id' not in env:
        images = ec2_connection.get_all_images(owners=['self'])
        puts('Available images')
        for image in images:
            puts('Image: {0: <15} {1: <35} {2}'.format(image.id, image.name, image.description))

        prompt('AMI id to build from: ', 'ami_id')
    if 'ami_name' not in env:
        prompt('AMI Name: ', 'ami_name', default='base-magphys-ami')
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
    if 'gmail_account' not in env:
        prompt('GMail Account:', 'gmail_account', default='theSkyNet.BOINC')
    if 'branch' not in env:
        prompt('Git Branch <return> for master:', 'branch')
    if 'create_s3' not in env:
        prompt('Create S3 Buckets:', 'create_s3', default='Y')
    if 'aws_access_key_id' not in env:
        prompt('AWS Access Key:', 'aws_access_key_id', default='')
    if 'aws_secret_access_key' not in env:
        prompt('AWS Secret Access Key:', 'aws_secret_access_key', default='')
    if 'nfs_server' not in env:
        prompt('NFS Server:', 'nfs_server', default='')
    if 'subnet_id' not in env:
        prompt('Subnet id:', 'subnet_id', default='')

    # Create the instance in AWS
    ec2_instance, ec2_connection = start_ami_instance(env.ami_id, env.instance_name)
    env.ec2_instance = ec2_instance
    env.ec2_connection = ec2_connection
    env.hosts = [ec2_instance.ip_address]

    # Add these to so we connect magically
    env.user = USERNAME
    env.key_filename = AWS_KEY


@task
@serial
def pogs_deploy_with_db():
    """
    Deploy the single server environment

    Deploy the single server system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[pogs_setup_env])

    resize_file_system()
    yum_pip_update()
    copy_public_keys()

    # Wait for things to settle down
    time.sleep(5)
    pogs_install(True)


@task
@serial
def pogs_deploy_without_db():
    """
    Deploy the single server environment

    Deploy the single server system in the AWS cloud with the database running on a different server
    """
    require('hosts', provided_by=[pogs_setup_env])

    resize_file_system()
    yum_pip_update()
    copy_public_keys()

    # Wait for things to settle down
    time.sleep(5)
    pogs_install(False)


@task
@serial
def boinc_final_messages():
    """
    Print the final messages
    """
    puts('''


##########################################################################
##########################################################################

##########################################################################


You need to do the following manual steps:

AWS:
1) Add the ami details to the pogs.settings

SSH
1) Connect to each of the servers from the other to ensure they can connect

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


@task
@serial
def start_pogs():
    # Copy files into place
    with cd('/home/ec2-user/boinc-magphys/machine-setup/boinc-pogs'):
        run('fab --set project_name={0} create_first_version'.format(env.project_name))
        run('fab --set project_name={0} start_daemons'.format(env.project_name))

    # Setup the crontab job to keep things ticking
    run('''echo 'MAILTO=""
PYTHONPATH=/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src
echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/{0} ; /home/ec2-user/projects/{0}/bin/start --cron" >> /tmp/crontab.txt'''.format(env.project_name))
    run('crontab /tmp/crontab.txt')

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
