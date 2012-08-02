# BOINC

This directory contains the files to build the BOINC servers in the AWS cloud.

The **fabfile.py** does all the heavy lifting.

* fab prod_env prod_env prod_deploy_stage01 prod_deploy_stage02 prod_deploy_stage03 prod_deploy_stage04 - will deploy to the multi-server production environment
* fab --conf=file.env --linewise prod_env prod_env prod_deploy_stage01 prod_deploy_stage02 prod_deploy_stage03 prod_deploy_stage04 - will deploy to the multi-server production environment in parallel. To make this work you must use an env file else fabric complains

This will create a brand new EC2 instance and run the scripts for setting up a newer version of the server.

