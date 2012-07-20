"""
Create a single instance with all the components running on the single instance
"""

# make sure we have the bits we need
import sys
import time

try:
    import boto
    import paramiko
except ImportError, e:
    print "You need to have boto and paramiko installed for this to work"
    sys.exit()

# Now run the proper script
import getpass
import create_instance
import utils

DB_USER = 'root'

class CreateSingleEcsInstance(create_instance.CreateEc2Instance):
    def __init__(self):
        create_instance.CreateEc2Instance.__init__(self)

    def stage02(self):
        # Finish the build
        # Activate the DB
        self._run_command('sudo mysql_install_db')
        self._run_command('sudo chown -R mysql:mysql /var/lib/mysql/*')
        self._run_command('''echo "service { 'mysqld': ensure => running, enable => true }" | sudo puppet apply''')

        # Wait for it to start up
        time.sleep(15)

        # Make the POGS project
        self._run_command('cd /home/ec2-user/boinc/tools')
        self._run_command('yes | ./make_project -v --url_base http://{0} --db_user {1} pogs'.format(self._instance.dns_name, DB_USER))

        # Setup the database for recording WU's
        self._run_command('mysql --user={0} < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql'.format(DB_USER))

        # Build the validator
        self._run_command('cd /home/ec2-user/boinc-magphys/server/src/Validator')
        self._run_command('make')

        # Move to the magphys area and start configuring
        self._run_command('cd /home/ec2-user/boinc-magphys/machine-setup')

        # setup_website
        self._run_command('sudo rake setup_website')

        # This is needed because the files that Apache serve are inside the user's home directory.
        self._run_command('chmod 711 /home/ec2-user')
        self._run_command('chmod -R oug+r /home/ec2-user/projects/pogs')
        self._run_command('chmod -R oug+x /home/ec2-user/projects/pogs/html')
        self._run_command('chmod ug+w /home/ec2-user/projects/pogs/log_*')
        self._run_command('chmod ug+wx /home/ec2-user/projects/pogs/upload')

        # Edit the files
        self._run_command('cd /home/ec2-user/boinc-magphys/machine-setup')
        self._run_command('python2.7 file_editor_single.py')

        # Setup the forums
        self._run_command('cd /home/ec2-user/projects/pogs/html/ops')
        self._run_command('php create_forums.php')

        # Copy files into place
        self._run_command('cd /home/ec2-user/boinc-magphys/machine-setup')
        self._run_command('rake update_versions')
        self._run_command('rake start_daemons')

        # Setup the crontab job to keep things ticking
        self._run_command('crontab -l > /tmp/crontab.txt')
        self._run_command('echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt')
        self._run_command('crontab /tmp/crontab.txt')

        # Setup the ops area password
        self._run_command('cd /home/ec2-user/projects/pogs/html/ops')
        self._run_command('htpasswd -bc .htpasswd {0} {1}'.format(ops_username, ops_password))

use_elastic_ip = utils.query_yes_no('Do you want to assign an Elastic IP to this instance', 'no')
public_ip = None
if use_elastic_ip:
    public_ip = raw_input('What is the public IP address: ')
ops_username = raw_input('Ops area username: ')
ops_password = getpass.getpass('Password: ')
instance_name = raw_input('Instance name: ')

ec2_instance = CreateSingleEcsInstance()
ec2_instance.setup(use_elastic_ip, public_ip)
ec2_instance.stage01()
ec2_instance.name_instance(instance_name)
ec2_instance.stage02()
ec2_instance.close()

# Done
print '-------------------------'
print 'Done'
