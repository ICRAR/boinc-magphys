#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
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
Set of functions that help programs shut down gracefully.
"""
import threading
import httplib
import time
import sys
from Boinc import boinc_project_path

SHUTDOWN_SIGNAL = False
THREAD_STARTED = False
CAUGHT_SIGINT = False


def start_poll():
    global THREAD_STARTED

    if not THREAD_STARTED:
        threading.Thread(target=shutdown_signal_poll).start()
        THREAD_STARTED = True


def shutdown():
    return SHUTDOWN_SIGNAL


def is_valid_time(dtime):
    try:
        time.strptime(dtime, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def shutdown_signal_poll():
    conn = httplib.HTTPConnection("169.254.169.254")

    global SHUTDOWN_SIGNAL

    while True:
        conn.request("GET", "/latest/meta-data/spot/termination-time")

        response = conn.getresponse()

        msg = response.read()

        if response.status == 200:
            if is_valid_time(msg):
                SHUTDOWN_SIGNAL = True
                break

        time.sleep(5)

    conn.close()

    return


def check_stop_trigger():
    """
    For fits2wu. Checks whether a stop trigger is present and closes at a good time
    if one is.
    """

    try:
        junk = open(boinc_project_path.project_path('stop_daemons'), 'r')
    except IOError:
        if CAUGHT_SIGINT:
            sys.exit(1)
    else:
        sys.exit(1)


def sigint_handler():
    global CAUGHT_SIGINT

    CAUGHT_SIGINT = True