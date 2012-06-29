#!/bin/bash

. variables.sh

# Move to the magphys area and start configuring
cd /home/ec2-user/boinc-magphys/machine-setup

# setup_website
sudo rake setup_website

# Copy files into place
rake update_versions
rake start_daemons
