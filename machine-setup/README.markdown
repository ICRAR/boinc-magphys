These are scripts for creating a new EC2 instance with the BOINC server installed.
The idea is to make setting up such an instance easily reproducible by encouraging a "scripting ➞ spin up ➞ verify ➞ start over" workflow, which eliminates any non-scripted configuration.

An instance of the BOINC server can be created by running
* python ./create_single_instance.py
* python ./create_multiple_instances.py

This will create a brand new EC2 instance and run the scripts for setting up a newer version of the server.
