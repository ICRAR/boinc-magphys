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
The plot data
"""
from sqlalchemy import MetaData, Table, Column, DATE, Float, Integer, String

PLOT_METADATA = MetaData()

USAGE = Table('usage',
              PLOT_METADATA,
              Column('usage_id', Integer, primary_key=True),
              Column('date', DATE, index=True, unique=True),
              Column('gflops', Float),
              Column('active_users', Integer),
              Column('registered_users', Integer),
              )

HDF5_SIZE = Table('hdf5_size',
                  PLOT_METADATA,
                  Column('hdf5_size_id', Integer, primary_key=True),
                  Column('name', String, index=True, unique=True),
                  Column('size', Integer),
                  Column('run_id', Integer),
                  )

INDIVIDUAL = Table('individual',
                   PLOT_METADATA,
                   Column('individual_id', Integer, primary_key=True),
                   Column('date', DATE, index=True),
                   Column('user_id', Integer),
                   Column('expavg_credit', Float),
                   )
