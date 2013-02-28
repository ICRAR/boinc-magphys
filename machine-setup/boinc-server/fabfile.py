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

from fabric.api import run, sudo, put, env, require
from fabric.context_managers import cd
from fabric.contrib.files import append, comment
from fabric.decorators import task, serial
from fabric.operations import prompt
from fabric.utils import puts, abort, fastprint

USERNAME = 'ec2-user'
AMI_ID = 'ami-1624987f'
INSTANCE_TYPE = 'm1.small'
INSTANCES_FILE = os.path.expanduser('~/.aws/aws_instances')
AWS_KEY = os.path.expanduser('~/.ssh/icrar-boinc.pem')
KEY_NAME = 'icrar-boinc'
SECURITY_GROUPS = ['icrar-boinc-server'] # Security group allows SSH
PUBLIC_KEYS = os.path.expanduser('~/Documents/Keys')

def base_install(host0):
    """
    Perform the basic install
    """
    if host0:
        # Clone our code
        run('git clone git://github.com/ICRAR/boinc-magphys.git')

    # Puppet and git should be installed by the python
    with cd('/home/ec2-user/boinc-magphys/machine-setup'):
        sudo('puppet apply boinc-magphys.pp')

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

    # Setup NAGIOS
    sudo('chkconfig nrpe on')
    sudo('service nrpe start')

    # Setup the HDF5
    with cd('/usr/local/src'):
        sudo('wget http://www.hdfgroup.org/ftp/lib-external/szip/2.1/src/szip-2.1.tar.gz')
        sudo('tar -xvzf szip-2.1.tar.gz')
        sudo('wget http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.10.tar.gz')
        sudo('tar -xvzf hdf5-1.8.10.tar.gz')
        sudo('rm *.gz')
    with cd('/usr/local/src/szip-2.1'):
        sudo('./configure --prefix=/usr/local/szip')
        sudo('make')
        sudo('make install')
    with cd('/usr/local/src/hdf5-1.8.10'):
        sudo('./configure --prefix=/usr/local/hdf5 --with-szlib=/usr/local/szip --enable-production')
        sudo('make')
        sudo('make install')
    sudo('''echo "/usr/local/hdf5/lib
/usr/local/szip/lib" >> /etc/ld.so.conf.d/hdf5.conf''')
    sudo('ldconfig')

    # Setup BOINC
    if host0:
        # Recommended version per http://boinc.berkeley.edu/download_all.php on 2012-07-10
        run('svn co http://boinc.berkeley.edu/svn/trunk/boinc /home/ec2-user/boinc')

        with cd('/home/ec2-user/boinc'):
            run('./_autosetup')
            run('./configure --disable-client --disable-manager')
            run('make')

        # Setup the pythonpath
        append('/home/ec2-user/.bash_profile',
            ['',
             'PYTHONPATH=/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src',
             'export PYTHONPATH'])

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
    sudo('pip-2.7 install boto')

    # Plotting and reporting
    sudo('pip-2.7 install matplotlib')
    sudo('pip-2.7 install astropy')

    with cd('/tmp'):
        run('wget https://h5py.googlecode.com/files/h5py-2.1.0.tar.gz')
        run('tar -xvzf h5py-2.1.0.tar.gz')
    with cd('/tmp/h5py-2.1.0'):
        sudo('python2.7 setup.py build --hdf5=/usr/local/hdf5')
        sudo('python2.7 setup.py install')

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

def build_mod_wsgi():
    """
    Build the WSGI for the Python web interface
    """
    run('mkdir -p /tmp/build')

    with cd('/tmp/build'):
        run('wget http://modwsgi.googlecode.com/files/mod_wsgi-3.3.tar.gz')
        run('tar -xvf mod_wsgi-3.3.tar.gz')
    with cd('/tmp/build/mod_wsgi-3.3'):
        run('./configure --with-python=/usr/bin/python2.7')
        run('make')
        sudo('make install')

    # Clean up
    sudo('rm -rf /tmp/build')

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

