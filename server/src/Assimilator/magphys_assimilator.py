#! /usr/bin/env python

import Assimilator
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
class WorkUnitResult(Base):
    __tablename__ = 'work_unit_result'
    
    wuresult_id = Column(Integer, primary_key=True)
    point_name = Column(String(100))
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
    
class WorkUnitFilter(Base):
    __tablename__ = 'work_unit_filter'
    
    wufilter_id = Column(Integer, primary_key=True)
    wuresult_id = Column(Integer, ForeignKey('work_unit_result.wuresult_id'))
    filter_name = Column(String(100))
    observed_flux = Column(Float)
    observational_uncertainty = Column(Float)
    flux_bfm = Column(Float)
    
    work_unit = relationship("WorkUnitResult", backref=backref('filters', order_by=wufilter_id))
    
class WorkUnitParameter(Base):
    __tablename__ = 'work_unit_parameter'
    
    wuparameter_id = Column(Integer, primary_key=True)
    wuresult_id = Column(Integer, ForeignKey('work_unit_result.wuresult_id'))
    parameter_name = Column(String(100))
    percentile2_5 = Column(Float)
    percentile16 = Column(Float)
    percentile50 = Column(Float)
    percentile84 = Column(Float)
    percentile97_5 = Column(Float)
    
    work_unit = relationship("WorkUnitResult", backref=backref('parameters', order_by=wuparameter_id))

class WorkUnitHistogram(Base):
    __tablename__ = 'work_unit_histogram'
    
    wuhistogram_id = Column(Integer, primary_key=True)
    wuparameter_id = Column(Integer, ForeignKey('work_unit_parameter.wuparameter_id'))
    x_axis = Column(Float)
    hist_value = Column(Float)
    
    parameter = relationship("WorkUnitParameter", backref=backref('histograms', order_by=wuhistogram_id))
    
class WorkUnitUser(Base):
    __tablename__ = 'work_unit_user'
    
    wuuser_id = Column(Integer, primary_key=True)
    wuresult_id = Column(Integer, ForeignKey('work_unit_result.wuresult_id'))
    userid = Column(Integer)
    create_time = Column(TIMESTAMP)
    
    work_unit = relationship("WorkUnitResult", backref=backref('users', order_by=wuuser_id))
            
