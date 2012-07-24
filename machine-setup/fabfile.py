"""
Fabric file for installing the servers

This doesn't use the role decorator as it only seems to work at the top level.
"""
import glob

import boto
import os
import time

from fabric.api import run, sudo, put, env, require
from fabric.context_managers import cd
from fabric.contrib.console import confirm
from fabric.contrib.files import append, sed, comment
from fabric.decorators import task, parallel, serial
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

@task
@parallel
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
@parallel
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
@serial
def single_install():
    """ Perform the tasks to install the whole BOINC server on a single machine

    The web, upload and download are all
    """
    # Activate the DB
    sudo('mysql_install_db')
    sudo('chown -R mysql:mysql /var/lib/mysql/*')
    run('''echo "service { 'mysqld': ensure => running, enable => true }" | sudo puppet apply''')
    sudo('service mysqld start')

    # Wait for it to start up
    time.sleep(5)

    # Make the POGS project
    with cd('/home/ec2-user/boinc/tools'):
        run('./make_project -v --no_query --url_base http://{0} --db_user root pogs'.format(env.hosts[WEB_HOST]))

    # Setup the database for recording WU's
    run('mysql --user=root < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql')

    # Edit the files
    sed('/home/ec2-user/projects/pogs/html/project/project.inc', 'REPLACE WITH PROJECT NAME', 'theSkyNet POGS - the PS1 Optical Galaxy Survey')
    sed('/home/ec2-user/projects/pogs/html/project/project.inc', 'REPLACE WITH COPYRIGHT HOLDER', 'The International Centre for Radio Astronomy Research')
    sed('/home/ec2-user/projects/pogs/html/project/project.inc', '"white.css"', '"black.css"')

    # As this goes through SED we need to be a bit careful
    sed('/home/ec2-user/projects/pogs/config.xml',
        '  </daemons>',
        '    <daemon>\\n'
        '      <cmd>\\n'
        '        /home/ec2-user/boinc-magphys/server/src/Validator/magphys_validator -d 3 --app magphys_wrapper --credit_from_wu --update_credited_job\\n'
        '      </cmd>\\n'
        '    </daemon>\\n'
        '    <daemon>\\n'
        '      <cmd>\\n'
        '        python2.7 /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper\\n'
        '      </cmd>\\n'
        '    </daemon>\\n'
        '  </daemons>\\n'
        '  <locality_scheduling/>\\n')

    comment('/home/ec2-user/projects/pogs/html/ops/create_forums.php', '^die', char='// ')

    sed('/home/ec2-user/projects/pogs/html/user/index.php', 'XXX is a research project that uses volunteers', 'theSkyNet POGS is a research project that uses volunteers')
    sed('/home/ec2-user/projects/pogs/html/user/index.php',
        'to do research in XXX.',
        'to do research in astronomy.\\n'
        'We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.\\n'
        'We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.')
    sed('/home/ec2-user/projects/pogs/html/user/index.php', 'XXX is a research project that uses Internet-connected', 'theSkyNet POGS is a research project that uses Internet-connected')
    sed('/home/ec2-user/projects/pogs/html/user/index.php',
        'computers to do research in XXX.',
        'computers to do research in astronomy.\\n'
        'We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.\\n'
        'We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.')
    sed('/home/ec2-user/projects/pogs/html/user/index.php', 'XXX is based at', 'theSkyNet POGS is based at')
    sed('/home/ec2-user/projects/pogs/html/user/index.php', '\[describe your institution, with link to web page\]', 'The International Centre for Radio Astronomy Research.')

    # Build the validator
    with cd ('/home/ec2-user/boinc-magphys/server/src/Validator'):
        run('make')

    # setup_website
    with cd('/home/ec2-user/boinc-magphys/machine-setup'):
        sudo('rake setup_website')

    # This is needed because the files that Apache serve are inside the user's home directory.
    run('chmod 711 /home/ec2-user')
    run('chmod -R oug+r /home/ec2-user/projects/pogs')
    run('chmod -R oug+x /home/ec2-user/projects/pogs/html')
    run('chmod ug+w /home/ec2-user/projects/pogs/log_*')
    run('chmod ug+wx /home/ec2-user/projects/pogs/upload')

    # Setup the forums
    with cd('/home/ec2-user/projects/pogs/html/ops'):
        run('php create_forums.php')

    # Copy files into place
    with cd('/home/ec2-user/boinc-magphys/machine-setup'):
        run('rake update_versions')
        run('rake start_daemons')

    # Setup the crontab job to keep things ticking
    run('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt')
    run('crontab /tmp/crontab.txt')

    # Setup the ops area password
    with cd('/home/ec2-user/projects/pogs/html/ops'):
        run('htpasswd -bc .htpasswd {0} {1}'.format(env.ops_username, env.ops_password))

