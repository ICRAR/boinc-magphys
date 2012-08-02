# BOINC

This directory contains the files to build the BOINC servers in the AWS cloud.
The idea is to make setting up such an instance easily reproducible by encouraging a "scripting ➞ spin up ➞ verify ➞ start over" workflow, which eliminates any non-scripted configuration.

The various **fabfile.py** files do all the heavy lifting.

These will create a brand new EC2 instance and run the scripts for setting up a newer version of the server.

# MySQL

To create a user and grant them privilege in MySQl do the following:
* CREATE USER 'theskynet'@'%' IDENTIFIED BY 'Password1';
* grant alter,create,delete,drop,index,insert,select,show databases, show view, update on *.* to 'theskynet'@'%';
