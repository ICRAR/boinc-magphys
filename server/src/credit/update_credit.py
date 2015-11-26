#! /usr/bin/env python2.7
#
#    Copyright (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
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
Job to recalculate the number of pixels processed by each user.
"""

import os
import sys

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))

from utils.logging_helper import config_logger
from config import DB_LOGIN
from sqlalchemy import create_engine, select, func
from database.database_support_core import USER_PIXEL, AREA_USER, AREA, PIXEL_RESULT

LOG = config_logger(__name__)
COMMIT_THRESHOLD = 100

LOG.info('PYTHONPATH = {0}'.format(sys.path))

engine = create_engine(DB_LOGIN)
connection = engine.connect()

trans = connection.begin()
try:
    result = connection.execute(USER_PIXEL.delete())
    LOG.info('Deleted {0} rows.'.format(result.rowcount))
    trans.commit()
except Exception:
    trans.rollback()
    raise

# result = connection.execute(
# insert into user_pixel
# select area_user.userid, count(*)
# from     area, area_user, pixel_result pxresult
# where area.area_id = area_user.area_id
# and    pxresult.area_id = area.area_id
# group by area_user.userid)

LOG.info('This is the query I am using')
LOG.info(str(select([AREA_USER.c.userid, func.count()])
             .where(AREA.c.area_id == AREA_USER.c.area_id)
             .where(PIXEL_RESULT.c.area_id == AREA.c.area_id)
             .group_by(AREA_USER.c.userid)))
LOG.info('This\'ll probably take a while...')

result = connection.execute(select([AREA_USER.c.userid, func.count()])
                            .where(AREA.c.area_id == AREA_USER.c.area_id)
                            .where(PIXEL_RESULT.c.area_id == AREA.c.area_id)
                            .group_by(AREA_USER.c.userid))

LOG.info('Done!')
insert_queue = []
rowcount = 0
LOG.info('Now inserting...')
try:
    for row in result:
        rowcount += 1
        if len(insert_queue) > COMMIT_THRESHOLD:

            trans = connection.begin()
            for item in insert_queue:
                connection.execute(item)
            insert_queue = []
            trans.commit()

        else:
            insert_queue.append(USER_PIXEL.insert().values(userid=row[0], pixel_count=row[1]))

    # Process any remaining db tasks
    if len(insert_queue) > 0:

        trans = connection.begin()
        for item in insert_queue:
            connection.execute(item)
        trans.commit()

except Exception:
    trans.rollback()
    raise

LOG.info('Inserted {0} rows.'.format(rowcount))

connection.close()
