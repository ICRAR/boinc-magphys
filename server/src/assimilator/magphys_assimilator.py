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
The Assimilator for the MagPhys code
"""
import time
import assimilator
import boinc_path_config
import math
import gzip, os, sys, traceback, datetime
from Boinc import database, boinc_db, boinc_project_path, configxml, sched_messages
from xml.dom.minidom import parseString
from assimilator_utils import is_gzip
from config import DB_LOGIN, MIN_HIST_VALUE
from database.database_support import AreaUser, PixelResult, PixelFilter, PixelParameter, PixelHistogram, ParameterName

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class MagphysAssimilator(assimilator.Assimilator):
    area = None
    error_wu_id = None

    def __init__(self):
        assimilator.Assimilator.__init__(self)

        # Login is set in the database package
        engine = create_engine(DB_LOGIN)
        self.Session = sessionmaker(bind=engine)
        self.map_parameter_name = {}

        # Load the parameter name map
        session = self.Session()
        for parameter_name in session.query(ParameterName).all():
            self.map_parameter_name[parameter_name.name] = parameter_name.parameter_name_id
        session.close()
        self.logNormal('')

    def get_output_file_infos(self, result, list):
        """
        Get the file names
        """
        dom = parseString(result.xml_doc_in)
        for node in dom.getElementsByTagName('file_name'):
            list.append(node.firstChild.nodeValue)

    def getResult(self, session, pxresultId):
        """
        Get the pixel result row from the database
        """
        if self.noinsert:
            pxresult = None
        else:
            pxresult = session.query(PixelResult).filter("pxresult_id=:pxresultId").params(pxresultId=pxresultId).first()

        if pxresult is None:
            self.logCritical("Pixel Result row not found for pxresultId of %s\n", pxresultId)
            return None
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
        """
        Add the pixel to the database
        """
        if pxresult.pxresult_id is None and not self.noinsert:
            session.add(pxresult)

    def processResult(self, session, outFile, wu):
        """
        Read the output file, add the values to the PixelResult row, and insert the filter,
        parameter and histogram rows.
        """
        if is_gzip(outFile):
            f = gzip.open(outFile , "rb")
        else:
            f = open(outFile, "r")

        lineNo = 0
        pxresult = None
        parameter = None
        percentiles_next = False
        histogram_next = False
        skynet_next1 = False
        skynet_next2 = False
        result_count = 0
        histogram_count1 = 0
        histogram_count2 = 0
        try:
            for line in f:
                lineNo += 1

                if line.startswith(" ####### "):
                    if pxresult:
                        self.saveResult(session, pxresult)
                        self.logDebug('%.3f seconds for %d - %d : %d histogram entries\n', time.time() - start_time, pxresult.pxresult_id, histogram_count1, histogram_count2)
                    start_time = time.time()
                    values = line.split()
                    pointName = values[1]
                    pxresultId = pointName[3:].rstrip()
                    pxresult = self.getResult(session, pxresultId)
                    if pxresult:
                      pxresult.workunit_id = wu.id
                    lineNo = 0
                    percentiles_next = False
                    histogram_next = False
                    skynet_next1 = False
                    skynet_next2 = False
                    result_count += 1
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
                            parameter.parameter_name_id = self.map_parameter_name[parameterName]
                            pxresult.parameters.append(parameter)
                            percentiles_next = False
                            histogram_next = True
                            skynet_next1 = False
                            skynet_next2 = False
                        elif line.startswith("#....percentiles of the PDF......") and parameter is not None:
                            percentiles_next = True
                            histogram_next = False
                            skynet_next1 = False
                            skynet_next2 = False
                        elif line.startswith(" #...theSkyNet"):
                            percentiles_next = False
                            histogram_next = False
                            skynet_next1 = True
                            skynet_next2 = False
                        elif line.startswith("# theSkyNet2"):
                            percentiles_next = False
                            histogram_next = False
                            skynet_next1 = False
                            skynet_next2 = True
                        elif percentiles_next:
                            values = line.split()
                            parameter.percentile2_5 = float(values[0])
                            parameter.percentile16 = float(values[1])
                            parameter.percentile50 = float(values[2])
                            parameter.percentile84 = float(values[3])
                            parameter.percentile97_5 = float(values[4])
                            percentiles_next = False
                        elif histogram_next:
                            histogram_count1 += 1
                            values = line.split()
                            hist_value = float(values[1])
                            if hist_value > MIN_HIST_VALUE and not math.isnan(hist_value):
                                histogram_count1 += 2
                                hist = PixelHistogram()
                                hist.pxresult_id = pxresult.pxresult_id
                                hist.x_axis = float(values[0])
                                hist.hist_value = hist_value
                                parameter.histograms.append(hist)
                        elif skynet_next1:
                            values = line.split()
                            pxresult.i_opt = float(values[0])
                            pxresult.i_ir = float(values[1])
                            pxresult.dmstar = float(values[2])
                            pxresult.dfmu_aux = float(values[3])
                            pxresult.dz = float(values[4])
                            skynet_next1 = False
                        elif skynet_next2:
                            # We have the highest bin probability values which require the parameter_id
                            values = line.split()
                            parameter.high_prob_bin = float(values[0])
                            parameter.first_prob_bin = float(values[1])
                            parameter.last_prob_bin = float(values[2])
                            parameter.bin_step = float(values[3])
                            skynet_next2 = False

        except IOError:
            self.logCritical('IOError after %d lines\n', lineNo)
        finally:
            f.close()
        if pxresult:
            self.saveResult(session, pxresult)
        return result_count

    def assimilate_handler(self, wu, results, canonical_result):
        """
        Process the Results.
        """
        self.logDebug("Start of assimilate_handler for wu %d\n", wu.id)
        try:
            if wu.canonical_result:
                outFile = self.get_file_path(canonical_result)
                self.area = None
                if outFile:
                     if os.path.isfile(outFile):
                          pass
                     else:
                         self.logDebug("File [%s] not found\n", outFile)
                         outFile = None

                if outFile:
                    self.logDebug("Reading File [%s]\n", outFile)
                    start = time.time()
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
                            self.area.update_time = datetime.datetime.now()
                            useridSet = set()
                            for result in results:
                                if result.user and result.validate_state == boinc_db.VALIDATE_STATE_VALID:
                                    userid = result.user.id
                                    if userid not in useridSet:
                                        useridSet.add(userid)

                            for user in self.area.users:
                                session.delete(user)
                            for userid in useridSet:
                                usr = AreaUser()
                                usr.userid = userid

                                self.area.users.append(usr)
                        end = time.time()
                        time_taken = '{0:.2f}'.format(end - start)
                        self.logDebug("Saving %d results for workunit %d in %s seconds\n", resultCount, wu.id, time_taken)
                        session.commit()
                    session.close()
                else:
                    self.logCritical("The output file was not found\n")
            else:
                self.logDebug("No canonical_result for workunit\n")
                self.report_errors(wu)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            if wu.id == self.error_wu_id:
                self.logCritical("Unexpected error occurred, stop after second attempt\n")
                raise
            else:
                self.error_wu_id = wu.id
                self.logCritical("Unexpected error occurred, retrying...\n")
                return -1

        return 0

if __name__ == '__main__':
    asm = MagphysAssimilator()
    asm.run()
