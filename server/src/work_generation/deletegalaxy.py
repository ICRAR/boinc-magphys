#! /usr/bin/env python2.7
"""
Delete a galaxy and all it's related data.
"""
from __future__ import print_function
import argparse
import logging
import sys
from sqlalchemy.sql.expression import func
from config import db_login
from database.database_support import Galaxy, PixelFilter, PixelParameter, PixelHistogram, AreaUser, FitsHeader, Area
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

    values = session.query(func.max(Area.area_id),func.min(Area.area_id)).filter(galaxy_id=galaxy.galaxy_id).first()
    LOG.info('Areas range {0}'.format(values))

    for area in galaxy.areas:
        for pxresult in area.pixelResults:
            print("Deleting area {0} pixel {1}".format(area.area_id, pxresult.pxresult_id), end="\r")
            sys.stdout.flush()

            session.query(PixelFilter).filter_by(pxresult_id=pxresult.pxresult_id).delete()
            session.query(PixelParameter).filter_by(pxresult_id=pxresult.pxresult_id).delete()
            session.query(PixelHistogram).filter_by(pxresult_id=pxresult.pxresult_id).delete()

            session.delete(pxresult)

        session.query(AreaUser).filter_by(area_id=area.area_id).delete()
        session.delete(area)

        session.commit()

    session.query(FitsHeader).filter_by(galaxy_id=galaxy.galaxy_id).delete()
    session.delete(galaxy)
    LOG.info('Galaxy with galaxy_id of %d was deleted', GALAXY_ID)

session.commit()
session.close()
