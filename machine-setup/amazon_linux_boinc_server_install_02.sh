#!/bin/bash

. variables.sh

# Move to the magphys area and start configuring
cd /home/ec2-user/boinc-magphys/machine-setup

# setup_website
sudo rake setup_website

# This is needed because the files that Apache serve are inside the user's home directory.
chmod 711 /home/ec2-user
chmod -R oug+r /home/ec2-user/projects/pogs
chmod -R oug+x /home/ec2-user/projects/pogs/html
chmod oug+w /home/ec2-user/projects/pogs/log_*

# Setup the pythonpath
echo ' ' >> ~/.bash_profile
echo 'PYTHONPATH=$PYTHONPATH:/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src/Assimilator' >> ~/.bash_profile
echo 'export PYTHONPATH' >> ~/.bash_profile

wget http://aarnet.dl.sourceforge.net/project/mysql-python/mysql-python/1.2.3/MySQL-python-1.2.3.tar.gz
tar -xvf MySQL-python-1.2.3.tar.gz
cd MySQL-python-1.2.3
sudo python2.7 setup.py install
cd /home/ec2-user
sudo rm -rf /home/ec2-user/MySQL-python-1.2.3*

# Copy files into place
cd /home/ec2-user/boinc-magphys/machine-setup
rake update_versions
rake start_daemons
