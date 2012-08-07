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
from fabric.decorators import task, serial
from fabric.operations import prompt
from fabric.utils import puts, abort, fastprint

USERNAME = 'ec2-user'
AMI_ID = 'ami-aecd60c7'
INSTANCE_TYPE = 'm1.small'
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


def to_boolean(choice, default=False):
    """Convert the yes/no to true/false

    :param choice: the text string input
    :type choice: string
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    choice_lower = choice.lower()
    if choice_lower in valid:
        return valid[choice_lower]

    return default

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

def single_install(with_db):
    """ Perform the tasks to install the whole BOINC server on a single machine

    The web, upload and download are all
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
            run('./make_project -v --no_query --url_base http://{0} --db_user root {1}'.format(env.hosts[WEB_HOST], env.project_name))

    else:
        # Setup the database for recording WU's
        run('mysql --user={0} --host={1} --password={2} < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql'.format(env.db_username, env.db_host_name, env.db_password))

        # Make the BOINC project
        with cd('/home/ec2-user/boinc/tools'):
            run('./make_project -v --no_query --drop_db_first --url_base http://{0} --db_user {1} --db_host={2} --db_passwd={3} {4}'
                .format(env.hosts[WEB_HOST], env.db_username, env.db_host_name, env.db_password, env.project_name))

        run('echo databaseUserid = "{0}" > /home/ec2-user/boinc-magphys/server/src/config/database.settings'.format(env.db_username))
        run('echo databasePassword = "{0}" >> /home/ec2-user/boinc-magphys/server/src/config/database.settings'.format(env.db_password))
        run('echo databaseHostname = "{0}" >> /home/ec2-user/boinc-magphys/server/src/config/database.settings'.format(env.db_host_name))
        run('echo databaseName = "magphys" >> /home/ec2-user/boinc-magphys/server/src/config/database.settings')

    # Setup Django files
    run('echo template_dir = "/home/ec2-user/boinc-magphys/server/src/templates" > /home/ec2-user/boinc-magphys/server/src/config/django.settings')
    run('echo image_dir = "/home/ec2-user/galaxyImages" >> /home/ec2-user/boinc-magphys/server/src/config/django.settings')

    # Edit the files
    sed('/home/ec2-user/projects/{0}/html/project/project.inc'.format(env.project_name), 'REPLACE WITH PROJECT NAME', 'theSkyNet {0} - the PS1 Optical Galaxy Survey'.format(env.project_name.upper()))
    sed('/home/ec2-user/projects/{0}/html/project/project.inc'.format(env.project_name), 'REPLACE WITH COPYRIGHT HOLDER', 'The International Centre for Radio Astronomy Research')
    sed('/home/ec2-user/projects/{0}/html/project/project.inc'.format(env.project_name), '"white.css"', '"black.css"')

    # As this goes through AWK we need to be a bit careful
    run('cp /home/ec2-user/projects/{0}/config.xml /home/ec2-user/projects/{0}/config.xml.bak'.format(env.project_name))
    run('''awk '/<daemons>/,/<\/daemons>/ {if ( $0 ~ /<\/daemons>/ ) print "'''
        '  <daemons>\\n'
        '    <daemon>\\n'
        '      <cmd>\\n'
        '        feeder -d 2\\n'
        '      </cmd>\\n'
        '    </daemon>\\n'
        '    <daemon>\\n'
        '      <cmd>\\n'
        '        transitioner -d 2\\n'
        '      </cmd>\\n'
        '    </daemon>\\n'
        '    <daemon>\\n'
        '      <cmd>\\n'
        '        file_deleter -d 2\\n'
        '      </cmd>\\n'
        '    </daemon>\\n'
        '    <daemon>\\n'
        '      <cmd>\\n'
        '        /home/ec2-user/boinc-magphys/server/src/magphys_validator/magphys_validator -d 3 --app magphys_wrapper --credit_from_wu --update_credited_job\\n'
        '      </cmd>\\n'
        '    </daemon>\\n'
        '    <daemon>\\n'
        '      <cmd>\\n'
        '        python2.7 /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper\\n'
        '      </cmd>\\n'
        '    </daemon>\\n'
        '''  </daemons>"; next } 1' /home/ec2-user/projects/%(name)s/config.xml.bak > /home/ec2-user/projects/%(name)s/config.xml'''% { 'name' : env.project_name})
    run('cp /home/ec2-user/projects/{0}/config.xml /home/ec2-user/projects/{0}/config.xml.bak'.format(env.project_name))
    run('''awk '/<one_result_per_user_per_wu>/,/<\/one_result_per_user_per_wu>/ {if ( $0 ~ /<\/one_result_per_user_per_wu>/ ) print "'''
        '    <delete_delay_hours>48</delete_delay_hours>\\n'
        '    <locality_scheduling/>\\n'
        '    <prefer_primary_platform>1</prefer_primary_platform>\\n'
        '''    <one_result_per_host_per_wu/>"; next } 1' /home/ec2-user/projects/%(name)s/config.xml.bak > /home/ec2-user/projects/%(name)s/config.xml''' % { 'name' : env.project_name})

    comment('/home/ec2-user/projects/{0}/html/ops/create_forums.php'.format(env.project_name), '^die', char='// ')

    sed('/home/ec2-user/projects/{0}/html/user/index.php'.format(env.project_name), 'XXX is a research project that uses volunteers', 'theSkyNet {0} is a research project that uses volunteers'.format(env.project_name.upper))
    sed('/home/ec2-user/projects/{0}/html/user/index.php'.format(env.project_name),
        'to do research in XXX.',
        'to do research in astronomy.\\n'
        'We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.\\n'
        'We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.')
    sed('/home/ec2-user/projects/{0}/html/user/index.php'.format(env.project_name), 'XXX is a research project that uses Internet-connected', 'theSkyNet {0} is a research project that uses Internet-connected'.format(env.project_name.upper()))
    sed('/home/ec2-user/projects/{0}/html/user/index.php'.format(env.project_name),
        'computers to do research in XXX.',
        'computers to do research in astronomy.\\n'
        'We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.\\n'
        'We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.')
    sed('/home/ec2-user/projects/{0}/html/user/index.php'.format(env.project_name), 'XXX is based at', 'theSkyNet {0} is based at'.format(env.project_name.upper()))
    sed('/home/ec2-user/projects/{0}/html/user/index.php'.format(env.project_name), '\[describe your institution, with link to web page\]', 'The International Centre for Radio Astronomy Research.')

    # Build the validator
    with cd ('/home/ec2-user/boinc-magphys/server/src/magphys_validator'):
        run('make')

    # setup_website
    with cd('/home/ec2-user/boinc-magphys/machine-setup/boinc'):
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
        run('fab --set project_name={0} create_first_version'.format(env.project_name))
        run('fab --set project_name={0} start_daemons'.format(env.project_name))

    # Setup the crontab job to keep things ticking
    run('echo "PYTHONPATH=/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src" >> /tmp/crontab.txt')
    run('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/{0} ; /home/ec2-user/projects/{0}/bin/start --cron" >> /tmp/crontab.txt'.format(env.project_name))
    run('crontab /tmp/crontab.txt')

    # Setup the ops area password
    with cd('/home/ec2-user/projects/{0}/html/ops'.format(env.project_name)):
        run('htpasswd -bc .htpasswd {0} {1}'.format(env.ops_username, env.ops_password))

