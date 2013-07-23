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
Fix the RA and DEC for many of the galaxies
"""
import logging
import os
import sys

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../server/src')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import tempfile
import urllib2
from astropy.io.votable.table import parse_single_table
from sqlalchemy import create_engine, select, or_
import warnings
from config import DB_LOGIN
from database.database_support_core import GALAXY

# Connect to the database - the login string is set in the database package
ENGINE = create_engine(DB_LOGIN)
connection = ENGINE.connect()


def fix_name(name):
    """
    Remove the lower case a-f

    :param name:
    :return:
    """
    last_char = name[-1]
    if last_char == 'a' or last_char == 'b' or last_char == 'c' or last_char == 'd' or last_char == 'e' or last_char == 'f' or last_char == 'g':
        return name[:-1]

    return name


def getVOTable(url, table_number):
    """
    Returns VOTable from a URL and table number
    """
    tmp = tempfile.mkstemp(".xml", "pogs_fix", None, False)
    file_name = tmp[0]
    os.close(file_name)
    xml_file = tmp[1]
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req, timeout=10)
        with open(xml_file, 'w') as file_name:
            file_name.write(response.read())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            table = parse_single_table(xml_file, pedantic=False, table_number=table_number)
    except:
        raise Exception("Problem contacting VOTable provider")
    finally:
        os.remove(xml_file)

    return table


def get_ra_dec(name):
    """
    Go to NED and get the details

    :param name: the galaxy we're looking for
    :return:
    """
    try:
        url = 'http://ned.ipac.caltech.edu/cgi-bin/objsearch?expand=no&objname=' + name + '&of=xml_posn'
        table = getVOTable(url, 0)
        ra_eqj2000 = table.array['pos_ra_equ_J2000_d'][0]
        dec_eqj2000 = table.array['pos_dec_equ_J2000_d'][0]
        LOG.info('VOTable data collected from NED for {0}'.format(name))
        return True, float(ra_eqj2000), float(dec_eqj2000)
    except Exception:
        pass

    # Try Hyperleda
    try:
        url = 'http://leda.univ-lyon1.fr/G.cgi?n=113&c=o&o=' + name + '&a=x&z=d'
        table = getVOTable(url, 0)
        ra_eqj2000 = table.array['alpha'][0]
        dec_eqj2000 = table.array['delta'][0]
        LOG.info('VOTable data collected from Hyperleda for {0}'.format(name))
        return True, float(ra_eqj2000), float(dec_eqj2000)
    except Exception:
        LOG.exception('ERROR: Getting VO data for {0}'.format(name))
        return False, 0.0, 0.0


for galaxy in connection.execute(select([GALAXY]).where(or_(GALAXY.c.ra_cent == None,  GALAXY.c.ra_cent == 0.0, GALAXY.c.dec_cent == None, GALAXY.c.dec_cent == 0.0))):
    LOG.info('Processing %d - %s', galaxy[GALAXY.c.galaxy_id], galaxy[GALAXY.c.name])
    name = fix_name(galaxy[GALAXY.c.name])

    (found, ra, dec) = get_ra_dec(name)
    if found:
        LOG.info('Updating {0} to RA: {1}, DEC: {2}'.format(name, ra, dec))
        #connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == galaxy[GALAXY.c.galaxy_id]).values(ra_cent=ra, dec_cent=dec))
