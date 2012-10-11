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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Column
from sqlalchemy.types import BigInteger, String

Base = declarative_base()
class Result(Base):
    __tablename__ = 'result'
    id = Column(BigInteger, primary_key=True)
    server_state = Column(BigInteger)
    workunitid = Column(BigInteger)
    appid = Column(BigInteger)

class Workunit(Base):
    __tablename__ = 'workunit'
    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    assimilate_state = Column(BigInteger)
