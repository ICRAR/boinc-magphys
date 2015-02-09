#! /usr/bin/env python2.7
#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
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
__author__ = 'ict310'

from sqlalchemy import create_engine
from database.database_support_core import AREA
from config import DB_LOGIN
import time
import datetime
import random

random.seed()
ENGINE = create_engine(DB_LOGIN)


def old():
    connection = ENGINE.connect()
    db_time = []
    i = 0
    while i < 300:
        start = time.time()
        transaction = connection.begin()
        area = random.randrange(5, 60, 1)
        wu_id = random.randrange(5, 60, 1)
        connection.execute(AREA.update()
                           .where(AREA.c.area_id == area)
                           .values(workunit_id=wu_id, update_time=datetime.datetime.now()))

        area = random.randrange(5, 60, 1)
        wu_id = random.randrange(5, 60, 1)
        connection.execute(AREA.update()
                           .where(AREA.c.area_id == area)
                           .values(workunit_id=wu_id, update_time=datetime.datetime.now()))

        sleepytime = random.randrange(0.8, 1.4, 0.1)
        time.sleep(sleepytime)

        area = random.randrange(5, 60, 1)
        wu_id = random.randrange(5, 60, 1)
        connection.execute(AREA.update()
                            .where(AREA.c.area_id == area)
                            .values(workunit_id=wu_id, update_time=datetime.datetime.now()))
        transaction.commit()
        print 'Time in DB {0}'.format(time.time() - start)
        db_time.append(time.time() - start)
        i += 1

    total = 0
    for dbtime in db_time:
        total += dbtime

    ave = total/len(db_time)
    print 'Total time: {0}'.format(total)
    print 'Ave per transaction: {0}'.format(ave)


def new():
    connection = ENGINE.connect()
    db_time = []
    i = 0

    while i < 300:
        db_queue = []
        area = random.randrange(5, 60, 1)
        wu_id = random.randrange(5, 60, 1)
        db_queue.append(AREA.update()
                           .where(AREA.c.area_id == area)
                           .values(workunit_id=wu_id, update_time=datetime.datetime.now()))

        area = random.randrange(5, 60, 1)
        wu_id = random.randrange(5, 60, 1)
        db_queue.append(AREA.update()
                           .where(AREA.c.area_id == area)
                           .values(workunit_id=wu_id, update_time=datetime.datetime.now()))

        sleepytime = random.randrange(0.8, 1.4, 0.1)
        time.sleep(sleepytime)

        area = random.randrange(5, 60, 1)
        wu_id = random.randrange(5, 60, 1)
        db_queue.append(AREA.update()
                           .where(AREA.c.area_id == area)
                           .values(workunit_id=wu_id, update_time=datetime.datetime.now()))

        start = time.time()
        transaction = connection.begin()
        for item in db_queue:
            connection.execute(item)
        transaction.commit()

        i += 1
        print 'Time in DB {0}'.format(time.time() - start)

    total = 0
    for dbtime in db_time:
        total += dbtime

    ave = total/len(db_time)
    print 'Total time: {0}'.format(total)
    print 'Ave per transaction: {0}'.format(ave)