@task
@serial
def web_install():
    """Install the web site components - these are not run in parallel

    Install the web components only
    """
    if env.host_string in env.roledefs['web']:
        # Setup the database for recording WU's
        run('mysql --user={0} --host={1} --password={2} < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql'.format(env.db_username, env.db_host_name, env.db_password))

        # Make the POGS project
        with cd('/home/ec2-user/boinc/tools'):
            run('./make_project -v --no_query --drop_db_first --url_base http://{0} --db_user {1} --db_host={2} --db_passwd={3} --cgi_url={4} pogs'
                .format(env.hosts[WEB_HOST], env.db_username, env.db_host_name, env.db_password, env.hosts[UPLOAD_HOST]))

        # Edit the files
        sed('/home/ec2-user/projects/pogs/html/project/project.inc', 'REPLACE WITH PROJECT NAME', 'theSkyNet POGS - the PS1 Optical Galaxy Survey')
        sed('/home/ec2-user/projects/pogs/html/project/project.inc', 'REPLACE WITH COPYRIGHT HOLDER', 'The International Centre for Radio Astronomy Research')
        sed('/home/ec2-user/projects/pogs/html/project/project.inc', '"white.css"', '"black.css"')

        # As this goes through SED we need to be a bit careful
        sed('/home/ec2-user/projects/pogs/config.xml',
            'http://.*amazonaws\.com/pogs_cgi/file_upload_handler',
            'http://{0}/pogs_cgi/file_upload_handler'.format(env.hosts[UPLOAD_HOST]))
        sed('/home/ec2-user/projects/pogs/config.xml',
            'http://.*amazonaws\.com/pogs/download',
            'http://{0}/pogs/download'.format(env.hosts[DOWNLOAD_HOST]))
        sed('/home/ec2-user/projects/pogs/config.xml',
            '  <daemons>((.|\\n)*)</daemons>',
            '  <daemons></daemons>\\n'
            '  <locality_scheduling/>\\n')

        comment('/home/ec2-user/projects/pogs/html/ops/create_forums.php', '^die', char='// ')

        sed('/home/ec2-user/projects/pogs/html/user/index.php',
            'XXX is a research project that uses volunteers',
            'theSkyNet POGS is a research project that uses volunteers')
        sed('/home/ec2-user/projects/pogs/html/user/index.php',
            'to do research in XXX.',
            'to do research in astronomy.\\n'
            'We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.\\n'
            'We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.')
        sed('/home/ec2-user/projects/pogs/html/user/index.php',
            'XXX is a research project that uses Internet-connected',
            'theSkyNet POGS is a research project that uses Internet-connected')
        sed('/home/ec2-user/projects/pogs/html/user/index.php',
            'computers to do research in XXX.',
            'computers to do research in astronomy.\\n'
            'We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.\\n'
            'We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.')
        sed('/home/ec2-user/projects/pogs/html/user/index.php', 'XXX is based at', 'theSkyNet POGS is based at')
        sed('/home/ec2-user/projects/pogs/html/user/index.php', '\[describe your institution, with link to web page\]', 'The International Centre for Radio Astronomy Research.')

        # setup_website - all need this
        with cd('/home/ec2-user/boinc-magphys/machine-setup'):
            sudo('rake setup_website')

        # This is needed because the files that Apache serve are inside the user's home directory.
        run('chmod 711 /home/ec2-user')
        run('chmod -R oug+r /home/ec2-user/projects/pogs')
        run('chmod -R oug+x /home/ec2-user/projects/pogs/html')
        run('chmod ug+w /home/ec2-user/projects/pogs/log_*')
        run('chmod ug+wx /home/ec2-user/projects/pogs/upload')

        # Setup the forums
        with cd('/home/ec2-user/projects/pogs/html/ops'):
            run('php create_forums.php')

        # Copy files into place
        with cd('/home/ec2-user/boinc-magphys/machine-setup'):
            run('rake start_daemons')

        # Setup the crontab job to keep things ticking
        run('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt')
        run('crontab /tmp/crontab.txt')

        # Setup the ops area password
        with cd('/home/ec2-user/projects/pogs/html/ops'):
            run('htpasswd -bc .htpasswd {0} {1}'.format(env.ops_username, env.ops_password))

