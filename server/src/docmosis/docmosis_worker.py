#! /usr/bin/env python2.7
#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012
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
Docmosis Worker Process - process jobs in docmosis_task table.
"""
import os
import sys
import logging
import uuid

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../../server/src')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../boinc/py')))
#LOG.info('PYTHONPATH = {0}'.format(sys.path))

import docmosis
from datetime import datetime
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select, update
from config import DB_LOGIN
from database.database_support_core import DOCMOSIS_TASK

ENGINE = create_engine(DB_LOGIN)

class TaskInfo():
    def __init__(self):
        self.taskid = ""
        self.userid = ""
        self.galaxies = []

def main():
    """
    This is where we'll usually start
    """

    # Generate unique token for this worker instance
    token = uuid.uuid4().hex
    assignTasks(token)
    LOG.info("Worker started with token id %s" % token)
    tasks = getTasks(token)
    LOG.info("Got %d tasks to process" % len(tasks))
    runTasks(tasks)
    LOG.info("Worker finished")

def runTasks(tasks):

    connection = ENGINE.connect()
    for task in tasks:
        docmosis.emailGalaxyReport(task.userid,task.galaxies)
        query = DOCMOSIS_TASK.update()
        query = query.where(DOCMOSIS_TASK.c.taskid == task.taskid)
        query = query.values(finish_time = datetime.now(), result = 1)
        connection.execute(query)
    connection.close()


def assignTasks(token):

    connection = ENGINE.connect()
    connection.execute(DOCMOSIS_TASK.update().where(DOCMOSIS_TASK.c.worker_token == None).values(worker_token = token))
    connection.close()

def getTasks(token):

    connection = ENGINE.connect()
    tasks = connection.execute(select([DOCMOSIS_TASK]).where(DOCMOSIS_TASK.c.worker_token == token))
    task_list = []
    for task in tasks:
        task_line = TaskInfo()
        task_line.taskid = task.taskid
        task_line.userid = task.userid
        task_line.galaxies = (task.galaxies).split(',')
        task_list.append(task_line)

    return task_list

if __name__ == '__main__':
    main()

