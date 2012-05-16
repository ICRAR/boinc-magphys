#!/bin/bash

BOINC_USER=ec2-user

cd /home/$BOINC_USER

export BOINC_SRC=/home/$BOINC_USER/boinc
rake setup_website
rake copy_files
#rake update_versions
#rake create_work
#rake start_daemons

