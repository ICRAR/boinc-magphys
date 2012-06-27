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
sudo -u boinc svn co http://boinc.berkeley.edu/svn/tags/boinc_core_release_7_0_25 /opt/boinc

cd /opt/boinc
sudo -u boinc ./_autosetup
sudo -u boinc ./configure --disable-client --disable-manager
sudo -u boinc make

cd /opt/boinc/tools

if [[ -z "$DB_HOST" ]]; then
yes | sudo -u boinc ./make_project -v --test_app --url_base $BASE_URL --db_user $DB_USER pogs
else
yes | sudo -u boinc ./make_project -v --url_base $BASE_URL --db_user $DB_USER --db_host $DB_HOST --db_name $DB_NAME -db_passwd $DB_PASSWD pogs
fi

## ARGH
## /opt/boinc/projects/pogs/html/user/create_account.php
## contains an error on line 51 ("$name" should be "$user_name")
##
sudo -u boinc sed --in-place '51d' /opt/boinc/projects/pogs/html/user/create_account.php
sudo -u boinc sed --in-place '51iif (!is_valid_user_name($user_name, $reason)) {' /opt/boinc/projects/pogs/html/user/create_account.php
