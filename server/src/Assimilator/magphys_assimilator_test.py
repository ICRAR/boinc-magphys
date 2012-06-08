#! /usr/bin/env python

import os, re, signal, sys, time, hashlib
import boinc_path_config
from Boinc import database, boinc_db, boinc_project_path, configxml, sched_messages
from xml.dom.minidom import parseString
import magphys_assimilator

class MagphysAssimilatorTest(magphys_assimilator.MagphysAssimilator):
    
    def __init__(self):
        magphys_assimilator.MagphysAssimilator.__init__(self)
    
    def test(self, sedFile, fitFile):
        self.processFiles(sedFile, fitFile)
    
if __name__ == '__main__':
    asm = MagphysAssimilatorTest()
    asm.test("/Users/rob/magphys/pix0.sed", "/Users/rob/magphys/pix0.fit")