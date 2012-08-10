#! /usr/bin/env python2.7

import os, re, sys
import boinc_path_config
from Boinc import database, boinc_db, boinc_project_path, configxml, sched_messages, db_base

from config import db_login
from database.database_support import Area, AreaUser
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

"""
Job to assign any credits in the "credited_job" table to the "area_user" table if not present,
and to remove the rows from "credited_job" table once they have been assigned to the area.
"""
class AssignCredit:
    def __init__(self):
        # Login is set in the database package
        engine = create_engine(db_login)
        self.Session = sessionmaker(bind=engine)
        
    def parse_args(self, args):
        """
        Parses arguments provided on the command line and sets
        those argument values as member variables. Arguments
        are parsed as their true types, so integers will be ints, 
        not strings.
        """
        
        args.reverse()
        while(len(args)):
            arg = args.pop()
            if arg == '-app':
                arg = args.pop()
                self.appname = arg
            else:
                self.logCritical("Unrecognized arg: %s\n", arg)
    
    def run(self):
        self.parse_args(sys.argv[1:])
        self.config = configxml.default_config().config

        # retrieve app where name = app.name
        database.connect()
        app=database.Apps.find1(name=self.appname)
        
        session = self.Session()
        conn = db_base.get_dbconnection()
        
        userCount = 0
        creditCount = 0
        
        qryCursor = conn.cursor()
        delCursor = conn.cursor()
        qryCursor.execute('select userid, workunitid from credited_job ')
        results = qryCursor.fetchall()
        for result in results:
            userCount += 1
            userid = result['userid']
            areaid = result['workunitid']
            areauser = session.query(AreaUser).filter(and_(AreaUser.userid == userid, AreaUser.area_id == areaid)).first()
            if areauser == None:
                areauser = AreaUser()
                areauser.userid = userid
                areauser.area_id =  areaid
                session.add(areauser)
                session.commit()
                print 'User', userid, 'Credited for Area', areaid
                creditCount += 1
            else:
                print 'User', userid, 'already Credited for Area', areaid
            
            delCursor.execute("delete from credited_job where userid = " + str(userid) + "  and workunitid = " + str(areaid))
           
        conn.commit() 
        database.close()
        session.close()
        print userCount, 'Users', creditCount, 'Credited'

if __name__ == '__main__':
    assign = AssignCredit()
    assign.run()
