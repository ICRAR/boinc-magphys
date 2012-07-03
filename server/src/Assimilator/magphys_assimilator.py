#! /usr/bin/env python

import assimilator
import os, re, signal, sys, time, hashlib
import boinc_path_config
from Boinc import database, boinc_db, boinc_project_path, configxml, sched_messages
from xml.dom.minidom import parseString
import xml.dom

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, REAL, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
class PixelResult(Base):
    __tablename__ = 'pixel_result'
    
    pxresult_id = Column(Integer, primary_key=True)
    point_name = Column(String(100))
    workunit_id = Column(Integer)
    i_sfh = Column(Float)
    i_ir = Column(Float)
    chi2 = Column(Float)
    redshift = Column(Float)
    fmu_sfh = Column(Float)
    fmu_ir = Column(Float)
    mu = Column(Float)
    tauv = Column(Float)
    s_sfr = Column(Float)
    m = Column(Float)
    ldust = Column(Float)
    t_w_bc = Column(Float)
    t_c_ism = Column(Float)
    xi_c_tot = Column(Float)
    xi_pah_tot = Column(Float)
    xi_mir_tot = Column(Float)
    x_w_tot = Column(Float)
    tvism = Column(Float)
    mdust = Column(Float)
    sfr = Column(Float)
    i_opt = Column(Float)
    dmstar = Column(Float)
    dfmu_aux = Column(Float)
    dz = Column(Float)
    
class PixelFilter(Base):
    __tablename__ = 'pixel_filter'
    
    pxfilter_id = Column(Integer, primary_key=True)
    pxresult_id = Column(Integer, ForeignKey('pixel_result.pxresult_id'))
    filter_name = Column(String(100))
    observed_flux = Column(Float)
    observational_uncertainty = Column(Float)
    flux_bfm = Column(Float)
    
    work_unit = relationship("PixelResult", backref=backref('filters', order_by=pxfilter_id))
    
class PixelParameter(Base):
    __tablename__ = 'pixel_parameter'
    
    pxparameter_id = Column(Integer, primary_key=True)
    pxresult_id = Column(Integer, ForeignKey('pixel_result.pxresult_id'))
    parameter_name = Column(String(100))
    percentile2_5 = Column(Float)
    percentile16 = Column(Float)
    percentile50 = Column(Float)
    percentile84 = Column(Float)
    percentile97_5 = Column(Float)
    
    work_unit = relationship("PixelResult", backref=backref('parameters', order_by=pxparameter_id))

class PixelHistogram(Base):
    __tablename__ = 'pixel_histogram'
    
    pxhistogram_id = Column(Integer, primary_key=True)
    pxparameter_id = Column(Integer, ForeignKey('pixel_parameter.pxparameter_id'))
    x_axis = Column(Float)
    hist_value = Column(Float)
    
    parameter = relationship("PixelParameter", backref=backref('histograms', order_by=pxhistogram_id))
    
class PixelUser(Base):
    __tablename__ = 'pixel_user'
    
    pxuser_id = Column(Integer, primary_key=True)
    pxresult_id = Column(Integer, ForeignKey('pixel_result.pxresult_id'))
    userid = Column(Integer)
    create_time = Column(TIMESTAMP)
    
    work_unit = relationship("PixelResult", backref=backref('users', order_by=pxuser_id))
            
