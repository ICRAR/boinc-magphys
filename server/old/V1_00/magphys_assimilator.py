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

import os
import sys
import logging

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '../../src/assimilator')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))
LOG.info('PYTHONPATH = {0}'.format(sys.path))

import time
import assimilator
import boinc_path_config
import math
import gzip, traceback, datetime
from Boinc import database, boinc_db, boinc_project_path, configxml, sched_messages
from assimilator_utils import is_gzip
from config import DB_LOGIN, MIN_HIST_VALUE
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from database.database_support_core import PARAMETER_NAME, PIXEL_RESULT, PIXEL_FILTER, PIXEL_HISTOGRAM, PIXEL_PARAMETER, AREA, AREA_USER

ENGINE = create_engine(DB_LOGIN)

class MagphysAssimilator(assimilator.Assimilator):

    def __init__(self):
        assimilator.Assimilator.__init__(self)

        # Login is set in the database package
        connection = ENGINE.connect()
        self._map_parameter_name = {}

        # Load the parameter name map
        for parameter_name in connection.execute(select([PARAMETER_NAME])):
            self._map_parameter_name[parameter_name[PARAMETER_NAME.c.name]] = parameter_name[PARAMETER_NAME.c.parameter_name_id]

        connection.close()

        self.logNormal('Starting assimilator')

    def _get_pixel_result(self, connection, pxresult_id):
        """
        Get the pixel result row from the database
        """
        self._area_id = None
        self._pxresult_id = None
        if not self.noinsert:
            pxresult = connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.pxresult_id == pxresult_id)).first()

            if pxresult is None:
                self.logCritical("Pixel Result row not found for pxresult_id = %s\n", pxresult_id)
            else:
                # Record the area_id
                self._area_id = pxresult[PIXEL_RESULT.c.area_id]
                self._pxresult_id = pxresult[PIXEL_RESULT.c.pxresult_id]

    def _save_results(self, connection, map_pixel_results, list_insert_filters, list_pixel_parameters, map_pixel_histograms):
        """
        Add the pixel to the database
        """
        if self._pxresult_id is not None and not self.noinsert:
            # Update the filters
            connection.execute(PIXEL_RESULT.update().where(PIXEL_RESULT.c.pxresult_id == self._pxresult_id).values(map_pixel_results))

            connection.execute(PIXEL_FILTER.insert(), list_insert_filters)

            # Because I need to get the PK back we have to do each one separately
            for pixel_parameter in list_pixel_parameters:
                result = connection.execute(PIXEL_PARAMETER.insert(), pixel_parameter)
                id = result.inserted_primary_key

                # Add the ID to the list
                list_pixel_histograms = map_pixel_histograms[pixel_parameter['parameter_name_id']]
                for map_values in list_pixel_histograms:
                    map_values['pxparameter_id'] = id[0]

                connection.execute(PIXEL_HISTOGRAM.insert(), list_pixel_histograms)

    def _process_result(self, connection, outFile, wu):
        """
        Read the output file, add the values to the PixelResult row, and insert the filter,
        parameter and histogram rows.
        """
        if is_gzip(outFile):
            f = gzip.open(outFile , "rb")
        else:
            f = open(outFile, "r")

        self._area_id = None
        self._pxresult_id = None
        lineNo = 0
        percentiles_next = False
        histogram_next = False
        skynet_next1 = False
        skynet_next2 = False
        result_count = 0
        map_pixel_results = {}
        map_pixel_parameter = {}
        map_pixel_histograms = {}
        list_filters = []
        list_pixel_parameters = []
        list_pixel_histograms = []
        start_time = None
        try:
            for line in f:
                lineNo += 1

                if line.startswith(" ####### "):
                    if self._pxresult_id is not None:
                        self._save_results(connection, map_pixel_results, list_filters, list_pixel_parameters, map_pixel_histograms)
                        #self.logDebug('%.3f seconds for %d\n', time.time() - start_time, self._pxresult_id)
                    map_pixel_results = {}
                    map_pixel_parameter = {}
                    map_pixel_histograms = {}
                    list_filters = []
                    list_pixel_parameters = []
                    start_time = time.time()
                    values = line.split()
                    pointName = values[1]
                    pxresult_id = pointName[3:].rstrip()
                    self._get_pixel_result(connection, pxresult_id)
                    if self._pxresult_id is not None:
                        map_pixel_results['workunit_id'] = wu.id
                    lineNo = 0
                    percentiles_next = False
                    histogram_next = False
                    skynet_next1 = False
                    skynet_next2 = False
                    result_count += 1
                elif self._pxresult_id is not None:
                    if lineNo == 2:
                        filterNames = line.split()
                        for filterName in filterNames:
                            if filterName != '#':
                                list_filters.append({'filter_name': filterName, 'pxresult_id': self._pxresult_id})
                    elif lineNo == 3:
                        index = 0
                        values = line.split()
                        for value in values:
                            filter = list_filters[index]
                            filter['observed_flux'] = float(value)
                            index += 1
                    elif lineNo == 4:
                        index = 0
                        values = line.split()
                        for value in values:
                            filter = list_filters[index]
                            filter['observational_uncertainty'] = float(value)
                            index += 1
                    elif lineNo == 9:
                        values = line.split()
                        map_pixel_results['i_sfh'] = float(values[0])
                        map_pixel_results['i_ir'] = float(values[1])
                        map_pixel_results['chi2'] = float(values[2])
                        map_pixel_results['redshift'] = float(values[3])
                    elif lineNo == 11:
                        values = line.split()
                        map_pixel_results['fmu_sfh'] = float(values[0])
                        map_pixel_results['fmu_ir'] = float(values[1])
                        map_pixel_results['mu'] = float(values[2])
                        map_pixel_results['tauv'] = float(values[3])
                        map_pixel_results['s_sfr'] = float(values[4])
                        map_pixel_results['m'] = float(values[5])
                        map_pixel_results['ldust'] = float(values[6])
                        map_pixel_results['t_w_bc'] = float(values[7])
                        map_pixel_results['t_c_ism'] = float(values[8])
                        map_pixel_results['xi_c_tot'] = float(values[9])
                        map_pixel_results['xi_pah_tot'] = float(values[10])
                        map_pixel_results['xi_mir_tot'] = float(values[11])
                        map_pixel_results['x_w_tot'] = float(values[12])
                        map_pixel_results['tvism'] = float(values[13])
                        map_pixel_results['mdust'] = float(values[14])
                        map_pixel_results['sfr'] = float(values[15])
                    elif lineNo == 13:
                        index = 0
                        values = line.split()
                        for value in values:
                            filter = list_filters[index]
                            filter['flux_bfm'] = float(value)
                            index += 1
                    elif lineNo > 13:
                        if line.startswith("# ..."):
                            parts = line.split('...')
                            parameterName = parts[1].strip()
                            parameter_name_id = self._map_parameter_name[parameterName]
                            map_pixel_parameter = {'parameter_name_id': parameter_name_id, 'pxresult_id': self._pxresult_id}
                            list_pixel_parameters.append(map_pixel_parameter)
                            list_pixel_histograms = []
                            map_pixel_histograms[parameter_name_id] = list_pixel_histograms
                            percentiles_next = False
                            histogram_next = True
                            skynet_next1 = False
                            skynet_next2 = False
                        elif line.startswith("#....percentiles of the PDF......") and len(map_pixel_parameter) > 0:
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
                            map_pixel_parameter['percentile2_5'] = float(values[0])
                            map_pixel_parameter['percentile16'] = float(values[1])
                            map_pixel_parameter['percentile50'] = float(values[2])
                            map_pixel_parameter['percentile84'] = float(values[3])
                            map_pixel_parameter['percentile97_5'] = float(values[4])
                            percentiles_next = False
                        elif histogram_next:
                            values = line.split()
                            hist_value = float(values[1])
                            if hist_value > MIN_HIST_VALUE and not math.isnan(hist_value):
                                list_pixel_histograms.append({'pxresult_id': self._pxresult_id, 'x_axis': float(values[0]), 'hist_value': hist_value})
                        elif skynet_next1:
                            values = line.split()
                            map_pixel_results['i_opt'] = float(values[0])
                            map_pixel_results['i_ir'] = float(values[1])
                            map_pixel_results['dmstar'] = float(values[2])
                            map_pixel_results['dfmu_aux'] = float(values[3])
                            map_pixel_results['dz'] = float(values[4])
                            skynet_next1 = False
                        elif skynet_next2:
                            # We have the highest bin probability values which require the parameter_id
                            values = line.split()
                            map_pixel_parameter['high_prob_bin'] = float(values[0])
                            map_pixel_parameter['first_prob_bin'] = float(values[1])
                            map_pixel_parameter['last_prob_bin'] = float(values[2])
                            map_pixel_parameter['bin_step'] = float(values[3])
                            skynet_next2 = False

        except IOError:
            self.logCritical('IOError after %d lines\n', lineNo)
        finally:
            f.close()
        if self._pxresult_id is not None:
            self._save_results(connection, map_pixel_results, list_filters, list_pixel_parameters, map_pixel_histograms)
            #self.logDebug('%.3f seconds for %d\n', time.time() - start_time, self._pxresult_id)
        return result_count

    def assimilate_handler(self, wu, results, canonical_result):
        """
        Process the Results.
        """
        self.logDebug("Start of assimilate_handler for wu %d\n", wu.id)
        connection = None
        transaction = None
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
                    connection = ENGINE.connect()
                    transaction = connection.begin()
                    resultCount = self._process_result(connection, outFile, wu)
                    if self.noinsert:
                        transaction.rollback()
                    else:
                        if not resultCount:
                            self.logCritical("No results were found in the output file\n")

                        if self._area_id is None:
                            self.logDebug("The Area was not found\n")
                        else:
                            connection.execute(AREA.update().
                                where(AREA.c.area_id == self._area_id).
                                values(workunit_id = wu.id, update_time = datetime.datetime.now()))

                            user_id_set = set()
                            for result in results:
                                if result.user and result.validate_state == boinc_db.VALIDATE_STATE_VALID:
                                    user_id = result.user.id
                                    if user_id not in user_id_set:
                                        user_id_set.add(user_id)

                            connection.execute(AREA_USER.delete().where(AREA_USER.c.area_id == self._area_id))
                            insert = AREA_USER.insert()
                            for user_id in user_id_set:
                                connection.execute(insert, area_id=self._area_id, userid=user_id)

                        time_taken = '{0:.2f}'.format(time.time() - start)
                        self.logDebug("Saving %d results for workunit %d in %s seconds\n", resultCount, wu.id, time_taken)
                        transaction.commit()
                    connection.close()
                else:
                    self.logCritical("The output file was not found\n")
            else:
                self.logDebug("No canonical_result for workunit\n")
                self.report_errors(wu)
        except:
            if transaction is not None:
                transaction.rollback()
            if connection is not None:
                connection.close()
            print "Unexpected error:", sys.exc_info()[0]
            traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            self.logCritical("Unexpected error occurred, retrying...\n")
            return -1

        return 0

if __name__ == '__main__':
    asm = MagphysAssimilator()
    asm.run()
