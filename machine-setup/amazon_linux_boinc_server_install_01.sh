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

# Recommended version per http://boinc.berkeley.edu/download_all.php on 2012-05-11
sudo svn co http://boinc.berkeley.edu/svn/tags/boinc_core_release_7_0_25 /opt/boinc

# This is needed because the files that Apache serve are inside the user's home directory.
chmod 711 /opt/boinc

cd /opt/boinc
./_autosetup
./configure --disable-client --disable-manager
make

cd /opt/boinc/tools

if [[ -z "$DB_HOST" ]]; then
yes | ./make_project -v --test_app --url_base $BASE_URL --db_user $DB_USER pogs
else
yes | ./make_project -v --url_base $BASE_URL --db_user $DB_USER --db_host $DB_HOST --db_name $DB_NAME -db_passwd $DB_PASSWD pogs
fi

## ARGH
## /opt/boinc/projects/pogs/html/user/create_account.php
## contains an error on line 51 ("$name" should be "$user_name")
##
sed --in-place '51d' /opt/boinc/projects/pogs/html/user/create_account.php
sed --in-place '51iif (!is_valid_user_name($user_name, $reason)) {' /opt/boinc/projects/pogs/html/user/create_account.php

sudo chown -R boinc:boinc /opt/boinc
