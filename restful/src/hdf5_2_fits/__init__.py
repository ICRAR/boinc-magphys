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
Load the configuration files
"""
from os.path import dirname, exists
from configobj import ConfigObj

HDF5_DIRECTORY = None
OUTPUT_DIRECTORY = None
NGAS_HOSTNAME = None
FROM_EMAIL = None
SMTP_SERVER = None

db_file_name = dirname(__file__) + '/restful.settings'
if exists(db_file_name):
    config = ConfigObj(db_file_name)
    HDF5_DIRECTORY = config['HDF5_DIRECTORY']
    OUTPUT_DIRECTORY = config['OUTPUT_DIRECTORY']
    NGAS_HOSTNAME = config['NGAS_HOSTNAME']
    FROM_EMAIL = config['FROM_EMAIL']
    SMTP_SERVER = config['SMTP_SERVER']

else:
    HDF5_DIRECTORY = '/tmp'
    OUTPUT_DIRECTORY = '/tmp'
    NGAS_HOSTNAME = 'cortex'
    FROM_EMAIL = 'kevin.vinsen@icrar.org'
    SMTP_SERVER = 'smtp.ivec.org'

print("""
HDF5_DIRECTORY   = {0}
OUTPUT_DIRECTORY = {1}
NGAS_HOSTNAME    = {2}
FROM_EMAIL       = {3}
SMTP_SERVER      = {4}""".format(HDF5_DIRECTORY, OUTPUT_DIRECTORY, NGAS_HOSTNAME, FROM_EMAIL, SMTP_SERVER))
