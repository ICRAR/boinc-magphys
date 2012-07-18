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
import os
import glob
import time
import getpass


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

IMAGE           = 'ami-aecd60c7' # Basic 64-bit Amazon Linux AMI - old
KEY_NAME        = 'icrar-boinc'
INSTANCE_TYPE   = 't1.micro'
SECURITY_GROUPS = ['icrar-boinc-server'] # Security group allows SSH
KEY_FILE        = os.path.expanduser('~/.ssh/icrar-boinc.pem')
PUBLIC_KEYS     = os.path.expanduser('~/Documents/Keys')

db_host_name = raw_input('DB Host name: ')
db_user = raw_input('DB username: ')
db_password = getpass.getpass('Password: ')
use_elastic_ip = query_yes_no('Do you want to assign the Elastic IP [{0}] to this instance'.format(PUBLIC_IP), 'no')
ops_username = raw_input('Ops area username: ')
ops_password = getpass.getpass('Password: ')

# Create the EC2 instance
print 'Starting an EC2 instance of type {0} with image {1}'.format(INSTANCE_TYPE, IMAGE)

# This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
conn = boto.connect_ec2()

if use_elastic_ip:
    # Disassociate the public IP
    if not conn.disassociate_address(public_ip=PUBLIC_IP):
        print 'Could not disassociate the IP {0}'.format(PUBLIC_IP)

reservation = conn.run_instances(IMAGE, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS)
instance = reservation.instances[0]
time.sleep(10) # Sleep so Amazon recognizes the new instance
while not instance.update() == 'running':
    sys.stdout.write('.')
    sys.stdout.flush()
    time.sleep(5)
print '.'

if use_elastic_ip :
    print 'Current DNS name is {0}. About to associate the Elastic IP'.format(instance.dns_name)
    if not conn.associate_address(instance_id=instance.id, public_ip=PUBLIC_IP):
        print 'Could not associate the IP {0} to the instance {1}'.format(PUBLIC_IP, instance.id)
        sys.exit()

# Give AWS time to switch everything over
time.sleep(10)

# Load the new instance data as the dns_name may have changed
instance.update(True)
print 'Current DNS name is {0} after associating the Elastic IP'.format(instance.dns_name)

# The instance is started, but not useable (yet)
print 'Started the instance: {0}'.format(instance.dns_name)
print 'Waiting for the SSH daemon to start'
for i in range(12):
    sys.stdout.write('.')
    sys.stdout.flush()
    time.sleep(5)
print '.'

# Connect to the machine - with the auto add policy as we may well not know this instance
print 'Connecting to the server via SSH: {0}'.format(instance.dns_name)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(instance.dns_name, username='ec2-user', key_filename=KEY_FILE)

# Copy
print 'SFTPing public keys to the server: {0}'.format(instance.dns_name)
ftp = ssh.open_sftp()
list_of_users = []
for file in glob.glob(PUBLIC_KEYS + '/*.pub'):
    filename = os.path.basename(file)
    user,ext = os.path.splitext(filename)
    list_of_users.append(user)
    ftp.put(file, filename)

ftp.close()

# Open a shell. We have to use the invoke_shell because the scripts have SUDO elements
channel = ssh.invoke_shell(width=200)
channel.set_combine_stderr(True)
print 'Timeout on channel: {0}'.format(channel.gettimeout())

def wait_for_prompt():
    """
    Wait for the prompt
    """
    buff1 = ''
    while True:
        while channel.recv_ready():
            buff2 = channel.recv(1024)
            sys.stdout.write(buff2)
            sys.stdout.flush()
            if buff2.endswith(']$ '):
                return
            else:
                # Defend against the rare occasion when the ']' is at the end of the
                # buffer and the $ starts the next buffer
                buff = buff1 + buff2
                if buff.endswith(']$ '):
                    return
            buff1 = buff2
            time.sleep(0.1)

def run_command(command):
    """
    Execute a command.
    """
    channel.send(command + '\n')
    wait_for_prompt()

# Run the scripts
wait_for_prompt()
# Update the AMI completely
run_command('sudo yum --assumeyes update')

# Install puppet and git
run_command('sudo yum --assumeyes install puppet git')

# Clone our code
run_command('git clone git://github.com/ICRAR/boinc-magphys.git')

# Now run the rest of the setup
run_command('cd ~/boinc-magphys/machine-setup/multiple_instance')
run_command('''sed -i '' 9,11D variables.sh''')
run_command('sed ')
run_command('sed ')
run_command('chmod +x amazon_linux_boinc_servers_install_*.sh')
run_command('./amazon_linux_boinc_servers_install_01.sh')

for user in list_of_users:
    run_command('sudo useradd {0}'.format(user))
    run_command('sudo mkdir /home/{0}/.ssh'.format(user))
    run_command('sudo chmod 700 /home/{0}/.ssh'.format(user))
    run_command('sudo chown {0}:{0} /home/{0}/.ssh'.format(user))
    run_command('sudo mv /home/ec2-user/{0}.pub /home/{0}/.ssh/authorized_keys'.format(user))
    run_command('sudo chmod 700 /home/{0}/.ssh/authorized_keys'.format(user))
    run_command('sudo chown {0}:{0} /home/{0}/.ssh/authorized_keys'.format(user))

    # Add them to the sudoers
    run_command('''sudo su -l root -c 'echo "{0} ALL = NOPASSWD: ALL" >> /etc/sudoers' '''.format(user))

# Setup the ops area password
run_command('cd /home/ec2-user/projects/pogs/html/ops')
run_command('htpasswd -bc .htpasswd {0} {1}'.format(ops_username, ops_password))

channel.close()
ssh.close()

# Done
print '-------------------------'
print 'Done'
