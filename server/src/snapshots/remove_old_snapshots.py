#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
Remove old snapshots
"""
import argparse
import logging
import os
from datetime import datetime, timedelta

import boto

LOG = logging.getLogger(__name__)


def parser_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('days', type=int, help='How many days ago')
    parser.add_argument('start_text', nargs='*', help='The text to match on')
    return parser.parse_args()


def matches(name, start_text_list):
    for start_text in start_text_list:
        if name.startswith(start_text):
            return True

    return False


def remove_snapshots(args):
    start_text = args.start_text
    before = datetime.utcnow() - timedelta(days=args.days)

    deletion_counter = 0
    size_counter = 0

    if os.path.exists(os.path.join(os.path.expanduser('~'), '.aws/credentials')):
        ec2_connection = boto.connect_ec2(profile_name='theSkyNet')
    else:
        ec2_connection = boto.connect_ec2()

    for snapshot in ec2_connection.get_all_snapshots(owner='self'):

        start_time = datetime.strptime(
            snapshot.start_time,
            '%Y-%m-%dT%H:%M:%S.000Z'
        )

        if start_time < before and 'Name' in snapshot.tags and matches(snapshot.tags['Name'], start_text):
            LOG.info(
                'Deleting id: {id}, name: {name}, size: {size}, time: {time}'.format(
                    id=snapshot.id,
                    name=snapshot.tags['Name'],
                    size=snapshot.volume_size,
                    time=snapshot.start_time
                )
            )
            deletion_counter += 1
            size_counter = size_counter + snapshot.volume_size

            # Now delete it
            snapshot.delete()

    LOG.info(
        'Deleted {number} snapshots totalling {size} GB'.format(
            number=deletion_counter,
            size=size_counter
        )
    )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    arguments = parser_arguments()
    remove_snapshots(arguments)