class MagphysAssimilator(Assimilator.Assimilator):
    
    def __init__(self):
        Assimilator.Assimilator.__init__(self)
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
        for node in dom.getElementsByTagName('file_ref'):
            list.append(node.firstChild.nodeValue)
    
    def processResult(self, session, sedFile, fitFile, results):
        parts = fitFile.split('/')
        last = parts[len(parts)-1]
        parts = last.split('.')
        pointName = parts[0]
        print 'Point Name',
        print pointName
        
        #session = self.Session()
        wu = session.query(WorkUnitResult).filter("point_name=:name").params(name=pointName).first()
        doAdd = False
        if (wu == None):
            wu = WorkUnitResult()
        else:
            for filter in wu.filters:
                session.delete(filter)
            for parameter in wu.parameters:
                for histogram in parameter.histograms:
                    session.delete(histogram)
                session.delete(parameter)
            for user in wu.users:
                session.delete(user)
        wu.point_name = pointName;
        wu.filters = []
        wu.parameters = []
        
        self.processFitFile(fitFile, wu)
        self.processSedFile(sedFile, wu)
        
        for result in results:
            usr = WorkUnitUser()
            usr.userid = result.userid
            #usr.create_time = 
            wu.users.append(usr)
            
        if wu.wuresult_id == None:
            session.add(wu)
        #session.commit()
    
    def processFitFile(self, fitFile, wu):
        """
        Read the ".fit" file, add the values to the WorkUnitResult row, and insert the filter,
        parameter and histogram rows.
        """
        f = open(fitFile , "r")
        lineNo = 0
        parameter = None
        percentilesNext = False
        histogramNext = False
        for line in f:
            lineNo = lineNo + 1
            
            if lineNo == 2:
                filterNames = line.split()
                for filterName in filterNames:
                    if filterName != '#':
                        filter = WorkUnitFilter()
                        filter.filter_name = filterName
                        wu.filters.append(filter)
            elif lineNo == 3:
                idx = 0
                values = line.split()
                for value in values:
                    filter = wu.filters[idx]
                    filter.observed_flux = float(value)
                    idx = idx + 1
            elif lineNo == 4:
                idx = 0
                values = line.split()
                for value in values:
                    filter = wu.filters[idx]
                    filter.observational_uncertainty = float(value)
                    idx = idx + 1
            elif lineNo == 9:
                values = line.split()
                wu.i_sfh = float(values[0])
                wu.i_ir = float(values[1])
                wu.chi2 = float(values[2])
                wu.redshift = float(values[3])
                #for value in values:
                #    print value
            elif lineNo == 11:
                values = line.split()
                wu.fmu_sfh = float(values[0])
                wu.fmu_ir = float(values[1])
                wu.mu = float(values[2])
                wu.tauv = float(values[3])
                wu.s_sfr = float(values[4])
                wu.m = float(values[5])
                wu.ldust = float(values[6])
                wu.t_w_bc = float(values[7])
                wu.t_c_ism = float(values[8])
                wu.xi_c_tot = float(values[9])
                wu.xi_pah_tot = float(values[10])
                wu.xi_mir_tot = float(values[11])
                wu.x_w_tot = float(values[12])
                wu.tvism = float(values[13])
                wu.mdust = float(values[14])
                wu.sfr = float(values[15])
            elif lineNo == 13:
                idx = 0
                values = line.split()
                for value in values:
                    filter = wu.filters[idx]
                    filter.flux_bfm = float(value)
                    idx = idx + 1
            elif lineNo > 13:
                if line.startswith("# ..."):
                    parts = line.split('...')
                    parameterName = parts[1].strip()
                    parameter = WorkUnitParameter()
                    parameter.parameter_name = parameterName;
                    wu.parameters.append(parameter)
                    percentilesNext = False;
                    histogramNext = True
                elif line.startswith("#....percentiles of the PDF......") and parameter != None:
                    percentilesNext = True;
                    histogramNext = False
                elif percentilesNext:
                    values = line.split()
                    parameter.percentile2_5 = float(values[0])
                    parameter.percentile16 = float(values[1])
                    parameter.percentile50 = float(values[2])
                    parameter.percentile84 = float(values[3])
                    parameter.percentile97_5 = float(values[4])
                    percentilesNext = False;
                elif histogramNext:
                    hist = WorkUnitHistogram()
                    values = line.split()
                    hist.x_axis = float(values[0])
                    hist.hist_value = float(values[1])
                    parameter.histograms.append(hist)
                    
        f.close()
    
    def processSedFile(self, sedFile, wu):
        """
        Read the ".sed" file, and add other values to the WorkUnitResult row.
        """
        f = open(sedFile , "r")
        lineNo = 0
        #parameterName = None
        skynetFound = False
        for line in f:
            lineNo = lineNo + 1
            
            if lineNo == 1:
                if line.startswith(" #...theSkyNet"):
                    skynetFound = True
            elif lineNo == 2 and skynetFound:
                values = line.split()
                wu.i_opt = float(values[0])
                wu.i_ir = float(values[1])
                wu.dmstar = float(values[2])
                wu.dfmu_aux = float(values[3])
                wu.dz = float(values[4])
        f.close()
        
    def assimilate_handler(self, wu, results, canonical_result):
        """
        Process the Results.
        """

        if (wu.canonical_resultid):
            file_list = []
            self.get_output_file_infos(canonical_result, file_list)
            
            sedFile = None;
            fitFile = None;
            for file in file_list:
                print file
                if (file.endswith(".sed")):
                    sedFile = file
                elif (file.endswith(".fit")):
                    fitFile = file
                    
            if (sedFile and fitFile):
                session = self.Session()
                self.processResult(session, sedFile, fitFile, results)
                session.commit()
            else:
                self.logCritical("Both of the sed and fit files were not returned\n")
        else:
            reportErrors(wu)
            
        return 0;
    
if __name__ == '__main__':
    asm = MagphysAssimilator()
    asm.run()