This directory contains the files to build the BOINC servers in the AWS cloud.
The idea is to make setting up such an instance easily reproducible by encouraging a "scripting ➞ spin up ➞ verify ➞ start over" workflow, which eliminates any non-scripted configuration.

The **fabfile.py** does all the heavy lifting.

* fab test_env test_deploy - will deploy everything on a single server
* fab prod_env prod_deploy - will deploy to the multi-server production environ

These are scripts for creating a new EC2 instance with the BOINC server installed.

An instance of the BOINC server can be created by running
* python ./create_single_instance.py
* python ./create_multiple_instances.py

This will create a brand new EC2 instance and run the scripts for setting up a newer version of the server.
