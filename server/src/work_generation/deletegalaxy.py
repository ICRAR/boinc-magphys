import argparse
import logging
from config import db_login
from database.database_support import Galaxy, Area, AreaUser, PixelResult, PixelFilter, PixelParameter, PixelHistogram
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
if galaxy == None:
    print 'Error: Galaxy with galaxy_id of', GALAXY_ID, 'was not found'
else:
    for area in galaxy.areas:
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
    session.delete(galaxy)
    print 'Galaxy with galaxy_id of', GALAXY_ID, 'was deleted'
        
        
session.commit()
session.close()