#!/bin/bash
cd /home/ec2-user/boinc/client/
sudo -u ec2-user -c "./boinc --daemon"

# Pause to let things get running
sleep 120s

# Attach
sudo -u ec2-user -c "./boinccmd --project_attach http://pogs.theskynet.org/pogs/ <authenticator>"

