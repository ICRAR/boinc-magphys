#!/usr/bin/env python

# make sure we have the bits we need
import sys
try:
    import boto
    import paramiko
except ImportError, e:
    print "You need to have boto and paramiko installed for this to work"
    sys.exit()

# Now run the proper script
import create_instance
import utils
import getpass

class CreateMultipleEc2Instances(create_instance.CreateEc2Instance):
    def __init__(self):
        create_instance.CreateEc2Instance.__init__(self)

    def stage02(self):
        self._run_command('cd ~/boinc-magphys/machine-setup/multiple_instance')
        self._run_command('sed ')

        # Setup the ops area password
        self._run_command('cd /home/ec2-user/projects/pogs/html/ops')
        self._run_command('htpasswd -bc .htpasswd {0} {1}'.format(ops_username, ops_password))

db_host_name = raw_input('DB Host name: ')
db_user = raw_input('DB username: ')
db_password = getpass.getpass('Password: ')
ops_username = raw_input('Ops area username: ')
ops_password = getpass.getpass('Password: ')

ec2_instance = CreateMultipleEc2Instances()
ec2_instance.stage01()
ec2_instance.stage02()


# Done
print '-------------------------'
print 'Done'
