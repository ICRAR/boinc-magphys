#!/bin/bash

. variables.sh

# Puppet and git should be installed by the python
sudo puppet boinc-magphys.pp

# Is the DB here - if so activate it
if [[ -z "$DB_HOST" ]]; then
sudo mysql_install_db
sudo chown -R mysql:mysql /var/lib/mysql/*

echo "service { 'mysqld': ensure => running, enable => true }" | sudo puppet apply
fi

# Recommended version per http://boinc.berkeley.edu/download_all.php on 2012-07-10
svn co http://boinc.berkeley.edu/svn/trunk/boinc /home/ec2-user/boinc

cd /home/ec2-user/boinc
./_autosetup

# A bug in the configure.ac needs this to be run twice
./_autosetup
./configure --disable-client --disable-manager
make

# Make the POGS project
cd /home/ec2-user/boinc/tools

if [[ -z "$DB_HOST" ]]; then
yes | ./make_project -v --url_base $BASE_URL --db_user $DB_USER pogs
else
yes | ./make_project -v --url_base $BASE_URL --db_user $DB_USER --db_host $DB_HOST --db_name $DB_NAME -db_passwd $DB_PASSWD pogs
fi

# Setup the crontab job to keep things ticking
crontab -l > /tmp/crontab.txt
echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt
crontab /tmp/crontab.txt

# Setup the database for recording WU's
if [[ -z "$DB_HOST" ]]; then
#Local setup
mysql --user=$DB_USER < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql
else
mysql --user=$DB_USER --password=$DB_PASSWD --host=$DB_HOST < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql
fi

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
