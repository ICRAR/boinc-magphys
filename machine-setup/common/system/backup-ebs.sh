#!/bin/bash
#
# Script to take a backup of the various volumes.
#
# NOTE: Need to create a policy to create snapshot with ec2:CreateSnapshot Action, assign it to a user dedicated
# user, putting their access information below.  Risk is conisdered low as all key could be used to do is
# create snapshots.
#
# This script should be run regularly (at least daily) to ensure a recent snapshot is available for recovery.
# The resulting image will look like a "crashed" machine if used as the starting point for a machine.
# It is best if the machine requiring backup runs the script for its volumes so that the "sync" gives the best
# chance of having the most stable image to recover from.
#
# @Mark Boulton
#
export AWS_ACCESS_KEY=
export AWS_SECRET_KEY=

export EC2_HOME=/opt/aws/apitools/ec2
export JAVA_HOME=/usr/lib/jvm/jre

DAY=`date +%Y%m%d%H%M`
LOG_FILE=xxxxxxxx/backup-ebs.log

TMP_FILE=backup-ebs-tmp-file

#creating the snapshots

echo $DAY >> $LOG_FILE

sync
/opt/aws/bin/ec2-create-snapshot --region us-east-1 vol-xxxxxxxx -d "<server name> sda root Set01 $DAY" | tee --append $LOG_FILE | cut -d \	 -f 2 > $TMP_FILE
/opt/aws/bin/ec2-create-tags `cat $TMP_FILE` --tag timestamp=$DAY --tag "Name=<server name> vol-xxxxxxxx $DAY" >> $LOG_FILE

rm $TMP_FILE