@task
@serial
def upload_install():
    """Install the upload components

    Install the upload components only
    """
    if env.host_string in env.roledefs['upload']:
        # Make the POGS project
        # There doesn't seem to be away build the directories and ignore the DB
        with cd('/home/ec2-user/boinc/tools'):
            run('./make_project -v --no_query --drop_db_first --url_base http://{0} --db_user {1} --db_host={2} --db_passwd={3} --cgi_url={4} pogs'
                .format(env.hosts[WEB_HOST], env.db_username, env.db_host_name, env.db_password, env.hosts[UPLOAD_HOST]))

        # As this goes through SED we need to be a bit careful
        sed('/home/ec2-user/projects/pogs/config.xml',
            'http://.*amazonaws\.com/pogs_cgi/file_upload_handler',
            'http://{0}/pogs_cgi/file_upload_handler'.format(env.hosts[UPLOAD_HOST]))
        sed('/home/ec2-user/projects/pogs/config.xml',
            'http://.*amazonaws\.com/pogs/download',
            'http://{0}/pogs/download'.format(env.hosts[DOWNLOAD_HOST]))
        sed('/home/ec2-user/projects/pogs/config.xml',
            '  <daemons>((.|\\n)*)</daemons>',
            '  <daemons>\\n'
            '    <daemon>\\n'
            '      <cmd>\\n'
            '        file_deleter --input_files_only -d 3\\n'
            '      </cmd>\\n'
            '    </daemon>\\n'
            '    <daemon>\\n'
            '      <cmd>\\n'
            '        /home/ec2-user/boinc-magphys/server/src/Validator/magphys_validator -d 3 --app magphys_wrapper --credit_from_wu --update_credited_job\\n'
            '      </cmd>\\n'
            '    </daemon>\\n'
            '    <daemon>\\n'
            '      <cmd>\\n'
            '        python2.7 /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper\\n'
            '      </cmd>\\n'
            '    </daemon>\\n'
            '  </daemons>\\n'
            '  <locality_scheduling/>\\n')

        # Build the validator
        with cd ('/home/ec2-user/boinc-magphys/server/src/Validator'):
            run('make')

        # setup_website - still need this as it is CGI
        with cd('/home/ec2-user/boinc-magphys/machine-setup'):
            sudo('rake setup_website')

        # This is needed because the files that Apache serve are inside the user's home directory.
        run('chmod 711 /home/ec2-user')
        run('chmod -R oug+r /home/ec2-user/projects/pogs')
        run('chmod ug+w /home/ec2-user/projects/pogs/log_*')
        run('chmod ug+wx /home/ec2-user/projects/pogs/upload')

        # Remove the HTML
        run('rm -rf /home/ec2-user/projects/pogs/html')

        # Copy files into place
        with cd('/home/ec2-user/boinc-magphys/machine-setup'):
            run('rake start_daemons')

        # Setup the crontab job to keep things ticking
        run('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt')
        run('crontab /tmp/crontab.txt')

@task
@serial
def download_install():
    """Install the download components

    Install the download components only
    """
    if env.host_string in env.roledefs['download']:
        # Make the POGS project
        # There doesn't seem to be away build the directories and ignore the DB
        with cd('/home/ec2-user/boinc/tools'):
            run('./make_project -v --no_query --drop_db_first --url_base http://{0} --db_user {1} --db_host={2} --db_passwd={3} --cgi_url={4} pogs'
                .format(env.hosts[WEB_HOST], env.db_username, env.db_host_name, env.db_password, env.hosts[UPLOAD_HOST]))

        # As this goes through SED we need to be a bit careful
        sed('/home/ec2-user/projects/pogs/config.xml',
            'http://.*amazonaws\.com/pogs_cgi/file_upload_handler',
            'http://{0}/pogs_cgi/file_upload_handler'.format(env.hosts[UPLOAD_HOST]))
        sed('/home/ec2-user/projects/pogs/config.xml',
            'http://.*amazonaws\.com/pogs/download',
            'http://{0}/pogs/download'.format(env.hosts[DOWNLOAD_HOST]))
        sed('/home/ec2-user/projects/pogs/config.xml',
            '  <daemons>((.|\\n)*)</daemons>',
            '  <daemons>\\n'
            '    <daemon>\\n'
            '      <cmd>\\n'
            '        feeder -d 3\\n'
            '      </cmd>\\n'
            '    </daemon>\\n'
            '    <daemon>\\n'
            '      <cmd>\\n'
            '        transitioner -d 3\\n'
            '      </cmd>\\n'
            '    </daemon>\\n'
            '    <daemon>\\n'
            '      <cmd>\\n'
            '        file_deleter --output_files_only -d 3\\n'
            '      </cmd>\\n'
            '    </daemon>\\n'
            '  </daemons>\\n'
            '  <locality_scheduling/>\\n')

        # Build the validator
        with cd ('/home/ec2-user/boinc-magphys/server/src/Validator'):
            run('make')

        # setup_website - all need this
        with cd('/home/ec2-user/boinc-magphys/machine-setup'):
            sudo('rake setup_website')
            run('rake update_versions')

        # This is needed because the files that Apache serve are inside the user's home directory.
        run('chmod 711 /home/ec2-user')
        run('chmod -R oug+r /home/ec2-user/projects/pogs')
        run('chmod ug+w /home/ec2-user/projects/pogs/log_*')
        run('chmod -R oug+x /home/ec2-user/projects/pogs/html')

        # Copy files into place
        with cd('/home/ec2-user/boinc-magphys/machine-setup'):
            run('rake start_daemons')

        # Setup the crontab job to keep things ticking
        run('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt')
        run('crontab /tmp/crontab.txt')

