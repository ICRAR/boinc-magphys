"""
Create an instance
"""
import os
import sys
import boto
import paramiko
import glob
import time

IMAGE = 'ami-aecd60c7' # Basic 64-bit Amazon Linux AMI
KEY_NAME = 'icrar-boinc'
INSTANCE_TYPE = 't1.micro'
SECURITY_GROUPS = ['icrar-boinc-server'] # Security group allows SSH
KEY_FILE = os.path.expanduser('~/.ssh/icrar-boinc.pem')
PUBLIC_KEYS = os.path.expanduser('~/Documents/Keys')

class CreateEc2Instance():
    def __init__(self):
        self._conn = None
        self._channel = None
        self._ssh = None

    def setup(self, use_elastic_ip, public_ip):
        self._use_elastic_ip = use_elastic_ip
        self._public_ip = public_ip

    def close(self):
        self._channel.close()
        self._ssh.close()

    def _wait_for_prompt(self):
        """
        Wait for the prompt
        """
        buff1 = ''
        while True:
            while self._channel.recv_ready():
                buff2 = self._channel.recv(1024)
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

    def _run_command(self, command):
        """
        Execute a command.
        """
        self._channel.send(command + '\n')
        self._wait_for_prompt()

    def name_instance(self, instance_name):
        self._conn.create_tags([self._instance.id], {"Name": instance_name})

    def stage01(self):
        # Create the EC2 instance
        print 'Starting an EC2 instance of type {0} with image {1}'.format(INSTANCE_TYPE, IMAGE)

        # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
        self._conn = boto.connect_ec2()

        if self._use_elastic_ip:
            # Disassociate the public IP
            if not self._conn.disassociate_address(public_ip=self._public_ip):
                print 'Could not disassociate the IP {0}'.format(self._public_ip)

        reservation = self._conn.run_instances(IMAGE, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS)
        self._instance = reservation.instances[0]
        time.sleep(10) # Sleep so Amazon recognizes the new instance
        while not self._instance.update() == 'running':
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(5)
        print '.'

        if self._use_elastic_ip:
            print 'Current DNS name is {0}. About to associate the Elastic IP'.format(self._instance.dns_name)
            if not self._conn.associate_address(instance_id=self._instance.id, public_ip=self._public_ip):
                print 'Could not associate the IP {0} to the instance {1}'.format(self._public_ip, self._instance.id)
                sys.exit()

        # Give AWS time to switch everything over
        time.sleep(10)

        # Load the new instance data as the dns_name may have changed
        self._instance.update(True)
        print 'Current DNS name is {0} after associating the Elastic IP'.format(self._instance.dns_name)

        # The instance is started, but not useable (yet)
        print 'Started the instance: {0}'.format(self._instance.dns_name)
        print 'Waiting for the SSH daemon to start'
        for i in range(12):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(5)
        print '.'

        # Connect to the machine - with the auto add policy as we may well not know this instance
        print 'Connecting to the server via SSH: {0}'.format(self._instance.dns_name)
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(self._instance.dns_name, username='ec2-user', key_filename=KEY_FILE)

        # Copy
        print 'SFTPing public keys to the server: {0}'.format(self._instance.dns_name)
        ftp = self._ssh.open_sftp()
        list_of_users = []
        for file in glob.glob(PUBLIC_KEYS + '/*.pub'):
            filename = os.path.basename(file)
            user, ext = os.path.splitext(filename)
            list_of_users.append(user)
            ftp.put(file, filename)

        ftp.close()

        # Open a shell. We have to use the invoke_shell because the scripts have SUDO elements
        self._channel = self._ssh.invoke_shell(width=200)
        self._channel.set_combine_stderr(True)
        print 'Timeout on channel: {0}'.format(self._channel.gettimeout())

        # Run the scripts
        self._wait_for_prompt()

        # Update the AMI completely
        self._run_command('sudo yum --assumeyes update')

        # Install puppet and git
        self._run_command('sudo yum --assumeyes install puppet git')

        # Clone our code
        self._run_command('git clone git://github.com/ICRAR/boinc-magphys.git')

        # Now run the rest of the setup
        self._run_command('cd ~/boinc-magphys/machine-setup')

        # Puppet and git should be installed by the python
        self._run_command('sudo puppet boinc-magphys.pp')

        # Recommended version per http://boinc.berkeley.edu/download_all.php on 2012-07-10
        self._run_command('svn co http://boinc.berkeley.edu/svn/trunk/boinc /home/ec2-user/boinc')

        self._run_command('cd /home/ec2-user/boinc')
        self._run_command('./_autosetup')
        self._run_command('./configure --disable-client --disable-manager')
        self._run_command('make')

        # Setup the pythonpath
        self._run_command('''echo ' ' >> ~/.bash_profile''')
        self._run_command('''echo 'PYTHONPATH=$PYTHONPATH:/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src' >> ~/.bash_profile''')
        self._run_command('''echo 'export PYTHONPATH' >> ~/.bash_profile''')

        # Setup the python
        self._run_command('wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg')
        self._run_command('sudo sh setuptools-0.6c11-py2.7.egg')
        self._run_command('rm setuptools-0.6c11-py2.7.egg')
        self._run_command('sudo rm -f /usr/bin/easy_install')
        self._run_command('sudo easy_install-2.7 pip')
        self._run_command('sudo rm -f /usr/bin/pip')
        self._run_command('sudo pip-2.7 install sqlalchemy')
        self._run_command('sudo pip-2.7 install Numpy')
        self._run_command('sudo pip-2.7 install pyfits')

        # Used by BOINC in the assimilator
        self._run_command('sudo pip-2.7 install MySQL-python')

        for user in list_of_users:
            self._run_command('sudo useradd {0}'.format(user))
            self._run_command('sudo mkdir /home/{0}/.ssh'.format(user))
            self._run_command('sudo chmod 700 /home/{0}/.ssh'.format(user))
            self._run_command('sudo chown {0}:{0} /home/{0}/.ssh'.format(user))
            self._run_command('sudo mv /home/ec2-user/{0}.pub /home/{0}/.ssh/authorized_keys'.format(user))
            self._run_command('sudo chmod 700 /home/{0}/.ssh/authorized_keys'.format(user))
            self._run_command('sudo chown {0}:{0} /home/{0}/.ssh/authorized_keys'.format(user))

            # Add them to the sudoers
            self._run_command('''sudo su -l root -c 'echo "{0} ALL = NOPASSWD: ALL" >> /etc/sudoers' '''.format(user))