def build_mod_wsgi():
    run('mkdir -p /home/ec2-user/build')

    with cd('/home/ec2-user/build'):
        run('wget http://modwsgi.googlecode.com/files/mod_wsgi-3.3.tar.gz')
        run('tar -xvf mod_wsgi-3.3.tar.gz')
    with cd('/home/ec2-user/build/mod_wsgi-3.3'):
        run('./configure --with-python=/usr/bin/python2.7')
        run('make')
        sudo('make install')

    # Clean up
    sudo('rm -rf /home/ec2-user/build')

@task
@serial
def test_env():
    """Configure the test environment

    Ask a series of questions before deploying to the cloud.

    Allow the user to select if a Elastic IP address is to be used
    """
    if 'use_elastic_ip' in env:
        use_elastic_ip = to_boolean(env.use_elastic_ip)
    else:
        use_elastic_ip = confirm('Do you want to assign an Elastic IP to this instance: ', False)

    public_ip = None
    if use_elastic_ip:
        if 'public_ip' in env:
            public_ip = env.public_ip
        else:
            public_ip = prompt('What is the public IP address: ', 'public_ip')

    if 'ops_username' not in env:
        prompt('Ops area username: ', 'ops_username')
    if 'ops_password' not in env:
        prompt('Password: ', 'ops_password')
    if 'instance_name' not in env:
        prompt('AWS Instance name: ', 'instance_name')
    if 'project_name' not in env:
        prompt('BOINC project name: ', 'project_name')


    # Create the instance in AWS
    host_names = create_instance([env.instance_name], use_elastic_ip, [public_ip])
    env.hosts = host_names
    env.user = USERNAME
    env.key_filename = AWS_KEY
    env.roledefs = {
        'web' : host_names,
        'upload' : host_names,
        'download' : host_names
    }

@task
@serial
def test_deploy_with_db():
    """Deploy the test environment

    Deploy the test system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[test_env])

    copy_public_keys()
    base_install()
    build_mod_wsgi()
    single_install(True)

@task
@serial
def test_deploy_without_db():
    """Deploy the test environment

    Deploy the test system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[test_env])

    copy_public_keys()
    base_install()
    build_mod_wsgi()
    single_install(False)

