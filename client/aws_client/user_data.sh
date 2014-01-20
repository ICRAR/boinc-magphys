#!/bin/bash
cd /home/ec2-user/boinc/client/
su --session-command "./boinc --daemon" ec2-user

# Pause to let things get running
sleep 120s

# Attach
su --session-command "./boinccmd --project_attach http://pogs.theskynet.org/pogs/ <authenticator>" ec2-user
