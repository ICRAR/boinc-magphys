#! /usr/bin/env python2.7
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
Module for loading the run details into the database
"""
from decimal import Decimal
import logging
import hashlib

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

def get_redshift(filename):
    """
    Find and return the read shift
    """
    index = filename.index('_z')
    redshift = filename[index+2:]
    redshift = redshift[:-5]
    return Decimal(redshift)

def get_md5(filename):
    """
    Get the md5sum for the file
    >>> get_md5(/Users/kevinvinsen/Documents/ICRAR/work/boinc-magphys/server/runs/0001/infrared_dce08_z0.0000.lbr.gz)
    65671c99ba116f2c0e3b87f6e20f6e43
    >>> get_md5(/Users/kevinvinsen/Documents/ICRAR/work/boinc-magphys/server/runs/0001/starformhist_cb07_z0.0000.lbr.gz)
    a646f7f23f058e6519d1151508a448fa
    """
    file = open(filename, "rb")
    hash = hashlib.md5()
    hex_hash = None
    while True:
        piece = file.read(10240)

        if piece:
            hash.update(piece)
        else: # we're at end of file
            hex_hash = hash.hexdigest()
            break

    file.close()
    return hex_hash
