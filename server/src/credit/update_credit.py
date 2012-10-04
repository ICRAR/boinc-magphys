#! /usr/bin/env python2.7
"""
Job to recalculate the number of pixels processed by each user.
"""

from config import DB_LOGIN
from sqlalchemy import create_engine

engine = create_engine(DB_LOGIN)
connection = engine.connect()
trans = connection.begin()
try:
    result = connection.execute("delete from user_pixel")
    print 'Deleted', result.rowcount, 'rows.'
    result = connection.execute("""
insert into user_pixel
select area_user.userid, count(*)
from     area, area_user, pixel_result pxresult
where area.area_id = area_user.area_id
and    pxresult.area_id = area.area_id
group by area_user.userid
""")
    print 'Inserted', result.rowcount, 'rows.'
    trans.commit()
except:
    trans.rollback()
    raise

connection.close()
