#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012
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
When an AMI is spun up we need to make sure that things have started properly, database connections etc.
The bash script should check to make sure the NFS is working as this code is on the NFS

This module contains the code to do this
"""
from sqlalchemy import create_engine, select, func
from config import DB_LOGIN
from database.database_support_core import REGISTER


def check_database_connection():
    """
    Check we can connect to the database
    :return:
    """
    try:
        engine = create_engine(DB_LOGIN)
        connection = engine.connect()

        # Read some data
        count = connection.execute(select([func.count(REGISTER.c.register_id)]).where(REGISTER.c.create_time == None)).first()[0]

        connection.close()

    except Exception:
        # Something when wrong
        return False

    return True


def pass_sanity_checks():
    """
    Do we pass the sanity checks
    :return: True if we pass the sanity checks
    """
    if not check_database_connection():
        return False

    if not public_ip():
        return False

    if not access_s3():
        return False

    # If we get here we're good
    return True
