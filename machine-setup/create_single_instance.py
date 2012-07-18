"""
Create a single instance with all the components running on the single instance
"""

# make sure we have the bits we need
import sys
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

class CreateSingleEcsInstance(create_instance.CreateEc2Instance):
    def __init__(self):
        create_instance.CreateEc2Instance.__init__(self)

    def stage02(self):
        # Finish the
        self._run_command('./single_instance_install.sh')

        # Setup the ops area password
        self._run_command('cd /home/ec2-user/projects/pogs/html/ops')
        self._run_command('htpasswd -bc .htpasswd {0} {1}'.format(ops_username, ops_password))

PUBLIC_IP       = '23.21.160.71'
use_elastic_ip = utils.query_yes_no('Do you want to assign the Elastic IP [{0}] to this instance'.format(PUBLIC_IP), 'no')
ops_username = raw_input('Ops area username: ')
ops_password = getpass.getpass('Password: ')
instance_name = raw_input('Instance name: ')

ec2_instance = CreateSingleEcsInstance()
ec2_instance.setup(use_elastic_ip, PUBLIC_IP, instance_name)
ec2_instance.stage01()
ec2_instance.stage02()
ec2_instance.close()

# Done
print '-------------------------'
print 'Done'
