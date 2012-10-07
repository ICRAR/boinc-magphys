#! /usr/bin/env python2.7
"""
During the Beta testing we stored all the Pixel Parameter values - this script removes the really small values
"""
import argparse
import logging
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
import time
from config import DB_LOGIN, MIN_HIST_VALUE
from database.database_support import Galaxy, Area

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Delete Galaxy by galaxy_id')
parser.add_argument('galaxy_id', nargs='+', help='the galaxy_id or 4-30 if you need a range')
args = vars(parser.parse_args())

engine = create_engine(DB_LOGIN)
Session = sessionmaker(bind=engine)
session = Session()

galaxy_ids = None
deleted_total = 0
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
        # Have we got work units out there for this galaxy?
        LOG.info('Working on galaxy %s (%d)', galaxy.name, galaxy.version_number)

        deleted_galaxy = 0
        for area_id in session.query(Area.area_id).filter_by(galaxy_id=galaxy.galaxy_id).order_by(Area.area_id).all():
            LOG.info('Deleting low pixel_histogram values from galaxy {0} area {1} : Deleted total {2} galaxy {3}'.format(galaxy.galaxy_id, area_id[0], deleted_total, deleted_galaxy))
            # Sqlalchemy doesn't support joins when deleting so use the raw SQL as it is MUCH faster
            result_proxy = engine.execute('''delete a from pixel_histogram a, pixel_result b
where a.pxresult_id = b.pxresult_id
and a.hist_value < {0}
and b.area_id = {1}'''.format(MIN_HIST_VALUE, area_id[0]))
            deleted_total += result_proxy.rowcount
            deleted_galaxy += result_proxy.rowcount
            session.commit()

            # Give the rest of the world a chance to access the database
            time.sleep(1)

        print('')
        LOG.info('Removed %d really small histogram values from %s (%d)', deleted_galaxy, galaxy.name, galaxy.version_number)

LOG.info('Done - removed %d really small histogram values.', deleted_total)
