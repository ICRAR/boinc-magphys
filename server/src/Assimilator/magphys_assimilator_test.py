#! /usr/bin/env python

import os, re, signal, sys, time, hashlib
import boinc_path_config
from Boinc import database, boinc_db, boinc_project_path, configxml, sched_messages
from xml.dom.minidom import parseString
import magphys_assimilator

class DUMMY_RESULT:
    userid = 0

class MagphysAssimilatorTest(magphys_assimilator.MagphysAssimilator):
    
    def __init__(self):
        magphys_assimilator.MagphysAssimilator.__init__(self)
    
    def test(self, sedFile, fitFile):
        session = self.Session()
        result1 = DUMMY_RESULT()
        result1.userid = 1
        result2 = DUMMY_RESULT()
        result2.userid = 2
        results = [result1,result2]
        self.processResult(session, sedFile, fitFile, results)
        session.commit()
    
if __name__ == '__main__':
    asm = MagphysAssimilatorTest()
    asm.test("/Users/rob/magphys/pix0.sed", "/Users/rob/magphys/pix0.fit")