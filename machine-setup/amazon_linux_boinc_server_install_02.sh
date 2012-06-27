#!/bin/bash

. variables.sh

# Setup the database for recording WU's
if [[ -z "$DB_HOST" ]]; then
#Local setup
mysql --user=$DB_USER < /home/ec2-user/boinc-magphys/server/src/WorkGeneration/create_link_database.sql
else
mysql --user=$DB_USER --password=$DB_PASSWD --host=$DB_HOST < /home/ec2-user/boinc-magphys/server/src/WorkGeneration/create_link_database.sql
fi

# Setup the database for Assimilating data
if [[ -z "$DB_HOST" ]]; then
#Local setup
mysql --user=$DB_USER < /home/ec2-user/boinc-magphys/server/src/Assimilator/create_assimilator_tables.sql
else
mysql --user=$DB_USER --password=$DB_PASSWD --host=$DB_HOST < /home/ec2-user/boinc-magphys/server/src/Assimilator/create_assimilator_tables.sql
fi

# Setup the python
wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg
sudo sh setuptools-0.6c11-py2.7.egg
rm setuptools-0.6c11-py2.7.egg
sudo rm -f /usr/bin/easy_install
sudo easy_install-2.7 pip
sudo rm -f /usr/bin/pip
sudo pip-2.7 install mysql-connector
sudo pip-2.7 install Numpy pyfits
sudo pip-2.7 install sqlalchemy

# Move to the magphys area and start configuring
cd /home/ec2-user/boinc-magphys

# setup_website
sudo rake setup_website

# Copy files into place
rake update_versions
rake start_daemons

crontab -l > /tmp/crontab.txt
echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /opt/boinc/projects/pogs ; //opt/boinc/projects/pogs/bin/start --cron" >> /tmp/crontab.txt
crontab  /tmp/crontab.txt
