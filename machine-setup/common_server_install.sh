#!/bin/bash

. variables.sh

# Puppet and git should be installed by the python
sudo puppet boinc-magphys.pp

# Recommended version per http://boinc.berkeley.edu/download_all.php on 2012-07-10
svn co http://boinc.berkeley.edu/svn/trunk/boinc /home/ec2-user/boinc

cd /home/ec2-user/boinc
./_autosetup

# A bug in the configure.ac needs this to be run twice
./_autosetup
./configure --disable-client --disable-manager
make

# Setup the pythonpath
echo ' ' >> ~/.bash_profile
echo 'PYTHONPATH=$PYTHONPATH:/home/ec2-user/boinc/py:/home/ec2-user/boinc-magphys/server/src' >> ~/.bash_profile
echo 'export PYTHONPATH' >> ~/.bash_profile

# Setup the python
wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg
sudo sh setuptools-0.6c11-py2.7.egg
rm setuptools-0.6c11-py2.7.egg
sudo rm -f /usr/bin/easy_install
sudo easy_install-2.7 pip
sudo rm -f /usr/bin/pip
sudo pip-2.7 install sqlalchemy
sudo pip-2.7 install Numpy
sudo pip-2.7 install pyfits

# Used by BOINC in the assimilator
sudo pip-2.7 install MySQL-python
