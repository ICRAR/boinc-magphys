# BOINC

This directory contains the files to build the various types of server required to support the POGS project in the AWS cloud.

The **fabfile.py** does all the heavy lifting for building the environments. It loads all the Python and the GlusterFS client

# BASE AMI

This command creates the Base AMI that the others are based off.

* fab base_setup_env base_build_ami


# BOINC Node

These commands create the BOINC instances.

* fab boinc_setup_env boinc_build_ami

# POGS Node

These commands create the POGS instances.

* fab pogs_setup_env pogs_deploy_with_db - will deploy everything including the DB Server
* fab --set db_host_name==aa,db_username=bb,db_password=cc pogs_setup_env pogs_deploy_without_db - will deploy everything without the DB Server
