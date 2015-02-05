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
Convert a FITS file ready to be converted into Work Units
"""
from __future__ import print_function
import hashlib
from utils.logging_helper import config_logger
import os
import json
import shutil
import math
import pyfits
import py_boinc
import subprocess
import multiprocessing

import time

from datetime import datetime
from sqlalchemy.sql.expression import select, func
from config import WG_MIN_PIXELS_PER_FILE, WG_ROW_HEIGHT, POGS_BOINC_PROJECT_ROOT, WG_REPORT_DEADLINE
from database.database_support_core import GALAXY, REGISTER, AREA, PIXEL_RESULT, FILTER, RUN_FILTER, FITS_HEADER, RUN, TAG_REGISTER, TAG_GALAXY
#from image.fitsimage import FitsImage
#from utils.name_builder import get_galaxy_image_bucket, get_galaxy_file_name, get_files_bucket, get_key_fits, get_key_sigma_fits
#from utils.s3_helper import S3Helper

LOG = config_logger(__name__)

OLD_WAY = False
APP_NAME = 'magphys_wrapper'
BIN_PATH = POGS_BOINC_PROJECT_ROOT + '/bin'
TEMPLATES_PATH1 = 'templates'                                          # In true BOINC style, this is magically relative to the project root
TEMPLATES_PATH2 = '/home/ec2-user/boinc-magphys/server/runs'           # Where the Server file & model files are
MIN_QUORUM = 2                                                         # Validator run when there are at least this many results for a work unit
TARGET_NRESULTS = MIN_QUORUM                                           # Initially create this many instances of a work unit
DELAY_BOUND = 86400 * WG_REPORT_DEADLINE                               # Clients must report results within WG_REPORT_DEADLINE days
FPOPS_BOUND_PER_PIXEL = 50                                             # Maximum number of gigaflops per pixel client will allow before terminating job
FPOPS_EXP = "e12"
PIXEL_COMMIT_THRESHOLD = 30


class Area:
    """
    An area
    """
    def __init__(self, top_x, top_y, bottom_x, bottom_y):
        self.top_x = top_x
        self.top_y = top_y
        self.bottom_x = bottom_x
        self.bottom_y = bottom_y


class PixelValue:
    """
    The pixel value
    """
    def __init__(self, value, sigma):
        self.value = value
        self.sigma = sigma


class Pixel:
    """
    A pixel
    """
    def __init__(self, x, y, pixels):
        self.x = x
        self.y = y
        self.pixels = pixels
        self.pixel_id = None


class PyBoincWu:
    """
    Used to encapsulate a single insert into the Boinc database
    """

    def __init__(self, app_name, min_quorom, max_success_results, delay_bound, target_nresults, wu_name,
                 wu_template, result_template, rsc_fpops_est, rsc_fpops_bound, rsc_memory_bound,
                 rsc_disk_bound, additional_xml, opaque, priority, list_input_files):

        self.app_name = app_name
        self.min_quorom = min_quorom
        self.max_success_results = max_success_results
        self.delay_bound = delay_bound
        self.target_nresults = target_nresults
        self.wu_name = wu_name
        self.wu_template = wu_template
        self.result_template = result_template
        self.rsc_fpops_est = rsc_fpops_est
        self.rsc_fpops_bound = rsc_fpops_bound
        self.rsc_memory_bound = rsc_memory_bound
        self.rsc_disk_bound = rsc_disk_bound
        self.additional_xml = additional_xml
        self.opaque = opaque
        self.priority = priority
        self.list_input_files = list_input_files


class Fit2Wu:
    """
    Convert a fit file to a wu
    """
    def __init__(self, connection, download_dir, fanout):
        """
        Initialise the class

        :param connection: the database connection
        :param download_dir: where the files will be written
        :param fanout: the fanout
        """
        self._pixel_count = 0
        self._work_units_added = 0
        self._signal_noise_hdu = None
        self._connection = connection
        self._download_dir = download_dir
        self._fanout = fanout
        self._filter_file = None
        self._sfh_model_file = None
        self._ir_model_file = None
        self._zlib_file = None
        self._filename = None
        self._galaxy_name = None
        self._galaxy_id = None
        self._galaxy_type = None
        self._priority = None
        self._redshift = None
        self._run_id = None
        self._sigma = None
        self._sigma_filename = None
        self._rounded_redshift = None
        self._hdu_list = None
        self._layer_count = None
        self._end_y = None
        self._end_x = None
        self._fpops_est_per_pixel = None
        self._cobblestone_scaling_factor = None
        self._template_file = None
        self._layer_order = None
        self._ultraviolet_bands = {}
        self._optical_bands = {}
        self._infrared_bands = {}

        ### New variables for bulk database inserts ###
        self._areaPK = None
        self._pixelPK = None
        self._database_insert_queue = []
        self._boinc_insert_queue = []
        self._db_access_time = []
        self._boinc_db_access_time = []
        self._pixels_processed = 0
    @profile
    def process_file(self, registration):
        """
        Process a registration.

        :param registration:
        """
        self._filename = registration[REGISTER.c.filename]
        self._galaxy_name = registration[REGISTER.c.galaxy_name]
        self._galaxy_type = registration[REGISTER.c.galaxy_type]
        self._priority = registration[REGISTER.c.priority]
        self._redshift = registration[REGISTER.c.redshift]
        self._run_id = registration[REGISTER.c.run_id]
        self._sigma = registration[REGISTER.c.sigma]
        self._sigma_filename = registration[REGISTER.c.sigma_filename]

        # Have we files that we can use for this?
        self._rounded_redshift = self._get_rounded_redshift()
        if self._rounded_redshift is None:
            LOG.error('No models matching the redshift of %.4f', self._redshift)
            return 0, 0

        self._hdu_list = pyfits.open(self._filename, memmap=True)
        self._layer_count = len(self._hdu_list)

        # Do we need to open and sort the S/N Ratio file
        if self._sigma_filename is not None:
            self._sigma = 0.0
            self._signal_noise_hdu = pyfits.open(self._sigma_filename, memmap=True)
            if self._layer_count != len(self._signal_noise_hdu):
                LOG.error('The layer counts do not match %d vs %d', self._layer_count, len(self._signal_noise_hdu))
                return 0, 0
        else:
            self._sigma = float(self._sigma)

        self._end_y = self._hdu_list[0].data.shape[0]
        self._end_x = self._hdu_list[0].data.shape[1]

        LOG.info("Image dimensions: %(x)d x %(y)d x %(z)d => %(pix).2f Mpixels" % {'x': self._end_x, 'y': self._end_y, 'z': self._layer_count, 'pix': self._end_x * self._end_y / 1000000.0})

        # Get the flops estimate amd cobblestone factor
        run = self._connection.execute(select([RUN]).where(RUN.c.run_id == self._run_id)).first()
        self._fpops_est_per_pixel = run[RUN.c.fpops_est]
        self._cobblestone_scaling_factor = run[RUN.c.cobblestone_factor]

        # Create and save the object
        datetime_now = datetime.now()
        # Galaxy ID is only needed once
        self._galaxy_id = self._connection.execute(select([func.max(GALAXY.c.galaxy_id)])).first()[0]
        if self._galaxy_id is None:
            self._galaxy_id = 0
        other_galaxies = self._connection.execute(select([GALAXY.c.name]))
        for gal in other_galaxies:
            if gal[0] == self._galaxy_name:
                self._galaxy_id = self._connection.execute(select([GALAXY.c.galaxy_id]).where(GALAXY.c.name == self._galaxy_name)).first()[0]

        self._galaxy_id += 1
        self._database_insert_queue.append(GALAXY.insert().values(name=self._galaxy_name,
                                                                dimension_x=self._end_x,
                                                                dimension_y=self._end_y,
                                                                dimension_z=self._layer_count,
                                                                redshift=self._redshift,
                                                                sigma=self._sigma,
                                                                create_time=datetime_now,
                                                                image_time=datetime_now,
                                                                galaxy_type=self._galaxy_type,
                                                                ra_cent=0,
                                                                dec_cent=0,
                                                                pixel_count=0,
                                                                pixels_processed=0,
                                                                run_id=self._run_id,
                                                                galaxy_id=self._galaxy_id))

        # Area and Pixel PKs are needed multiple times.
        self._areaPK = self._connection.execute(select([func.max(AREA.c.area_id)])).first()[0]

        if self._areaPK is None:
            self._areaPK = 0

        self._pixelPK = self._connection.execute(select([func.max(PIXEL_RESULT.c.pxresult_id)])).first()[0]

        if self._pixelPK is None:
            self._pixelPK = 0

        if self._galaxy_id is None or self._areaPK is None or self._pixelPK is None:
            raise Exception('galaxy_id {0}, area_id {1}, or pxresult_id {2} is None!'
                            .format(self._galaxy_id, self._areaPK, self._pixelPK))

        LOG.info("Writing %s to database", self._galaxy_name)

        # Store the tags
        self._store_tags(registration[REGISTER.c.register_id])

        # Store the fits header
        self._store_fits_header()

        # Get the filters we're using for this run and sort the layers
        self._get_filters_sort_layers()

        # Build the template file we need if necessary
        self._build_template_file()

        # Copy the filter and model files we need
        self._copy_important_files()

        # Now break up the galaxy into chunks
        self._break_up_galaxy()

        # Sometimes there will be some remaining inserts to perform, so perform them now
        if len(self._database_insert_queue) > 0:
            LOG.info('Processing {0} remaining database inserts'.format(len(self._database_insert_queue)))
            self._run_pending_db_tasks()
            self._run_pending_boinc_db_tasks()

        # Now calculate the amount of time spent in the db...
        sum = 0
        for rtime in self._db_access_time:
            sum += rtime

        ave = sum / len(self._db_access_time)
        LOG.info('Total time in DB for this galaxy {0}'.format(sum))
        LOG.info('Average time in DB for each area {0}'.format(ave))

        # ... And the amount of time spent in the boinc db
        bsum = 0
        for rtime in self._boinc_db_access_time:
            bsum += rtime

        bave = bsum / len(self._boinc_db_access_time)
        LOG.info('Total time in BOINC DB for this galaxy {0}'.format(bsum))
        LOG.info('Average time in BOINC DB for each area {0}'.format(bave))

        LOG.info('Building the images')
        """
        galaxy_file_name = get_galaxy_file_name(self._galaxy_name, self._run_id, self._galaxy_id)
        s3helper = S3Helper()
        image = FitsImage(self._connection)
        image.build_image(self._filename, galaxy_file_name, self._galaxy_id, get_galaxy_image_bucket())

        # Copy the fits file to S3 - renamed to make it unique
        bucket_name = get_files_bucket()
        s3helper.add_file_to_bucket(bucket_name, get_key_fits(self._galaxy_name, self._run_id, self._galaxy_id), self._filename)
        if self._sigma_filename is not None:
            s3helper.add_file_to_bucket(bucket_name, get_key_sigma_fits(self._galaxy_name, self._run_id, self._galaxy_id), self._sigma_filename)
        """
        # Store the pixel count as the last thing to stop the original_image_checker going off
        # too soon for BIG galaxies
        self._connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == self._galaxy_id).values(pixel_count=self._pixel_count))
        return self._work_units_added, self._pixel_count, sum, ave, bsum, bave

    def _run_db_tasks_parallel(self):
        db_process = multiprocessing.Process(target=self._run_pending_db_tasks)
        boinc_db_process = multiprocessing.Process(target=self._run_pending_boinc_db_tasks)

        db_process.start()
        boinc_db_process.start()

        db_process.join()
        boinc_db_process.join()

        self._database_insert_queue = []
        self._boinc_insert_queue = []

    @profile
    def _break_up_galaxy(self):
        """
        Break up the galaxy into small pieces
        """
        start_y = 0
        for pix_y in range(start_y, self._end_y, WG_ROW_HEIGHT):
            self._create_areas(pix_y)

    def _run_pending_db_tasks(self):
        """
        Runs all of the queued database tasks as one transaction
        :return:
        """
        LOG.info('Committing all pending data to database')
        start = time.time()
        # Perform all database actions now as one bulk insert
        transaction = self._connection.begin()
        try:
            for query in self._database_insert_queue:
                self._connection.execute(query)
            transaction.commit()
        except Exception:
            LOG.error('Error inserting into database')
            transaction.rollback()
            raise
        # Used to calculate the average time spend in the db
        self._db_access_time.append(time.time() - start)
        # Reset queue to none
        self._database_insert_queue = []
        
    def _run_pending_boinc_db_tasks(self):
        """
        Runs all of the queued boinc db tasks as one transaction.
        :return:
        """
        LOG.info('Committing all pending data to BOINC database')
        start = time.time()
        for query in self._boinc_insert_queue:

            py_boinc.boinc_db_transaction_start()
            retval = py_boinc.boinc_create_work(app_name=query.app_name,
                                                min_quorom=query.min_quorom,
                                                max_success_results=query.max_success_results,
                                                delay_bound=query.delay_bound,
                                                target_nresults=query.target_nresults,
                                                wu_name=query.wu_name,
                                                wu_template=query.wu_template,
                                                result_template=query.result_template,
                                                rsc_fpops_est=query.rsc_fpops_est,
                                                rsc_fpops_bound=query.rsc_fpops_bound,
                                                rsc_memory_bound=query.rsc_memory_bound,
                                                rsc_disk_bound=query.rsc_disk_bound,
                                                additional_xml=query.additional_xml,
                                                opaque=query.opaque,
                                                priority=query.priority,
                                                list_input_files=query.list_input_files)
            if retval != 0:
                py_boinc.boinc_db_transaction_rollback()
                LOG.error('Error writing to boinc database. boinc_create_work return value = {0}'.format(retval))
                return
            else:
                py_boinc.boinc_db_transaction_commit()

        # Used to calculate the final average time spent in the boinc db
        self._boinc_db_access_time.append(time.time() - start)
        # Reset queue to none.
        self._boinc_insert_queue = []


    def _build_template_file(self):
        """
        Build the template files we need if they don't exist
        """
        self._template_file = '{0}/{1:=04d}/fitsed_wu_{2}.xml'.format(POGS_BOINC_PROJECT_ROOT, self._run_id, self._rounded_redshift)
        if not os.path.isfile(self._template_file):
            # Make the directory we need
            directory = '{0}/{1:=04d}'.format(POGS_BOINC_PROJECT_ROOT, self._run_id)
            if not os.path.isdir(directory):
                os.mkdir(directory)
            template_file = open(self._template_file, 'wb')
            template_file.write('''<input_template>
    <file_info>
        <number>0</number>
    </file_info>
    <file_info>
        <number>1</number>
    </file_info>
    <file_info>
        <number>2</number>
        <sticky/>
        <no_delete/>
    </file_info>
    <file_info>
        <number>3</number>
        <sticky/>
        <no_delete/>
    </file_info>
    <file_info>
        <number>4</number>
        <sticky/>
        <no_delete/>
    </file_info>
    <file_info>
        <number>5</number>
        <sticky/>
        <no_delete/>
    </file_info>

    <workunit>
        <file_ref>
            <file_number>0</file_number>
            <open_name>observations.dat</open_name>
            <copy_file/>
        </file_ref>
        <file_ref>
            <file_number>1</file_number>
            <open_name>job.xml</open_name>
            <copy_file/>
        </file_ref>
        <file_ref>
            <file_number>2</file_number>
            <open_name>filters.dat</open_name>
            <copy_file/>
        </file_ref>
        <file_ref>
            <file_number>3</file_number>
            <open_name>zlibs.dat</open_name>
            <copy_file/>
        </file_ref>
        <file_ref>
            <file_number>4</file_number>
            <open_name>starformhist_cb07_z{0}.lbr</open_name>
            <copy_file/>
        </file_ref>
        <file_ref>
            <file_number>5</file_number>
            <open_name>infrared_dce08_z{0}.lbr</open_name>
            <copy_file/>
        </file_ref>
        <rsc_disk_bound>500000000</rsc_disk_bound>
    </workunit>
</input_template>'''.format(self._rounded_redshift))
            template_file.close()

    def _copy_important_files(self):
        """
        Copy the model, zlib and filter files to where we need them (if the don't exist). They are marked as no_delete so one should be all we need
        """
        # Copy the filter file
        self._filter_file = '{0:=04d}_filters.dat'.format(self._run_id)
        new_full_path = self._fanout_path(self._filter_file)
        if not os.path.isfile(new_full_path):
            source = '{0}/{1:=04d}/filters.dat'.format(TEMPLATES_PATH2, self._run_id)
            shutil.copy(source, new_full_path)

        # Copy the SFH model
        self._sfh_model_file = '{0:=04d}_starformhist_cb07_z{1}.lbr'.format(self._run_id, self._rounded_redshift)
        new_full_path = self._fanout_path(self._sfh_model_file)
        if not os.path.isfile(new_full_path):
            source = '{0}/{1:=04d}/starformhist_cb07_z{2}.lbr'.format(TEMPLATES_PATH2, self._run_id, self._rounded_redshift)
            shutil.copy(source, new_full_path)

        # Copy the IR model
        self._ir_model_file = '{0:=04d}_infrared_dce08_z{1}.lbr'.format(self._run_id, self._rounded_redshift)
        new_full_path = self._fanout_path(self._ir_model_file)
        if not os.path.isfile(new_full_path):
            source = '{0}/{1:=04d}/infrared_dce08_z{2}.lbr'.format(TEMPLATES_PATH2, self._run_id, self._rounded_redshift)
            shutil.copy(source, new_full_path)

        # Create the zlib file
        self._zlib_file = '{0:=04d}zlib_{1}.dat'.format(self._run_id, self._rounded_redshift)
        new_full_path = self._fanout_path(self._zlib_file)
        if not os.path.isfile(new_full_path):
            zlib_file = open(new_full_path, 'wb')
            zlib_file.write(' 1  {0}'.format(self._rounded_redshift))
            zlib_file.close()
    @profile
    def _create_areas(self, pix_y):
        """
        Create a area - we try to make them squares, but they aren't as the images have dead zones
        """
        area_insert = AREA.insert()
        pixel_result_insert = PIXEL_RESULT.insert()
        pix_x = 0
        while pix_x < self._end_x:
            max_x, pixels = self._get_pixels(pix_x, pix_y)

            if len(pixels) > 0:
                area = Area(pix_x, pix_y, max_x, min(pix_y + WG_ROW_HEIGHT, self._end_y))

                # Needs to be incremented before use
                self._areaPK += 1
                area.area_id = self._areaPK

                # Enqueue this insert
                self._database_insert_queue.append(area_insert.values(galaxy_id=self._galaxy_id,
                                                                      top_x=area.top_x,
                                                                      top_y=area.top_y,
                                                                      bottom_x=area.bottom_x,
                                                                      bottom_y=area.bottom_y,
                                                                      area_id=self._areaPK))

                for pixel in pixels:
                    # Needs to be incremented before use
                    self._pixelPK += 1
                    pixel.pixel_id = self._pixelPK

                    # Enqueue this insert
                    self._database_insert_queue.append(pixel_result_insert.values(galaxy_id=self._galaxy_id,
                                                                                  area_id=area.area_id,
                                                                                  y=pixel.y,
                                                                                  x=pixel.x,
                                                                                  pxresult_id=self._pixelPK))
                    self._pixel_count += 1

                # Write the pixels, at this point the area has been fully created
                self._create_output_file(area, pixels)
                self._work_units_added += 1
                self._pixels_processed += len(pixels)

                # Once we've processed more pixels then the commit threshold, we commit everything to both dbs
                if self._pixels_processed > PIXEL_COMMIT_THRESHOLD:
                    self._run_pending_db_tasks()
                    self._run_pending_boinc_db_tasks()
                    self._pixels_processed = 0  # reset for next areas

            pix_x = max_x + 1


    def _create_job_xml(self, file_name, pixels_in_file):
        """
        Create the job.xml file

        :param file_name:
        :param pixels_in_file:
        """
        new_full_path = self._fanout_path(file_name)
        job_file = open(new_full_path, 'wb')
        job_file.write('<job_desc>\n')
        for i in range(1, pixels_in_file + 1):
            job_file.write('''   <task>
      <application>fit_sed</application>
      <command_line>{0} filters.dat observations.dat</command_line>
      <stdout_filename>stdout_file</stdout_filename>
      <stderr_filename>stderr_file</stderr_filename>
   </task>
'''.format(i))

        job_file.write('''   <task>
      <application>concat</application>
      <command_line>{0} output.fit</command_line>
      <stdout_filename>stdout_file</stdout_filename>
      <stderr_filename>stderr_file</stderr_filename>
   </task>
'''.format(pixels_in_file))

        job_file.write('</job_desc>\n')
        job_file.close()

    def _create_observation_file(self, filename, data, pixels):
        """
        Create an observation file for the list of pixels
        :param filename:
        :param data:
        :param pixels:
        """
        new_full_path = self._fanout_path(filename)
        outfile = open(new_full_path, 'w')
        outfile.write('#  {0}\n'.format(json.dumps(data)))

        row_num = 0
        for pixel in pixels:
            outfile.write('pix%(id)s %(pixel_redshift)s ' % {'id': pixel.pixel_id, 'pixel_redshift': self._redshift})
            for pixel_value in pixel.pixels:
                outfile.write("{0}  {1}  ".format(pixel_value.value, pixel_value.sigma))

            outfile.write('\n')
            row_num += 1
        outfile.close()
    @profile
    def _create_output_file(self, area, pixels):
        """
        Write an output file for this area
        :param area:
        :param pixels:
        """
        pixels_in_area = len(pixels)
        work_unit_name = '%(galaxy)s_area%(area)s' % {'galaxy': self._galaxy_name, 'area': area.area_id}
        LOG.info("Creating work unit %s : %d pixels", work_unit_name, pixels_in_area)

        file_name_job = work_unit_name + '.job.xml'

        # Copy files into BOINC's download hierarchy
        data = [{'galaxy': self._galaxy_name,
                 'run_id': self._run_id,
                 'galaxy_id': self._galaxy_id,
                 'area_id': area.area_id,
                 'pixels': pixels_in_area,
                 'top_x': area.top_x,
                 'top_y': area.top_y,
                 'bottom_x': area.bottom_x,
                 'bottom_y': area.bottom_y, }]
        self._create_observation_file(work_unit_name, data, pixels)
        self._create_job_xml(file_name_job, pixels_in_area)

        # And "create work" = create the work unit
        args_files = [work_unit_name, file_name_job, self._filter_file, self._zlib_file, self._sfh_model_file, self._ir_model_file]
        if OLD_WAY:
            args_params = [
                "--appname",         APP_NAME,
                "--min_quorum",      "%(min_quorum)s" % {'min_quorum': MIN_QUORUM},
                "--max_success_results", "4",
                "--delay_bound",     "%(delay_bound)s" % {'delay_bound': DELAY_BOUND},
                "--target_nresults", "%(target_nresults)s" % {'target_nresults': TARGET_NRESULTS},
                "--wu_name",         work_unit_name,
                "--wu_template",     self._template_file,
                "--result_template", TEMPLATES_PATH1 + "/fitsed_result.xml",
                "--rsc_fpops_est",   "%(est).4f%(exp)s" % {'est': self._fpops_est_per_pixel * pixels_in_area, 'exp': FPOPS_EXP},
                "--rsc_fpops_bound", "%(bound).4f%(exp)s" % {'bound': self._fpops_est_per_pixel * FPOPS_BOUND_PER_PIXEL * pixels_in_area, 'exp': FPOPS_EXP},
                "--rsc_memory_bound", "1e8",
                "--rsc_disk_bound", "1e8",
                "--additional_xml", "<credit>%(credit).03f</credit>" % {'credit': pixels_in_area * self._cobblestone_scaling_factor},
                "--opaque",   str(area.area_id),
                "--priority", '{0}'.format(self._priority)
            ]
            cmd_create_work = [
                BIN_PATH + "/create_work"
            ]
            cmd_create_work.extend(args_params)
            cmd_create_work.extend(args_files)
            subprocess.call(cmd_create_work)

        else:
            entry = PyBoincWu(app_name=APP_NAME,
                                min_quorom=MIN_QUORUM,
                                max_success_results=4,
                                delay_bound=DELAY_BOUND,
                                target_nresults=TARGET_NRESULTS,
                                wu_name=work_unit_name,
                                wu_template=self._template_file,
                                result_template=TEMPLATES_PATH1 + "/fitsed_result.xml",
                                rsc_fpops_est=self._fpops_est_per_pixel * pixels_in_area * 1e12,
                                rsc_fpops_bound=self._fpops_est_per_pixel * FPOPS_BOUND_PER_PIXEL * pixels_in_area * 1e12,
                                rsc_memory_bound=1e8,
                                rsc_disk_bound=1e8,
                                additional_xml="<credit>%(credit).03f</credit>" % {'credit': pixels_in_area * self._cobblestone_scaling_factor},
                                opaque=area.area_id,
                                priority=self._priority,
                                list_input_files=args_files)
            self._boinc_insert_queue.append(entry)

    def _enough_layers(self, pixels):
        """
        Are there enough layers with data in them to warrant counting this pixel?
        :param pixels:
        """
        uv_layers = 0
        for layer_id in self._ultraviolet_bands.values():
            if pixels[layer_id].value > 0:
                uv_layers += 1

        optical_layers = 0
        for layer_id in self._optical_bands.values():
            if pixels[layer_id].value > 0:
                optical_layers += 1

        ir_layers = 0
        for layer_id in self._infrared_bands.values():
            if pixels[layer_id].value > 0:
                ir_layers += 1

        if optical_layers >= 4:
            return True

        if optical_layers == 3 and (uv_layers >= 1 or ir_layers >= 1):
            return True

        # Not enough layers
        return False

    def _fanout_path(self, file_name):
        """
        Calculate the fanout path and create the directory

        :param file_name:
        :rtype : the string of the download directory
        """
        s = hashlib.md5(file_name).hexdigest()[:8]
        x = long(s, 16)

        # Create the directory if needed
        hash_dir_name = "%s/%x" % (self._download_dir, x % self._fanout)
        if os.path.isfile(hash_dir_name):
            pass
        elif os.path.isdir(hash_dir_name):
            pass
        else:
            os.mkdir(hash_dir_name)

        return "%s/%x/%s" % (self._download_dir, x % self._fanout, file_name)

    def _get_filters_sort_layers(self):
        """
        Get the filters we'll be using for this run
        """
        # Build the filter tables I need
        self._ultraviolet_bands = {}
        self._optical_bands = {}
        self._infrared_bands = {}

        # Get the filters associated with this run
        list_filter_names = []
        for filter_name in self._connection.execute(select([FILTER], distinct=True, from_obj=FILTER.join(RUN_FILTER)).where(RUN_FILTER.c.run_id == self._run_id).order_by(FILTER.c.eff_lambda)):
            list_filter_names.append(filter_name)

        # The order of the filters will be there order in the fits file so record the name and its position
        names = []
        for layer in range(self._layer_count):
            hdu = self._hdu_list[layer]
            filter_name_magphysn = hdu.header['MAGPHYSN']
            if filter_name_magphysn is None:
                raise LookupError('The layer {0} does not have MAGPHYSN in it'.format(layer))
            names.append(filter_name_magphysn)

            found_filter = False
            for filter_name in list_filter_names:
                if filter_name_magphysn == filter_name[FILTER.c.name]:
                    found_filter = True
                    break

            if not found_filter:
                raise LookupError('The filter {0} in the fits file is not expected'.format(filter_name_magphysn))

        # If the fit is using a S/N ratio file check the order is correct
        if self._signal_noise_hdu is not None:
            names_snr = []
            for layer in range(self._layer_count):
                hdu = self._signal_noise_hdu[layer]
                filter_name = hdu.header['MAGPHYSN']
                if filter_name is None:
                    raise LookupError('The layer {0} does not have MAGPHYSN in it'.format(layer))
                names_snr.append(filter_name)

            # Make sure they match
            if len(names) == len(names_snr):
                for index in range(len(names)):
                    if names[index] != names_snr[index]:
                        raise LookupError('The list of bands are not the same size {0} vs {1}'.format(names, names_snr))
            else:
                raise LookupError('The list of bands are not the same size {0} vs {1}'.format(names, names_snr))

        layers = []
        for filter_name in list_filter_names:
            found_it = False
            for i in range(len(names)):
                if names[i] == filter_name[FILTER.c.name]:
                    layers.append(i)
                    if filter_name[FILTER.c.infrared] == 1:
                        self._infrared_bands[filter_name[FILTER.c.name]] = i

                    if filter_name[FILTER.c.optical] == 1:
                        self._optical_bands[filter_name[FILTER.c.name]] = i

                    if filter_name[FILTER.c.ultraviolet] == 1:
                        self._ultraviolet_bands[filter_name[FILTER.c.name]] = i
                    found_it = True
                    break

            if not found_it:
                layers.append(-1)

        self._layer_order = layers

    def _get_pixels(self, pix_x, pix_y):
        """
        Retrieves pixels from each pair of (x, y) coordinates specified in pix_x and pix_y.
        Returns pixels only from those coordinates where there is data in more than
        given by the enough_layers function. Pixels are retrieved in the order specified in
        the global LAYER_ORDER list.
        """
        result = []
        max_x = pix_x
        x = pix_x
        while x < self._end_x:
            for y in range(pix_y, pix_y + WG_ROW_HEIGHT):
                # Have we moved off the edge
                if y >= self._end_y:
                    continue

                pixels = []
                for layer in self._layer_order:
                    if layer == -1:
                        # The layer is missing
                        pixels.append(PixelValue(0, 0))
                    else:
                        # A vagary of PyFits/NumPy is the order of the x & y indexes is reversed
                        # See page 13 of the PyFITS User Guide
                        pixel = self._hdu_list[layer].data[y, x]
                        if math.isnan(pixel) or pixel == 0.0:
                            # A zero tells MAGPHYS - we have no value here
                            pixels.append(PixelValue(0, 0))
                        else:
                            if self._signal_noise_hdu is not None:
                                sigma = pixel / self._signal_noise_hdu[layer].data[y, x]
                            else:
                                sigma = pixel * self._sigma
                            pixels.append(PixelValue(pixel, sigma))

                if self._enough_layers(pixels):
                    result.append(Pixel(x, y, pixels))

            max_x = x
            if len(result) > WG_MIN_PIXELS_PER_FILE:
                break

            x += 1

        return max_x, result

    def _get_rounded_redshift(self):
        """
        Select the template for the red shift
        """
        if self._redshift < 0.005:
            return '0.0000'
        elif self._redshift < 0.015:
            return '0.0100'
        elif self._redshift < 0.025:
            return '0.0200'
        elif self._redshift < 0.035:
            return '0.0300'
        elif self._redshift < 0.045:
            return '0.0400'
        elif self._redshift < 0.055:
            return '0.0500'
        elif self._redshift < 0.065:
            return '0.0600'
        elif self._redshift < 0.075:
            return '0.0700'
        elif self._redshift < 0.085:
            return '0.0800'
        elif self._redshift < 0.095:
            return '0.0900'
        elif self._redshift < 0.105:
            return '0.1000'
        elif self._redshift < 0.115:
            return '0.1100'
        elif self._redshift < 0.125:
            return '0.1200'
        else:
            return None

    def _store_fits_header(self):
        """
        Store the FITS headers we need to remember
        """
        insert = FITS_HEADER.insert()
        header = self._hdu_list[0].header
        index = 0
        ctype1 = None
        ctype2 = None
        ra_deg_found = False
        dec_deg_found = False
        for keyword in header:
            try:
                # The new version of PyFits supports comments
                value = header[index]
                comment = header.comments[index]
                self._database_insert_queue.append(insert.values(galaxy_id=self._galaxy_id, keyword=keyword, value=value, comment=comment))

                # Record the ctype so we can get the RA and DEC
                if keyword == 'CTYPE1':
                    ctype1 = value
                elif keyword == 'CTYPE2':
                    ctype2 = value

                # Record the RA and DEC if we can
                if not ra_deg_found:
                    if keyword == 'RA_CENT' or (ctype1 == 'RA---TAN' and keyword == 'CRVAL1') or keyword == 'RA_DEG':
                        self._connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == self._galaxy_id).values(ra_cent=float(value)))
                    if keyword == 'RA_DEG':
                        ra_deg_found = True

                if not dec_deg_found:
                    if keyword == 'DEC_CENT' or (ctype2 == 'DEC--TAN' and keyword == 'CRVAL2') or keyword == 'DEC_DEG':
                        self._connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == self._galaxy_id).values(dec_cent=float(value)))
                    if keyword == 'DEC_DEG':
                        dec_deg_found = True
            except pyfits.verify.VerifyError:
                LOG.exception('VerifyError')
            index += 1

    def _store_tags(self, register_id):
        """
        Copy the tags to the galaxy
        :param register_id:
        :return:
        """
        for tag_register in self._connection.execute(select([TAG_REGISTER]).where(TAG_REGISTER.c.register_id == register_id)):
            LOG.info('tag_id: {0}, galaxy_id: {1}, register_id: {2}'.format(tag_register[TAG_REGISTER.c.tag_id], self._galaxy_id, register_id))
            self._database_insert_queue.append(TAG_GALAXY.insert().values(galaxy_id=self._galaxy_id, tag_id=tag_register[TAG_REGISTER.c.tag_id]))