def create_instance(stub_name, number_instances, ebs_size):
    """
    Create the AWS instance
    """
    puts('Creating {0} instances with "{1}" as the stub'.format(number_instances, stub_name))

    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    conn = boto.connect_ec2()

    reservations = conn.run_instances(AMI_ID, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS, min_count=number_instances, max_count=number_instances)
    instances = reservations.instances
    # Sleep so Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)

    # Are we running yet?
    for i in range(int(number_instances)):
        while not instances[i].update() == 'running':
            fastprint('.')
            time.sleep(5)

    # Sleep a bit more Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # Tag the instance
    for i in range(int(number_instances)):
        conn.create_tags([instances[i].id], {'Name': '{0}{1:02d}'.format(stub_name, i)})

    # Associate an Elastic IP
    for instance in instances:
        puts('Current DNS name is {0}. About to get an Elastic IP'.format(instance.dns_name))
        public_ip = conn.allocate_address()
        if not conn.associate_address(instance_id=instance.id, public_ip=public_ip.public_ip):
            abort('Could not associate the IP {0} to the instance {1}'.format(public_ip.public_ip, instance.id))

    # Give AWS time to switch everything over
    time.sleep(10)

    # Load the new instance data as the dns_name may have changed
    for instance in instances:
        instance.update(True)
    for instance in instances:
        puts('Current DNS name is {0} after associating the Elastic IP'.format(instance.dns_name))

    # Add the extra storage
    for instance in instances:
        volume = conn.create_volume(ebs_size, instance.placement)
        time.sleep(4)
        volume.attach(instance.id, '/dev/sdg')

    # The instance is started, but not useable (yet)
    puts('Started the instance(s) now waiting for the SSH daemon to start.')
    for i in range(12):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # we have to return an ASCII string
    host_names = []
    for instance in instances:
        host_names.append(str(instance.dns_name))
    puts('Host names = {0}'.format(host_names))
    return host_names

def create_shared_home():
    # Link the area so we have a common home
    if env.host_string == env.hosts[0]:
        sudo('mv /home/ec2-user /mnt/data && ln -s /mnt/data/ec2-user/ /home/ec2-user')
        sudo('chown ec2-user:ec2-user /home/ec2-user')
    else:
        sudo('rm -rf /home/ec2-user && ln -s /mnt/data/ec2-user/ /home/ec2-user')
        sudo('chown ec2-user:ec2-user /home/ec2-user')

def format_drive():
    """
    Format the drive
    """
    # Create the swap
    sudo('dd if=/dev/zero of=/swapfile bs=1M count=2048')
    sudo('mkswap /swapfile')
    sudo('swapon /swapfile')

    # Create the shared drives
    sudo('parted -a optimal /dev/sdg --script mklabel gpt')
    sudo('parted -a optimal /dev/sdg --script mkpart primary 0% 100%')
    time.sleep(2)
    sudo('mkfs.xfs -f -L data /dev/sdg1')
    sudo('mkdir -p /mnt/brick')
    sudo('chattr +i /mnt/brick')
    sudo('mount /dev/sdg1 /mnt/brick')
    sudo('''echo '
# Swap
/swapfile swap swap defaults 0 0
#
# XFS mounts
LABEL=data              /mnt/brick                   xfs     defaults        0 0
# GlusterFS
{0}:/gv0        /mnt/data                glusterfs defaults,transport=tcp,_netdev 1 0' >> /etc/fstab'''.format(env.host_string))

def gluster_install():
    """
    Load the Gluster RPMs and start the service
    """
    # Load the Gluster FS RPM's
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-3.3.1-1.el6.x86_64.rpm')
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-fuse-3.3.1-1.el6.x86_64.rpm')
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-geo-replication-3.3.1-1.el6.x86_64.rpm')
    run('wget http://download.gluster.org/pub/gluster/glusterfs/3.3/3.3.1/EPEL.repo/epel-6/x86_64/glusterfs-server-3.3.1-1.el6.x86_64.rpm')
    sudo('yum --assumeyes --quiet install *.rpm')
    sudo('chkconfig glusterd --add')
    sudo('chkconfig glusterd on')
    sudo('service glusterd start')
    run('rm *.rpm')

def gluster_mount():
    if env.host_string == env.hosts[0]:
        host_names = ''
        for host_name in env.hosts:
            host_names += host_name + ':/mnt/brick '
        sudo('gluster volume create gv0 replica 2 {0}'.format(host_names))
        sudo('gluster volume start gv0')
    sudo('mkdir -p /mnt/data')
    sudo('mount -o transport=tcp -t glusterfs {0}:/gv0 /mnt/data'.format(env.host_string))

def gluster_probe():
    for host_name in env.hosts:
        # Only probe other servers
        if env.host_string != host_name:
            sudo('gluster peer probe {0}'.format(host_name))
    sudo('gluster peer status')

def single_install(with_db):
    """
    Perform the tasks to install the whole BOINC server on a single machine
    """
    if with_db:
        # Activate the DB
        sudo('mysql_install_db')
        sudo('chown -R mysql:mysql /var/lib/mysql/*')
        run('''echo "service { 'mysqld': ensure => running, enable => true }" | sudo puppet apply''')
        sudo('service mysqld start')

        # Wait for it to start up
        time.sleep(5)

    if with_db:
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

    # Setup Django files
    run('''echo 'template_dir = "/home/ec2-user/boinc-magphys/server/src/templates"
image_dir = "/home/ec2-user/galaxyImages"
docmosis_key = "{0}"
docmosis_template = "Report.doc"' >> /home/ec2-user/boinc-magphys/server/src/config/django.settings'''.format(env.docmosis_key))

    # Setup Work Generation files
    run('''echo 'image_directory = "/home/ec2-user/galaxyImages"
min_pixels_per_file = "15"
row_height = "6"
threshold = "1000"
high_water_mark = "400"
report_deadline = "7"
boinc_project_root = "/home/ec2-user/projects/{0}"' >> /home/ec2-user/boinc-magphys/server/src/config/work_generation.settings'''.format(env.project_name))

    # Setup Apache for Django.
    sudo('cp /home/ec2-user/boinc-magphys/server/src/pogssite/config/wsgi.conf /etc/httpd/conf.d/')
    sudo('cp /home/ec2-user/boinc-magphys/server/src/pogssite/config/pogs.django.conf /etc/httpd/conf.d/')

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
    with cd ('/home/ec2-user/boinc-magphys/server/src/magphys_validator'):
        run('make')

    # setup_website
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
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    choice_lower = choice.lower()
    if choice_lower in valid:
        return valid[choice_lower]

    return default

