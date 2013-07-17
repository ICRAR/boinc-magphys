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
Connect to the BOINC database
"""
from sqlalchemy import Column, MetaData, BigInteger, String, Table

BOINC_METADATA = MetaData()

RESULT = Table('result',
               BOINC_METADATA,
               Column('id', BigInteger, primary_key=True, autoincrement=True),
               Column('server_state', BigInteger),
               Column('workunitid', BigInteger),
               Column('appid', BigInteger),
               Column('name', String),
)

WORK_UNIT = Table('workunit',
                  BOINC_METADATA,
                  Column('id', BigInteger, primary_key=True, autoincrement=True),
                  Column('name', String),
                  Column('assimilate_state', BigInteger)
)

USER = Table('user',
             BOINC_METADATA,
             Column('id', BigInteger, primary_key=True, autoincrement=True),
             Column('name', String)
)
