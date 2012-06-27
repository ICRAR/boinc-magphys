These are scripts for creating a new EC2 instance with the BOINC server installed. 
The idea is to make setting up such an instance easily reproducible by encouraging a "scripting ➞ spin up ➞ verify ➞ start over" workflow, which eliminates any non-scripted configuration. 

An instance of the BOINC server can be created by running
* python ./create_instance.py 

This will create a brand new EC2 instance and run the scripts for setting up a newer version of the server, 
(amazon_linux_boinc_server_install_01.sh, amazon_linux_boinc_server_install_02.sh, amazon_linux_boinc_server_install_03.sh).