def yum_install():
    # Update the AMI completely
    sudo('yum --assumeyes --quiet update')

    # Install xfsprogs, puppet and git
    sudo('yum --assumeyes --quiet install xfsprogs puppet git')

@task
@serial
def setup_env():
    """Configure the single server environment

    Ask a series of questions before deploying to the cloud.

    Allow the user to select if a Elastic IP address is to be used
    """
    if 'instances' not in env:
        prompt('Number of instances: ', 'instances')
    if 'ebs_size' not in env:
        prompt('EBS Size (GB): ', 'ebs_size')
    if 'ops_username' not in env:
        prompt('Ops area username: ', 'ops_username')
    if 'ops_password' not in env:
        prompt('Password: ', 'ops_password')
    if 'instance_stub_name' not in env:
        prompt('AWS Instance name stub: ', 'instance_stub_name')
    if 'project_name' not in env:
        prompt('BOINC project name: ', 'project_name')
    if 'gmail_account' not in env:
        prompt('GMail Account:', 'gmail_account')
    if 'gmail_password' not in env:
        prompt('GMail Password:', 'gmail_password')
    if 'docmosis_key' not in env:
        prompt('Docmosis Key:', 'docmosis_key')

    # Create the instance in AWS
    host_names = create_instance(env.instance_stub_name, env.instances, env.ebs_size)
    env.hosts = host_names
    env.user = USERNAME
    env.key_filename = AWS_KEY
    env.roledefs = {
        'main' : [host_names[0]],
        'additional' : host_names[1:]
    }

@task
@serial
def single_server():
    """
    Copy the files and start building a single server
    """
    require('hosts', provided_by=[setup_env])

    yum_install()

    # Wait for things to settle down
    time.sleep(15)
    format_drive()

    # Wait for things to settle down
    time.sleep(15)

@task
@serial
def gluster1():
    """
    Copy the files and start Gluster
    """
    require('hosts', provided_by=[setup_env])

    yum_install()
    gluster_install()

    # Wait for things to settle down
    time.sleep(15)
    format_drive()

    # Wait for things to settle down
    time.sleep(15)

@task
@serial
def gluster2():
    """
    Because AWS has public and private names we need to do the peer probe on all the nodes
    """
    require('hosts', provided_by=[setup_env])

    gluster_probe()

    # Wait for things to settle down
    time.sleep(15)

@task
@serial
def gluster3():
    """
    Create and Start the Gluster Volume (on host[0]) and mount it on all nodes
    """
    require('hosts', provided_by=[setup_env])

    gluster_mount()

    # Wait for things to settle down
    time.sleep(15)
    create_shared_home()

    # Wait for things to settle down
    time.sleep(15)

@task
@serial
def deploy_with_db():
    """
    Deploy the single server environment

    Deploy the single server system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[setup_env])

    copy_public_keys()
    base_install(env.host_string == env.hosts[0])

    # Wait for things to settle down
    time.sleep(5)
    build_mod_wsgi()

    # Wait for things to settle down
    time.sleep(5)
    if env.host_string == env.hosts[0]:
        single_install(True)

    # Wait for things to settle down
    time.sleep(5)

@task
@serial
def deploy_without_db():
    """
    Deploy the single server environment

    Deploy the single server system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[setup_env])

    copy_public_keys()
    base_install(env.host_string == env.hosts[0])

    # Wait for things to settle down
    time.sleep(5)
    build_mod_wsgi()

    # Wait for things to settle down
    time.sleep(5)
    if env.host_string == env.hosts[0]:
        single_install(False)

    # Wait for things to settle down
    time.sleep(5)

@task
@serial
def final_messages():
    """
    Print the final messages
    """
    if env.host_string == env.hosts[0]:
        puts('''


##########################################################################
##########################################################################

##########################################################################


You need to do the following manual steps:

Django
1) Go to '/home/ec2-user/boinc-magphys/server/src/pogssite'
2) run 'python27 manage.py syncdb' to initialise the django database

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

NGAS
1) If you need to move files from the server install NGAS

NAGIOS
1) Edit the config file and put the server address in it


##########################################################################

##########################################################################
##########################################################################
''')
