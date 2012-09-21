#! /usr/bin/env python2.7
"""
Delete a galaxy and all it's related data.
"""
from __future__ import print_function
import argparse
import logging
import sys
from config import db_login
from database.database_support import Galaxy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Delete Galaxy by galaxy_id')
parser.add_argument('galaxy_id', nargs=1, help='the galaxy_id')
args = vars(parser.parse_args())

GALAXY_ID = int(args['galaxy_id'][0])

# First check the galaxy exists in the database
engine = create_engine(db_login)
Session = sessionmaker(bind=engine)
session = Session()

galaxy = session.query(Galaxy).filter("galaxy_id=:galaxy_id").params(galaxy_id=GALAXY_ID).first()
if galaxy is None:
    LOG.info('Error: Galaxy with galaxy_id of %d was not found', GALAXY_ID)
else:
    LOG.info('Deleting Galaxy with galaxy_id of %d', GALAXY_ID)

    for area in galaxy.areas:
        print("Deleting area {0}".format(area.area_id), end="\r")
        sys.stdout.flush()
        for pxresult in area.pixelResults:
            for filter in pxresult.filters:
                session.delete(filter)
            for parameter in pxresult.parameters:
                for histogram in parameter.histograms:
                    session.delete(histogram)
                session.delete(parameter)
            session.delete(pxresult)
        for user in area.users:
            session.delete(user)
        session.delete(area)
    for hdr in galaxy.fits_headers:
        session.delete(hdr)
    session.delete(galaxy)
    LOG.info('Galaxy with galaxy_id of %d was deleted', GALAXY_ID)

session.commit()
session.close()
