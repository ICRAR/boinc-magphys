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

IMAGE           = 'ami-6078da09' # Basic 64-bit Amazon Linux AMI
KEY_NAME        = 'icrar-boinc'
INSTANCE_TYPE   = 't1.micro'
SECURITY_GROUPS = ['icrar-boinc-server'] # Security group allows SSH
KEY_FILE        = os.path.expanduser('~/.ssh/icrar-boinc.pem')
PUBLIC_KEYS     = os.path.expanduser('~/Documents/Keys')
PUBLIC_IP       = '23.21.160.71'

# Create the EC2 instance
print 'Starting an EC2 instance of type {0} with image {1}'.format(INSTANCE_TYPE, IMAGE)

# This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
conn = boto.connect_ec2()

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

if not conn.associate_address(instance_id=instance.id, public_ip=PUBLIC_IP):
    print 'Could not associate the IP {0} to the instance {1}'.format(PUBLIC_IP, instance.id)

# Load the new instance data as the dns_name will have changed
instance.update(True)

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
channel = ssh.invoke_shell()
channel.set_combine_stderr(True)

def wait_for_prompt():
    """
    Wait for the prompt
    """
    done = False
    while not done:
        time.sleep(0.5)
        while channel.recv_ready():
            buff = channel.recv(1024)
            sys.stdout.write(buff)
            sys.stdout.flush()
            if buff.endswith(']$ '):
                done = True

def run_command(command):
    """
    Execute a command.
    """
    #print '{0}'.format(command)
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
run_command('cd ~/boinc-magphys/machine-setup')
run_command('chmod +x amazon_linux_boinc_server_install_*.sh')
run_command('./amazon_linux_boinc_server_install_01.sh')
#run_command('./amazon_linux_boinc_server_install_02.sh')

for user in list_of_users:
    run_command('sudo useradd {0}'.format(user))
    run_command('sudo mkdir /home/{0}/.ssh'.format(user))
    run_command('sudo chmod 700 /home/{0}/.ssh'.format(user))
    run_command('sudo chown {0}:{0} /home/{0}/.ssh'.format(user))
    run_command('sudo mv /home/ec2-user/{0}.pub /home/{0}/.ssh/authorized_keys'.format(user))
    run_command('sudo chmod 700 /home/{0}/.ssh/authorized_keys'.format(user))
    run_command('sudo chown {0}:{0} /home/{0}/.ssh/authorized_keys'.format(user))

channel.close()
ssh.close()

# Done
print '-------------------------'
print 'Done'