class MagphysAssimilator(assimilator.Assimilator):
    
    def __init__(self):
        assimilator.Assimilator.__init__(self)
        #super(MagphysAssimilator, self).__init__(self)
        
        login = "mysql://root:@localhost/magphys_as"
        try:
             f = open(os.path.expanduser("~/Magphys.Profile") , "r")
             for line in f:
                 if line.startswith("url="):
                   login = line[4:]
             f.close()
        except IOError as e:
            pass
            
        engine = create_engine(login)
        self.Session = sessionmaker(bind=engine)
    
    def get_output_file_infos(self, result, list):
        dom = parseString(result.xml_doc_in)
        for node in dom.getElementsByTagName('file_name'):
            list.append(node.firstChild.nodeValue)
        
    def getResult(self, session, pointName):
        if self.noinsert:
            pxresult = None
        else:
            pxresult = session.query(PixelResult).filter("point_name=:name").params(name=pointName).first()
        #doAdd = False
        if pxresult == None:
            pxresult = PixelResult()
        else:
            for filter in pxresult.filters:
                session.delete(filter)
            for parameter in pxresult.parameters:
                for histogram in parameter.histograms:
                    session.delete(histogram)
                session.delete(parameter)
            for user in pxresult.users:
                session.delete(user)
        pxresult.point_name = pointName;
        pxresult.filters = []
        pxresult.parameters = []
        return pxresult
    
    def saveResult(self, session, pxresult, results):
        for result in results:
            if result.user and result.validate_status == boinc_db.VALIDATE_STATE_VALID:
                usr = PixelUser()
                usr.userid = result.user.id
                #usr.create_time = 
                pxresult.users.append(usr)
            
        if pxresult.pxresult_id == None and not self.noinsert:
            session.add(pxresult)
    
    def processResult(self, session, outFile, wu, results):
        """
        Read the output file, add the values to the PixelResult row, and insert the filter,
        parameter and histogram rows.
        """
        f = open(outFile , "r")
        lineNo = 0
        pointName = None
        pxresult = None
        parameter = None
        percentilesNext = False
        histogramNext = False
        skynetNext = False
        for line in f:
            lineNo = lineNo + 1
            
            if line.startswith(" ####### "):
                if pxresult:
                    self.saveResult(session, pxresult, results)
                values = line.split()
                pointName = values[1]
                print pointName
                pxresult = self.getResult(session, pointName)
                pxresult.workunit_id = wu.id
                lineNo = 0
                percentilesNext = False;
                histogramNext = False
                skynetNext = False
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
                        idx = idx + 1
                elif lineNo == 4:
                    idx = 0
                    values = line.split()
                    for value in values:
                        filter = pxresult.filters[idx]
                        filter.observational_uncertainty = float(value)
                        idx = idx + 1
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
                        idx = idx + 1
                elif lineNo > 13:
                    if line.startswith("# ..."):
                        parts = line.split('...')
                        parameterName = parts[1].strip()
                        parameter = PixelParameter()
                        parameter.parameter_name = parameterName;
                        pxresult.parameters.append(parameter)
                        percentilesNext = False;
                        histogramNext = True
                        skynetNext = False
                    elif line.startswith("#....percentiles of the PDF......") and parameter != None:
                        percentilesNext = True;
                        histogramNext = False
                        skynetNext = False
                    elif line.startswith(" #...theSkyNet"):
                        percentilesNext = False;
                        histogramNext = False
                        skynetNext = True
                    elif percentilesNext:
                        values = line.split()
                        parameter.percentile2_5 = float(values[0])
                        parameter.percentile16 = float(values[1])
                        parameter.percentile50 = float(values[2])
                        parameter.percentile84 = float(values[3])
                        parameter.percentile97_5 = float(values[4])
                        percentilesNext = False;
                    elif histogramNext:
                        hist = PixelHistogram()
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
                    
        f.close()
        if pxresult:
            self.saveResult(session, pxresult, results)
        
    def assimilate_handler(self, wu, results, canonical_result):
        """
        Process the Results.
        """

        if wu.canonical_result:
            #file_list = []
            outFile = self.get_file_path(canonical_result)
            #self.get_output_file_infos(canonical_result, file_list)
                    
            if (outFile):
                print "Reading File",
                print outFile
                session = self.Session()
                self.processResult(session, outFile, wu, results)
                if self.noinsert:
                    session.rollback()
                else:
                    session.commit()
            else:
                self.logCritical("The output file was not found\n")
        else:
            self.report_errors(wu)
            return -1
            
        return 0;
    
if __name__ == '__main__':
    asm = MagphysAssimilator()
    asm.run()