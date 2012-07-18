#!/bin/bash

. variables.sh


# Activate the DB
sudo mysql_install_db
sudo chown -R mysql:mysql /var/lib/mysql/*

echo "service { 'mysqld': ensure => running, enable => true }" | sudo puppet apply

# Wait for it to start up
sleep 15

# Make the POGS project
cd /home/ec2-user/boinc/tools

yes | ./make_project -v --url_base $BASE_URL --db_user $DB_USER pogs

# Setup the database for recording WU's
mysql --user=$DB_USER < /home/ec2-user/boinc-magphys/server/src/database/create_database.sql

# Build the validator
cd /home/ec2-user/boinc-magphys/server/src/Validator
make

# Move to the magphys area and start configuring
cd /home/ec2-user/boinc-magphys/machine-setup

# setup_website
sudo rake setup_website

# This is needed because the files that Apache serve are inside the user's home directory.
chmod 711 /home/ec2-user
chmod -R oug+r /home/ec2-user/projects/pogs
chmod -R oug+x /home/ec2-user/projects/pogs/html
chmod ug+w /home/ec2-user/projects/pogs/log_*
chmod ug+wx /home/ec2-user/projects/pogs/upload

# Edit the files
cd /home/ec2-user/boinc-magphys/machine-setup
python2.7 file_editor_single.py

# Setup the forums
cd /home/ec2-user/projects/pogs/html/ops
php create_forums.php

# Copy files into place
cd /home/ec2-user/boinc-magphys/machine-setup
rake update_versions
rake start_daemons

# Setup the crontab job to keep things ticking
crontab -l > /tmp/crontab.txt
echo "0,5,10,15,20,25,30,35,40,45,50,55 * * * * cd /home/ec2-user/projects/pogs ; /home/ec2-user/projects/pogs/bin/start --cron" >> /tmp/crontab.txt
crontab /tmp/crontab.txt

