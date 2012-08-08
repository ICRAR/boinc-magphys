#! /usr/bin/env python2.7

import assimilator
import boinc_path_config
import gzip, os
from Boinc import database, boinc_db, boinc_project_path, configxml, sched_messages
from xml.dom.minidom import parseString
from assimilator_utils import is_gzip
from config import db_login
from database.database_support import AreaUser, PixelResult, PixelFilter, PixelParameter, PixelHistogram

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class MagphysAssimilator(assimilator.Assimilator):
    area = None

    def __init__(self):
        assimilator.Assimilator.__init__(self)

        # Login is set in the database package
        engine = create_engine(db_login)
        self.Session = sessionmaker(bind=engine)

    def get_output_file_infos(self, result, list):
        dom = parseString(result.xml_doc_in)
        for node in dom.getElementsByTagName('file_name'):
            list.append(node.firstChild.nodeValue)

    def getResult(self, session, pxresultId):
        if self.noinsert:
            pxresult = None
        else:
            pxresult = session.query(PixelResult).filter("pxresult_id=:pxresultId").params(pxresultId=pxresultId).first()
        #doAdd = False
        if pxresult is None:
            print "Pixel Result row not found for pxresultId of", pxresultId
            return None
            #pxresult = PixelResult()
        else:
            for filter in pxresult.filters:
                session.delete(filter)
            for parameter in pxresult.parameters:
                for histogram in parameter.histograms:
                    session.delete(histogram)
                session.delete(parameter)
        self.area = pxresult.area
        pxresult.filters = []
        pxresult.parameters = []
        return pxresult

    def saveResult(self, session, pxresult):
        if pxresult.pxresult_id is None and not self.noinsert:
            session.add(pxresult)

    def processResult(self, session, outFile, wu):
        """
        Read the output file, add the values to the PixelResult row, and insert the filter,
        parameter and histogram rows.
        """
        if is_gzip(outFile):
            self.logDebug('Is GZIP\n')
            f = gzip.open(outFile , "rb")
        else:
            self.logDebug('Is not GZIP\n')
            f = open(outFile, "r")
        lineNo = 0
        pxresult = None
        parameter = None
        percentilesNext = False
        histogramNext = False
        skynetNext = False
        resultCount = 0
        try:
            for line in f:
                lineNo += 1

                if line.startswith(" ####### "):
                    if pxresult:
                        self.saveResult(session, pxresult)
                    values = line.split()
                    pointName = values[1]
                    #print "pointName", pointName
                    pxresultId = pointName[3:].rstrip()
                    #print "pxresultId", pxresultId
                    pxresult = self.getResult(session, pxresultId)
                    if pxresult:
                      pxresult.workunit_id = wu.id
                    lineNo = 0
                    percentilesNext = False
                    histogramNext = False
                    skynetNext = False
                    resultCount += 1
                elif pxresult:
                    if lineNo == 2:
                        filterNames = line.split()
                        for filterName in filterNames:
                            if filterName != '#':
                                filter = PixelFilter()
                                filter.filter_name = filterName
                                pxresult.filters.append(filter)
                    elif lineNo == 3:
                        idx = 0
                        values = line.split()
                        for value in values:
                            filter = pxresult.filters[idx]
                            filter.observed_flux = float(value)
                            idx += 1
                    elif lineNo == 4:
                        idx = 0
                        values = line.split()
                        for value in values:
                            filter = pxresult.filters[idx]
                            filter.observational_uncertainty = float(value)
                            idx += 1
                    elif lineNo == 9:
                        values = line.split()
                        pxresult.i_sfh = float(values[0])
                        pxresult.i_ir = float(values[1])
                        pxresult.chi2 = float(values[2])
                        pxresult.redshift = float(values[3])
                        #for value in values:
                        #    print value
                    elif lineNo == 11:
                        values = line.split()
                        pxresult.fmu_sfh = float(values[0])
                        pxresult.fmu_ir = float(values[1])
                        pxresult.mu = float(values[2])
                        pxresult.tauv = float(values[3])
                        pxresult.s_sfr = float(values[4])
                        pxresult.m = float(values[5])
                        pxresult.ldust = float(values[6])
                        pxresult.t_w_bc = float(values[7])
                        pxresult.t_c_ism = float(values[8])
                        pxresult.xi_c_tot = float(values[9])
                        pxresult.xi_pah_tot = float(values[10])
                        pxresult.xi_mir_tot = float(values[11])
                        pxresult.x_w_tot = float(values[12])
                        pxresult.tvism = float(values[13])
                        pxresult.mdust = float(values[14])
                        pxresult.sfr = float(values[15])
                    elif lineNo == 13:
                        idx = 0
                        values = line.split()
                        for value in values:
                            filter = pxresult.filters[idx]
                            filter.flux_bfm = float(value)
                            idx += 1
                    elif lineNo > 13:
                        if line.startswith("# ..."):
                            parts = line.split('...')
                            parameterName = parts[1].strip()
                            parameter = PixelParameter()
                            parameter.parameter_name = parameterName
                            pxresult.parameters.append(parameter)
                            percentilesNext = False
                            histogramNext = True
                            skynetNext = False
                        elif line.startswith("#....percentiles of the PDF......") and parameter is not None:
                            percentilesNext = True
                            histogramNext = False
                            skynetNext = False
                        elif line.startswith(" #...theSkyNet"):
                            percentilesNext = False
                            histogramNext = False
                            skynetNext = True
                        elif percentilesNext:
                            values = line.split()
                            parameter.percentile2_5 = float(values[0])
                            parameter.percentile16 = float(values[1])
                            parameter.percentile50 = float(values[2])
                            parameter.percentile84 = float(values[3])
                            parameter.percentile97_5 = float(values[4])
                            percentilesNext = False
                        elif histogramNext:
                            hist = PixelHistogram()
                            hist.pxresult_id = pxresult.pxresult_id
                            values = line.split()
                            hist.x_axis = float(values[0])
                            hist.hist_value = float(values[1])
                            parameter.histograms.append(hist)
                        elif skynetNext:
                            values = line.split()
                            pxresult.i_opt = float(values[0])
                            pxresult.i_ir = float(values[1])
                            pxresult.dmstar = float(values[2])
                            pxresult.dfmu_aux = float(values[3])
                            pxresult.dz = float(values[4])
                            skynetNext = False
        except IOError:
            self.logCritical('IOError after %d lines', lineNo)
        finally:
            f.close()
        if pxresult:
            self.saveResult(session, pxresult)
        return resultCount

    def assimilate_handler(self, wu, results, canonical_result):
        """
        Process the Results.
        """
        self.logDebug("Start of assimilate_handler for %d\n", wu.id)
        #self.logDebug("url: [%s]\n", login)
        if wu.canonical_result:
            #file_list = []
            outFile = self.get_file_path(canonical_result)
            self.area = None
            #self.get_output_file_infos(canonical_result, file_list)
            if outFile:
                 if os.path.isfile(outFile):
                      pass
                 else:
                     self.logDebug("File [%s] not found\n", outFile)
                     outFile = None

            if outFile:
                self.logDebug("Reading File [%s]\n", outFile)
                session = self.Session()
                resultCount = self.processResult(session, outFile, wu)
                if self.noinsert:
                    session.rollback()
                else:
                    if resultCount == 0:
                        self.logCritical("No results were found in the output file\n")
                    if self.area is None:
                        self.logDebug("The Area was not found\n")
                    else:
                        self.area.workunit_id = wu.id
                        useridSet = set()
                        for result in results:
                            #if result.user:
                            #    self.logDebug("Result: %d Userid: %d State: %d\n", result.id, result.user.id, result.validate_state)
                            if result.user and result.validate_state == boinc_db.VALIDATE_STATE_VALID:
                                userid = result.user.id
                                #self.logDebug("Userid %d\n", userid)
                                if userid not in useridSet:
                                    #self.logDebug("Added Userid %d\n", userid)
                                    useridSet.add(userid)
                        #print 'Adding users'
                        for user in self.area.users:
                            session.delete(user)
                        for userid in useridSet:
                            usr = AreaUser()
                            usr.userid = userid
                            #usr.create_time =
                            self.area.users.append(usr)
                    self.logDebug("Saving %d results for workunit %d\n", resultCount, wu.id)
                    session.commit()
            else:
                self.logCritical("The output file was not found\n")
        else:
            self.logDebug("No canonical_result for workunit\n")
            self.report_errors(wu)

        return 0

if __name__ == '__main__':
    asm = MagphysAssimilator()
    asm.run()
