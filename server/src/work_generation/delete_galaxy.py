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
from database.database_support import Galaxy, PixelFilter, PixelParameter, PixelHistogram, AreaUser, FitsHeader, Area, PixelResult, ParameterAggregate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Delete Galaxy by galaxy_id')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id or 4-30 if you need a range')
args = vars(parser.parse_args())

# First check the galaxy exists in the database
engine = create_engine(db_login)
Session = sessionmaker(bind=engine)
session = Session()

galaxy_ids = None
if len(args['galaxy_id']) == 1 and args['galaxy_id'][0].find('-') > 1:
    list = args['galaxy_id'][0].split('-')
    LOG.info('Range from %s to %s', list[0], list[1])
    galaxy_ids = range(int(list[0]), int(list[1]) + 1)
else:
    galaxy_ids = args['galaxy_id']

for galaxy_id_str in galaxy_ids:
    galaxy_id1 = int(galaxy_id_str)
    galaxy = session.query(Galaxy).filter_by(galaxy_id=galaxy_id1).first()
    if galaxy is None:
        LOG.info('Error: Galaxy with galaxy_id of %d was not found', galaxy_id1)
    else:
        LOG.info('Deleting Galaxy with galaxy_id of %d - %s', galaxy_id1, galaxy.name)

        values = session.query(func.min(Area.area_id),func.max(Area.area_id)).filter_by(galaxy_id=galaxy.galaxy_id).first()
        LOG.info('Areas range {0}'.format(values))

        for area_id1 in session.query(Area.area_id).filter_by(galaxy_id=galaxy.galaxy_id).order_by(Area.area_id).all():
            for pxresult_id1 in session.query(PixelResult.pxresult_id).filter_by(area_id=area_id1[0]).order_by(PixelResult.pxresult_id).all():
                print("Deleting galaxy {0} area {1} pixel {2}".format(galaxy_id_str, area_id1[0], pxresult_id1[0]), end="\r")
                sys.stdout.flush()

                for pxparameter_id1 in session(PixelParameter.pxparameter_id).filter_by(pxresult_id=pxresult_id1[0]).all():
                    session.query(ParameterAggregate).filter_by(pxparameter_id=pxparameter_id1[0]).delete()

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
