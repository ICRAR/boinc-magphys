# BOINC

This directory contains the files to build the BOINC servers in the AWS cloud.

The **fabfile.py** does all the heavy lifting for building the test environment.

* fab setup_env gluster1 gluster2 gluster3 deploy_with_db - will deploy everything on a dual gluster server including the DB
* fab setup_env gluster1 gluster2 gluster3 deploy_without_db - will deploy everything on a dual gluster server without the DB
* fab setup_env single_server deploy_with_db - will deploy everything on a single server with the DB

You can use a config file if you don't want to type values again and again, but the main one is hidden (I don't want DB passwords in clear text in GitHub :-) )

This will create a brand new EC2 instance and run the scripts for setting up a newer version of the server.

