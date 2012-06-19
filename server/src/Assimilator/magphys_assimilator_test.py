#! /usr/bin/env python

import os, re, signal, sys, time, hashlib
import boinc_path_config
from Boinc import database, boinc_db, boinc_project_path, configxml, sched_messages
from xml.dom.minidom import parseString
import magphys_assimilator

class DummyWorkUnit:
    canonical_resultid = 1
    xml_doc_in = ""
    
class DummyResult:
    userid = 0

class MagphysAssimilatorTest(magphys_assimilator.MagphysAssimilator):
    
    def __init__(self):
        magphys_assimilator.MagphysAssimilator.__init__(self)
    
    def test(self, outFile):
        str_list = []
        str_list.append("<?xml version=\"1.0\" ?>\n")
        str_list.append("<output>\n")
        str_list.append("  <file_name>")
        str_list.append(outFile)
        str_list.append("</file_name>\n")
        str_list.append("</output>")
        #print ''.join(str_list)
        
        result1 = DummyResult()
        result1.userid = 1
        result2 = DummyResult()
        result2.userid = 2
        results = [result1,result2]
        
        canonical_result = DummyResult()
        canonical_result.xml_doc_in = ''.join(str_list)
        
        wu = DummyWorkUnit()
        self.assimilate_handler(wu, results, canonical_result)
        
        #session = self.Session()
        #self.processResult(session, sedFile, fitFile, results)
        #session.commit()
    
if __name__ == '__main__':
    asm = MagphysAssimilatorTest()
    asm.test("/Users/rob/magphys/output.fit")