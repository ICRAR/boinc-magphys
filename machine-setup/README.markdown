# BOINC

This directory contains the files to build the BOINC servers in the AWS cloud.
The idea is to make setting up such an instance easily reproducible by encouraging a "scripting ➞ spin up ➞ verify ➞ start over" workflow, which eliminates any non-scripted configuration.

The **fabfile.py** does all the heavy lifting.

* fab test_env test_deploy_with_db - will deploy everything on a single server including the DB
* fab test_env test_deploy_without_db - will deploy everything on a single server without the DB
* fab test_env test_deploy - will deploy everything on a single server
* fab prod_env prod_env prod_deploy_stage01 prod_deploy_stage02 prod_deploy_stage03 prod_deploy_stage04 - will deploy to the multi-server production environment
* fab --conf=file.env --linewise prod_env prod_env prod_deploy_stage01 prod_deploy_stage02 prod_deploy_stage03 prod_deploy_stage04 - will deploy to the multi-server production environment in parallel. To make this work you must use an env file else fabric complains

This will create a brand new EC2 instance and run the scripts for setting up a newer version of the server.

# MySQL

To create a user and grant them privilege in MySQl do the following:
* CREATE USER 'theskynet'@'%' IDENTIFIED BY 'Password1';
* grant alter,create,delete,drop,index,insert,select,show databases, show view, update on *.* to 'theskynet'@'%';