@task
@serial
def database_details():
    """Install the DB details

    Install the DB details onto the upload and download servers
    """
    if env.host_string in env.roledefs['download'] or env.host_string in env.roledefs['upload']:
        sed('/home/ec2-user/boinc-magphys/server/src/database/__init__.py',
            '#databaseUserid',
            'databaseUserid = {0}'.format(env.db_username))
        sed('/home/ec2-user/boinc-magphys/server/src/database/__init__.py',
            '#databasePassword',
            'databasePassword = {0}'.format(env.db_password))
        sed('/home/ec2-user/boinc-magphys/server/src/database/__init__.py',
            '#databaseHostname',
            'databaseHostname = {0}'.format(env.db_host_name))
        sed('/home/ec2-user/boinc-magphys/server/src/database/__init__.py',
            '#databaseName',
            'databaseName = magphys')

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
        public_ip = prompt('What is the public IP address: ', 'public_ip')

    if 'ops_username' not in env:
        prompt('Ops area username: ', 'ops_username')
    if 'ops_password' not in env:
        prompt('Password: ', 'ops_password')
    if 'instance_name' not in env:
        prompt('Instance name: ', 'instance_name')

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
def prod_env():
    """Configure the production environment

    This will be three servers linked to a permanent DB
    """
    if 'server_running' not in env:
        if not confirm("Is the DB server running?"):
            abort('Start the DB server')

    if 'db_host_name' not in env:
        prompt('What is the hostname of the database?', 'db_host_name')
    if 'db_username' not in env:
        prompt('What is the username of the database?', 'db_username')
    if 'db_password' not in env:
        prompt('What is the password of the database?', 'db_password')
    if 'ops_username' not in env:
        prompt('Ops area username: ', 'ops_username')
    if 'ops_password' not in env:
        prompt('Password: ', 'ops_password')
    if 'public_ip01' not in env:
        prompt('What is the public IP address of the Web Server: ', 'public_ip01')
    if 'instance_name01' not in env:
        prompt('Instance name of the Web Server: ', 'instance_name01')
    if 'public_ip02' not in env:
        prompt('What is the public IP address of the Upload Server: ', 'public_ip02')
    if 'instance_name02' not in env:
        prompt('Instance name of the Upload Server: ', 'instance_name02')
    if 'public_ip03' not in env:
        prompt('What is the public IP address of the Download Server: ', 'public_ip03')
    if 'instance_name03' not in env:
        prompt('Instance name of the Download Server: ', 'instance_name03')

    # Create the instance in AWS
    host_names = create_instance([env.instance_name01, env.instance_name02, env.instance_name03], True, [env.public_ip01, env.public_ip02, env.public_ip03])
    env.hosts = host_names
    env.user = USERNAME
    env.key_filename = AWS_KEY

    env.roledefs = {
        'web' : [host_names[WEB_HOST]],
        'upload' : [host_names[UPLOAD_HOST]],
        'download' : [host_names[DOWNLOAD_HOST]]
    }

@task
@serial
def test_deploy():
    """Deploy the test environment

    Deploy the test system in the AWS cloud with everything running on a single server
    """
    require('hosts', provided_by=[test_env])

    copy_public_keys()
    base_install()
    single_install()

@task
@parallel
def prod_deploy():
    """Deploy
    """
    require('hosts', provided_by=[prod_env])

    copy_public_keys()
    base_install()

    # Serial bit
    # As I've having to create the POGS DB three times - we need to make sure
    # I don't try to do it twice
    web_install()
    upload_install()
    download_install()

    database_details()
