#!/bin/bash

# This is apparently one (the?) way of finding out the public hostname of an EC2 instance
# Need hostname because make_project cannot reliably find out the public hostname of EC2 instances
MY_HOSTNAME=`curl -s --fail http://169.254.169.254/latest/meta-data/public-hostname`
BASE_URL="http://$MY_HOSTNAME"

DB_USER=root
DB_HOST=
DB_NAME=
DB_PASSWD=
