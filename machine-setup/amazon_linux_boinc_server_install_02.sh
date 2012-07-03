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
chmod ug+w /home/ec2-user/projects/pogs/log_*
chmod ug+wx /home/ec2-user/projects/pogs/upload

# Edit the files
cd /home/ec2-user/boinc-magphys/machine-setup
python2.7 file_editor.py

# Copy files into place
cd /home/ec2-user/boinc-magphys/machine-setup
rake update_versions
rake start_daemons
