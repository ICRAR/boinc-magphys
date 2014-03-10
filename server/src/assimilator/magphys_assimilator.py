#! /usr/bin/env python2.7
#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
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

# Setup the Python Path as we may be running this via ssh
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, '..')))
sys.path.append(os.path.abspath(os.path.join(base_path, '../../../../boinc/py')))

import time
import assimilator
import boinc_path_config
import gzip, traceback, datetime
from Boinc import boinc_db
from utils.logging_helper import config_logger
from assimilator_utils import is_gzip
from config import DB_LOGIN
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from database.database_support_core import PARAMETER_NAME, PIXEL_RESULT, AREA, AREA_USER, GALAXY, GALAXY_USER
from utils.name_builder import get_files_bucket, get_key_sed
from utils.s3_helper import S3Helper

LOG = config_logger(__name__)
LOG.info('PYTHONPATH = {0}'.format(sys.path))

ENGINE = create_engine(DB_LOGIN)


class MagphysAssimilator(assimilator.Assimilator):

    def __init__(self):
        assimilator.Assimilator.__init__(self)

        # Login is set in the database package
        connection = ENGINE.connect()
        self._map_parameter_name = {}

        # Load the parameter name map
        for parameter_name in connection.execute(select([PARAMETER_NAME])):
            self._map_parameter_name[parameter_name[PARAMETER_NAME.c.name]] = parameter_name[PARAMETER_NAME.c.column_name]

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

                # Find the galaxy details
                galaxy = connection.execute(select([GALAXY], from_obj=GALAXY.join(AREA))
                                            .where(AREA.c.area_id == self._area_id)).first()
                self._galaxy_name = galaxy[GALAXY.c.name]
                self._galaxy_id = galaxy[GALAXY.c.galaxy_id]
                self._run_id = galaxy[GALAXY.c.run_id]

    def _save_results(self, connection, map_pixel_results):
        """
        Add the pixel to the database
        """
        if self._pxresult_id is not None and not self.noinsert:
            # Update the filters
            connection.execute(PIXEL_RESULT.update().where(PIXEL_RESULT.c.pxresult_id == self._pxresult_id).values(map_pixel_results))

    def _process_result(self, connection, out_file, wu):
        """
        Read the output file, add the values to the PixelResult row, and insert the filter,
        parameter and histogram rows.
        """
        if is_gzip(out_file):
            f = gzip.open(out_file, "rb")
        else:
            f = open(out_file, "r")

        self._area_id = None
        self._pxresult_id = None
        lineNo = 0
        percentiles_next = False
        histogram_next = False
        skynet_next1 = False
        skynet_next2 = False
        result_count = 0
        map_pixel_results = {}
        column_name = None
        start_time = None
        try:
            for line in f:
                lineNo += 1

                if line.startswith(" ####### "):
                    if self._pxresult_id is not None:
                        self._save_results(connection, map_pixel_results)
                        #self.logDebug('%.3f seconds for %d\n', time.time() - start_time, self._pxresult_id)
                    map_pixel_results = {}
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
                    if lineNo == 9:
                        # We can ignore these
                        pass
                    elif lineNo == 11:
                        # We prefer the median values
                        pass
                    elif lineNo > 13:
                        if line.startswith("# ..."):
                            parts = line.split('...')
                            parameter_name = parts[1].strip()
                            column_name = self._map_parameter_name[parameter_name]
                            percentiles_next = False
                            histogram_next = True
                            skynet_next1 = False
                            skynet_next2 = False
                        elif line.startswith("#....percentiles of the PDF......"):
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
                            map_pixel_results[column_name] = float(values[2])
                            percentiles_next = False
                        elif histogram_next:
                            pass
                        elif skynet_next1:
                            skynet_next1 = False
                        elif skynet_next2:
                            # We have the highest bin probability values which require the parameter_id
                            skynet_next2 = False

        except IOError:
            self.logCritical('IOError after %d lines\n', lineNo)
        finally:
            f.close()
        if self._pxresult_id is not None:
            self._save_results(connection, map_pixel_results)
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
                out_file = self.get_file_path(canonical_result)
                self.area = None
                if out_file:
                    if os.path.isfile(out_file):
                        pass
                    else:
                        self.logDebug("File [%s] not found\n", out_file)
                        out_file = None

                if out_file:
                    self.logDebug("Reading File [%s]\n", out_file)
                    start = time.time()
                    connection = ENGINE.connect()
                    transaction = connection.begin()
                    resultCount = self._process_result(connection, out_file, wu)
                    if self.noinsert:
                        transaction.rollback()
                    else:
                        if not resultCount:
                            self.logCritical("No results were found in the output file\n")

                        if self._area_id is None:
                            self.logDebug("The Area was not found\n")
                        else:
                            connection.execute(AREA.update()
                                               .where(AREA.c.area_id == self._area_id)
                                               .values(workunit_id=wu.id, update_time=datetime.datetime.now()))

                            user_id_set = set()
                            for result in results:
                                if result.user and result.validate_state == boinc_db.VALIDATE_STATE_VALID:
                                    user_id = result.user.id
                                    if user_id not in user_id_set:
                                        user_id_set.add(user_id)

                            connection.execute(AREA_USER.delete().where(AREA_USER.c.area_id == self._area_id))
                            insert_area_user = AREA_USER.insert()
                            insert_galaxy_user = GALAXY_USER.insert().prefix_with('IGNORE')
                            for user_id in user_id_set:
                                connection.execute(insert_area_user, area_id=self._area_id, userid=user_id)
                                # self.logDebug("Inserting row into galaxy_user for userid: %d galaxy_id: %d\n", user_id, self._galaxy_id)
                                connection.execute(insert_galaxy_user, galaxy_id=self._galaxy_id, userid=user_id)

                            # Copy the file to S3
                            s3helper = S3Helper()
                            s3helper.add_file_to_bucket(get_files_bucket(),
                                                        get_key_sed(self._galaxy_name, self._run_id, self._galaxy_id, self._area_id),
                                                        out_file,
                                                        reduced_redundancy=True)

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
