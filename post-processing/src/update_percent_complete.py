#! /usr/bin/env python2.7
"""
During the beta testing we had some pixels that would not converge onto a probability bin properly.

The fix was to just let them through, but the assimilator won't be processing the pixels properly.
So this files looks for area's that haven't had the workunit_id assigned. Then it looks at the workunits in
BOINC to see if has been assimilated
"""

# First check the galaxy exists in the database
import logging
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from config import db_login, boinc_db_login
from database.boinc_database_support import Workunit
from database.database_support import Galaxy, Area

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

engine_magphys = create_engine(db_login)
Session = sessionmaker(bind=engine_magphys)
session_magphys = Session()

engine_pogs = create_engine(boinc_db_login)
Session = sessionmaker(bind=engine_pogs)
session_pogs = Session()

galaxies = session_magphys.query(Galaxy).all()

for galaxy in galaxies:
    LOG.info('Working on galaxy %s (%d)', galaxy.name, galaxy.version_number)

    areas = session_magphys.query(Area).filter_by(galaxy_id=galaxy.galaxy_id).filter_by(workunit_id = None).all()

    for area in areas:
        wu_name = '{0}_area{1}'.format(galaxy.name, area.area_id)
        workunits = session_pogs.query(Workunit).filter_by(name=wu_name).all()

        for workunit in workunits:
            if workunit.assimilate_state == 2:
                LOG.info('%d Found area %d - WU_id %d', galaxy.name, area.area_id, workunit.id)
                area.workunit_id = workunit.id

                for pixel in area.pixelResults:
                    pixel.workunit_id = workunit.id

    session_magphys.commit()

LOG.info('Done.')
