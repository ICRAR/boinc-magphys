# BOINC

This directory contains the files to build the BOINC servers in the AWS cloud.

The **fabfile.py** does all the heavy lifting for building the test environment.

* fab test_env test_deploy_with_db - will deploy everything on a single server including the DB
* fab test_env test_deploy_without_db - will deploy everything on a single server without the DB

You can use a config file if you don't want to type values again and again, but the main one is hidden (I don't want DB passwords in clear text in GitHub :-) )

This will create a brand new EC2 instance and run the scripts for setting up a newer version of the server.

