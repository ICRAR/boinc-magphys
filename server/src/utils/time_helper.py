#
#    Copyright (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
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

import datetime
from . import static_vars  # declared in init


@static_vars(thirty=[4, 6, 9, 11], thirty1=[1, 3, 5, 7, 8, 10, 12])
def get_month_days():
    """
    Returns the number of days in this month
    :return: NUmber of days in this month
    """

    # Get the number of days in the current month
    now = datetime.datetime.now()

    if now.month in get_month_days.thirty:
        return 30
    elif now.month in get_month_days.thirty1:
        return 31
    else:
        # Leap year handling
        if now.year % 4 != 0:
            return 28
        elif now.year % 100 != 0:
            return 29
        elif now.year % 400 != 0:
            return 28
        else:
            return 29


def get_start_of_day():
    """
    Returns the time that this current day first started
    :return: Time object representing the exact start of this day
    """
    right_now = datetime.datetime.now()
    return right_now - datetime.timedelta(hours=right_now.hour, minutes=right_now.minute)


def get_hours_ago(hours):
    """
    Returns the time 'hours' hours ago
    :param hours: number of hours ago
    :return: Datetime object representing the time 'hours' hours ago.
    """

    right_now = datetime.datetime.now()
    return right_now - datetime.timedelta(hours=hours)


def seconds_since_epoch(the_time):
    """
    Returns the number of seconds since 1/1/1970
    :param the_time: datetime object to convert to seconds
    :return: Number of seconds from 1/1/1970 to this time
    """

    return (the_time - datetime.datetime(1970, 1, 1)).total_seconds()
