#! /usr/bin/env python2.7
"""
During the Beta testing we stored all the Pixel Parameter values - this script removes the really small values
"""
from __future__ import print_function
import logging
from operator import and_
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from config import DB_LOGIN, MIN_HIST_VALUE
from database.database_support import Galaxy, PixelResult, PixelParameter, PixelHistogram

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

engine = create_engine(DB_LOGIN)
Session = sessionmaker(bind=engine)
session = Session()

galaxies = session.query(Galaxy).all()

deleted_total = 0
for galaxy in galaxies:
    # Have we got work units out there for this galaxy?
    LOG.info('Working on galaxy %s (%d)', galaxy.name, galaxy.version_number)

    deleted_galaxy = 0
    for pxresult_id in session.query(PixelResult.pxresult_id).filter_by(galaxy_id=galaxy.galaxy_id).order_by(PixelResult.pxresult_id).all():
        print("Deleting low pixel_histogram values from galaxy {0} pixel {1} : Deleted total {2} galaxy {3}".format(galaxy.galaxy_id, pxresult_id[0], deleted_total, deleted_galaxy), end="\r")
        deleted = session.query(PixelHistogram).filter(and_(PixelHistogram.pxresult_id == pxresult_id[0], PixelHistogram.hist_value < MIN_HIST_VALUE)).delete()
        deleted_total += deleted
        deleted_galaxy += deleted
        session.commit()

    LOG.info('\nRemoved %d really small histogram values from %s (%d)', deleted_galaxy, galaxy.name, galaxy.version_number)
session.close()
LOG.info('Done.')
