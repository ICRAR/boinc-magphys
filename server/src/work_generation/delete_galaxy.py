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
from database.database_support import Galaxy, PixelFilter, PixelParameter, PixelHistogram, AreaUser, FitsHeader, Area, PixelResult
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Delete Galaxy by galaxy_id')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id')
args = vars(parser.parse_args())

# First check the galaxy exists in the database
engine = create_engine(db_login)
Session = sessionmaker(bind=engine)
session = Session()

for galaxy_id_str in args['galaxy_id']:
    galaxy_id1 = int(galaxy_id_str)
    galaxy = session.query(Galaxy).filter_by(galaxy_id=galaxy_id1).first()
    if galaxy is None:
        LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
    else:
        LOG.info('Deleting Galaxy with galaxy_id of %d', galaxy_id1)

        values = session.query(func.min(Area.area_id),func.max(Area.area_id)).filter_by(galaxy_id=galaxy.galaxy_id).first()
        LOG.info('Areas range {0}'.format(values))

        for area_id1 in session.query(Area.area_id).filter_by(galaxy_id=galaxy.galaxy_id).order_by(Area.area_id).all():
            for pxresult_id1 in session.query(PixelResult.pxresult_id).filter_by(area_id=area_id1[0]).order_by(PixelResult.pxresult_id).all():
                print("Deleting galaxy {0} area {1} pixel {2}".format(galaxy_id_str, area_id1[0], pxresult_id1[0]), end="\r")
                sys.stdout.flush()

                session.query(PixelFilter).filter_by(pxresult_id=pxresult_id1[0]).delete()
                session.query(PixelParameter).filter_by(pxresult_id=pxresult_id1[0]).delete()
                session.query(PixelHistogram).filter_by(pxresult_id=pxresult_id1[0]).delete()

            session.query(PixelResult).filter_by(area_id=area_id1[0]).delete()
            session.query(AreaUser).filter_by(area_id=area_id1[0]).delete()

            session.commit()

        session.query(Area).filter_by(galaxy_id=galaxy.galaxy_id).delete()
        session.query(FitsHeader).filter_by(galaxy_id=galaxy.galaxy_id).delete()
        session.delete(galaxy)
        LOG.info('Galaxy with galaxy_id of %d was deleted', galaxy_id1)
    session.commit()

session.commit()
session.close()
