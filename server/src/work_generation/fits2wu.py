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
Convert a FITS file ready to be converted into Work Units
"""
from __future__ import print_function
import argparse
import logging
import os
import json
import shutil
import math
import pyfits
import subprocess

from datetime import datetime
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import desc, and_
from config import BOINC_DB_LOGIN, WG_THRESHOLD, WG_HIGH_WATER_MARK, DB_LOGIN, WG_MIN_PIXELS_PER_FILE, WG_ROW_HEIGHT, WG_IMAGE_DIRECTORY, WG_BOINC_PROJECT_ROOT
from database.boinc_database_support import Result
from database.database_support import Register, FitsHeader, Galaxy, Area, PixelResult, RunFile, Run
from image.fitsimage import FitsImage
from work_generation import HEADER_PATTERNS, STAR_FORMATION_FILE, INFRARED_FILE

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--register', type=int, help='the registration id of a galaxy')
parser.add_argument('-l', '--limit', type=int, help='only generate N workunits from this galaxy (for testing)')
args = vars(parser.parse_args())

count = None
if args['register'] is None:
    # select count(*) from result where server_state = 2
    engine = create_engine(BOINC_DB_LOGIN)
    Session = sessionmaker(bind=engine)
    session = Session()
    count = session.query(Result).filter(Result.server_state == 2).count()
    session.close()

    LOG.info('Checking pending = %d : threshold = %d', count, WG_THRESHOLD)

    if count >= WG_THRESHOLD:
        LOG.info('Nothing to do')
        exit(0)

LIMIT = None
if args['limit'] is not None:
    LIMIT = args['limit']

APP_NAME = 'magphys_wrapper'
BIN_PATH = WG_BOINC_PROJECT_ROOT + '/bin'
TEMPLATES_PATH1 = 'templates'                                          # In true BOINC style, this is magically relative to the project root
TEMPLATES_PATH2 = '/home/ec2-user/boinc-magphys/server/runs'           # Where the Server code is
MIN_QUORUM = 2                                                         # Validator run when there are at least this many results for a work unit
TARGET_NRESULTS = MIN_QUORUM                                           # Initially create this many instances of a work unit
DELAY_BOUND = 86400 * 7                                                # Clients must report results within a week
FPOPS_EST_PER_PIXEL = 6                                                # Estimated number of gigaflops per pixel
FPOPS_BOUND_PER_PIXEL = FPOPS_EST_PER_PIXEL*50                         # Maximum number of gigaflops per pixel client will allow before terminating job
FPOPS_EXP = "e12"
COBBLESTONE_SCALING_FACTOR = 8.85

# The BOINC scripts/apps do not feel at home outside their directory
os.chdir(WG_BOINC_PROJECT_ROOT)

# Connect to the database - the login string is set in the database package
engine = create_engine(DB_LOGIN)
Session = sessionmaker(bind=engine)
session = Session()

## ######################################################################## ##
##
## FUNCTIONS AND STUFF
##
## ######################################################################## ##

class Pixel:
    """
    A pixel
    """
    def __init__(self, x, y, pixels):
        self.x = x
        self.y = y
        self.pixels = pixels
        self.pixel_id = None

class Fit2Wu:
    """
    Convert a fit file to a wu
    """
    def __init__(self):
        self._pixel_count = 0
        self._work_units_added = 0

    def process_file(self, registration):
        """
        Process a registration.
        """
        self._registration = registration

        # Get the filters we're using for this run
        self._get_filters()

        # Have we files that we can use for this?
        self._rounded_redshift = self._get_rounded_redshift()
        if self._rounded_redshift is None:
            LOG.error('No models matching the redshift of %.4f', registration.redshift)
            return 0

        self._hdu_list = pyfits.open(registration.filename, memmap=True)
        self._layer_count = len(self._hdu_list)

        self._end_y = self._hdu_list[0].data.shape[0]
        self._end_x = self._hdu_list[0].data.shape[1]

        LOG.info("Image dimensions: %(x)d x %(y)d x %(z)d => %(pix).2f Mpixels" % {'x':self._end_x,'y':self._end_y,'z':self._layer_count,'pix':self._end_x*self._end_y/1000000.0})

        # Update the version number
        version_number = self._get_version_number()
        if version_number > 1:
            self._update_current()

        filePrefixName = registration.galaxy_name + "_" + str(version_number)
        fitsFileName = filePrefixName + ".fits"

        # Create and save the object
        galaxy = Galaxy()
        galaxy.name = registration.galaxy_name
        galaxy.dimension_x = self._end_x
        galaxy.dimension_y = self._end_y
        galaxy.dimension_z = self._layer_count
        galaxy.redshift = registration.redshift
        galaxy.sigma = registration.sigma
        datetime_now = datetime.now()
        galaxy.create_time = datetime_now
        galaxy.image_time = datetime_now
        galaxy.version_number = version_number
        galaxy.galaxy_type = registration.galaxy_type
        galaxy.ra_cent = 0
        galaxy.dec_cent = 0
        galaxy.current = True
        galaxy.pixel_count = 0
        galaxy.pixels_processed = 0
        session.add(galaxy)

        # Flush to the DB so we can get the id
        session.flush()
        self._galaxy = galaxy
        LOG.info("Wrote %s to database", galaxy.name)

        # Store the fits header
        self._store_fits_header()
        self._sort_layers()

        # Build the template file we need if necessary
        self._build_template_file()

        # Now break up the galaxy into chunks
        self._break_up_galaxy()
        galaxy.pixel_count = self._pixel_count
        session.flush()

        LOG.info('Building the images')
        image = FitsImage()
        image.buildImage(registration.filename, WG_IMAGE_DIRECTORY, filePrefixName, "asinh", False, False, False, session, galaxy.galaxy_id)

        shutil.copyfile(registration.filename, image.get_file_path(WG_IMAGE_DIRECTORY, fitsFileName, True))

        return self._work_units_added, self._pixel_count

    def _break_up_galaxy(self):
        """
        Break up the galaxy into small pieces
        """
        start_y = 0
        for pix_y in range(start_y, self._end_y, WG_ROW_HEIGHT):
            self._create_areas(pix_y)

    def _build_template_file(self):
        """
        Build the template files we need if they don't exist
        """
        self._template_file = '{0}/{1:=4d}/fitsed_wu_{2}.xml'.format(TEMPLATES_PATH2, self._registration.run_id, self._rounded_redshift)
        if not os.path.isfile(self._template_file):
            (star_formation, infrared) = self._get_model_files()
            file = open(self._template_file, 'wb')
            file.write('''<input_template>
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
    </file_info>
    <file_info>
        <number>4</number>
    </file_info>
    <file_info>
        <number>5</number>
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
            <sticky/>
            <gzipped_url>{1}</gzipped_url>
            <md5_chksum>{2}</md5_chksum>
            <nbytes>{3}</nbytes>
        </file_ref>
        <file_ref>
            <file_number>5</file_number>
            <open_name>infrared_dce08_z{0}.lbr</open_name>
            <copy_file/>
            <sticky/>
            <gzipped_url>{4}</gzipped_url>
            <md5_chksum>{5}</md5_chksum>
            <nbytes>{6}</nbytes>
        </file_ref>
        <rsc_disk_bound>500000000</rsc_disk_bound>
    </workunit>
</input_template>'''.format(self._rounded_redshift, star_formation.file_name, star_formation.md5_hash, star_formation.size, infrared.file_name, infrared.md5_hash, infrared.size))
            file.close()

    def _create_areas(self, pix_y):
        """
        Create a area - we try to make them squares, but they aren't as the images have dead zones
        """
        pix_x = 0
        while pix_x < self._end_x:
            # Are we limiting the number created
            if LIMIT is not None and self._work_units_added > LIMIT:
                break

            max_x, pixels = self._get_pixels(pix_x, pix_y)
            if len(pixels) > 0:
                area = Area()
                area.galaxy_id = self._galaxy.galaxy_id
                area.top_x = pix_x
                area.top_y = pix_y
                area.bottom_x = max_x
                area.bottom_y = min(pix_y + WG_ROW_HEIGHT, self._end_y)
                session.add(area)
                session.flush()

                for pixel in pixels:
                    pixel_result = PixelResult()
                    pixel_result.galaxy_id = self._galaxy.galaxy_id
                    pixel_result.area_id = area.area_id
                    pixel_result.x = pixel.x
                    pixel_result.y = pixel.y
                    session.add(pixel_result)
                    session.flush()

                    pixel.pixel_id = pixel_result.pxresult_id
                    self._pixel_count += 1

                # Write the pixels
                self._create_output_file(area, pixels)
                self._work_units_added += 1

            pix_x = max_x + 1

    def _create_filters_dat(self, file_name_filters):
        source = '{0}/runs/{1}/filters.dat'.format(TEMPLATES_PATH2, self._registration.run_id)
        new_full_path = subprocess.check_output([BIN_PATH + "/dir_hier_path", file_name_filters]).rstrip()
        shutil.copy(source, new_full_path)

    def _create_job_xml(self, file_name, pixels_in_file):
        """
        Create the job.xml file
        """
        new_full_path = subprocess.check_output([BIN_PATH + "/dir_hier_path", file_name]).rstrip()
        file = open(new_full_path, 'wb')
        file.write('<job_desc>\n')
        for i in range(1, pixels_in_file + 1):
            file.write('''   <task>
      <application>fit_sed</application>
      <command_line>{0} filters.dat observations.dat</command_line>
      <stdout_filename>stdout_file</stdout_filename>
      <stderr_filename>stderr_file</stderr_filename>
   </task>
'''.format(i))

        file.write('''   <task>
      <application>concat</application>
      <command_line>{0} output.fit</command_line>
      <stdout_filename>stdout_file</stdout_filename>
      <stderr_filename>stderr_file</stderr_filename>
   </task>
'''.format(pixels_in_file))

        file.write('</job_desc>\n')
        file.close()

    def _create_observation_file(self, filename, data, pixels):
        """
        Create an observation file

        Create an observation file for the list of pixels
        """
        new_full_path = subprocess.check_output([BIN_PATH + "/dir_hier_path", filename]).rstrip()
        outfile = open(new_full_path, 'w')
        outfile.write('#  %(data)s\n' % { 'data': json.dumps(data) })

        row_num = 0
        for pixel in pixels:
            outfile.write('pix%(id)s %(pixel_redshift)s ' % {'id':pixel.pixel_id, 'pixel_redshift':self._galaxy.redshift})
            for value in pixel.pixels:
                outfile.write("{0}  {1}  ".format(value, value * self._galaxy.sigma))

            outfile.write('\n')
            row_num += 1
        outfile.close()

    def _create_output_file(self, area, pixels):
        """
        Write an output file for this area
        """
        pixels_in_area = len(pixels)
        filename = '%(galaxy)s_area%(area)s' % { 'galaxy':self._galaxy.name, 'area':area.area_id}
        LOG.info("Creating work unit %s : %d pixels", filename, pixels_in_area)

        args_params = [
            "--appname",         APP_NAME,
            "--min_quorum",      "%(min_quorum)s" % {'min_quorum':MIN_QUORUM},
            "--max_success_results", "4",
            "--delay_bound",     "%(delay_bound)s" % {'delay_bound':DELAY_BOUND},
            "--target_nresults", "%(target_nresults)s" % {'target_nresults':TARGET_NRESULTS},
            "--wu_name",         filename,
            "--wu_template",     self._template_file,
            "--result_template", TEMPLATES_PATH1 + "/fitsed_result.xml",
            "--rsc_fpops_est",   "%(est)d%(exp)s" % {'est':FPOPS_EST_PER_PIXEL*pixels_in_area, 'exp':FPOPS_EXP},
            "--rsc_fpops_bound", "%(bound)d%(exp)s"  % {'bound':FPOPS_BOUND_PER_PIXEL*pixels_in_area, 'exp':FPOPS_EXP},
            "--rsc_memory_bound", "1e8",
            "--rsc_disk_bound", "1e8",
            "--additional_xml", "<credit>%(credit).03f</credit>" % {'credit':pixels_in_area*COBBLESTONE_SCALING_FACTOR},
            "--opaque",   str(area.area_id),
            "--priority", '{0}'.format(self._registration.priority)
        ]
        file_name_job = filename + '.job.xml'
        file_name_zlib = filename + '.zlib.dat'
        file_name_filters = filename + '.filters.dat'
        (file_name_star_formation_history, file_name_infrared) = self._get_model_names()
        args_files = [filename, file_name_job, file_name_filters, file_name_zlib, file_name_star_formation_history, file_name_infrared]
        cmd_create_work = [
            BIN_PATH + "/create_work"
        ]
        cmd_create_work.extend(args_params)
        cmd_create_work.extend(args_files)

        # Copy files into BOINC's download hierarchy
        data = [{'galaxy':self._galaxy.name, 'area_id':area.area_id, 'pixels':pixels_in_area, 'top_x':area.top_x, 'top_y':area.top_y, 'bottom_x':area.bottom_x, 'bottom_y':area.bottom_y,}]
        self._create_observation_file(filename, data, pixels)
        self._create_job_xml(file_name_job, pixels_in_area)
        self._create_filters_dat(file_name_filters)
        self._create_zlib_dat(file_name_zlib)

        # And "create work" = create the work unit
        subprocess.call(cmd_create_work)

    def _create_zlib_dat(self, file_name_zlib):
        new_full_path = subprocess.check_output([BIN_PATH + "/dir_hier_path", file_name_zlib]).rstrip()
        file = open(new_full_path, 'wb')
        file.write(' 1  {0}'.format(self._rounded_redshift))
        file.close()

    def _enough_layers(self, pixels):
        """
        Are there enough layers with data in them to warrant counting this pixel?
        """
        uv_layers = 0
        for layer_id in self._ultraviolet_bands.values():
            if pixels[layer_id] > 0:
                uv_layers += 1

        optical_layers = 0
        for layer_id in self._optical_bands.values():
            if pixels[layer_id] > 0:
                optical_layers += 1

        ir_layers = 0
        for layer_id in self._infrared_bands.values():
            if pixels[layer_id] > 0:
                ir_layers += 1

        if optical_layers >= 4:
            return True

        if optical_layers == 3 and (uv_layers >= 1 or ir_layers >= 1):
            return True

        # Not enough layers
        return False

    def _get_filters(self):
        """
        Get the filters we'll be using for this run
        """
        # Build the filter tables I need
        self._filter_bands = []
        self._ultraviolet_bands = {}
        self._optical_bands = {}
        self._infrared_bands = {}

        run = session.query(Run).filter(Run.run_id == self._registration.run_id).first()

        for filter in run.filters:
            self._filter_bands.append(filter.name)

            if filter.infrared == 1:
                self._infrared_bands[filter.name] = filter.sort_order

            if filter.optical == 1:
                self._optical_bands[filter.name] = filter.sort_order

            if filter.ultraviolet == 1:
                self._ultraviolet_bands[filter.name] = filter.sort_order

    def _get_model_files(self):
        """
        Get the two model files we need
        """
        star_formation = None
        infrared = None
        for run_file in session.query(RunFile).filter(RunFile.run_id == self._registration.run_id).filter(RunFile.redshift == self._rounded_redshift).all():
            if run_file.file_type == STAR_FORMATION_FILE:
                star_formation = run_file
            elif run_file.file_type == INFRARED_FILE:
                infrared = run_file

            # Are we done?
            if star_formation is not None and infrared is not None:
                break

        return star_formation, infrared

    def _get_model_names(self):
        """
        Create a unique model name for the run to be stored on the client
        """
        star_formation_history = '{0:=4d}_starformhist_cb07_z{1}.lbr'.format(self._registration.run_id, self._rounded_redshift)
        infrared =  '{0:=4d}_infrared_dce08_z{1}.lbr'.format(self._registration.run_id, self._rounded_redshift)
        return star_formation_history, infrared

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
                        pixels.append(0)
                    else:
                        # A vagary of PyFits/NumPy is the order of the x & y indexes is reversed
                        # See page 13 of the PyFITS User Guide
                        pixel = self._hdu_list[layer].data[y, x]
                        if math.isnan(pixel) or pixel == 0.0:
                            # A zero tells MAGPHYS - we have no value here
                            pixels.append(0)
                        else:
                            pixels.append(pixel)

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
        if self._registration.redshift < 0.005:
            return '0.0000'
        elif self._registration.redshift < 0.015:
            return '0.0100'
        elif self._registration.redshift < 0.025:
            return '0.0200'
        elif self._registration.redshift < 0.035:
            return '0.0300'
        elif self._registration.redshift < 0.045:
            return '0.0400'
        elif self._registration.redshift < 0.055:
            return '0.0500'
        elif self._registration.redshift < 0.065:
            return '0.0600'
        elif self._registration.redshift < 0.075:
            return '0.0700'
        elif self._registration.redshift < 0.085:
            return '0.0800'
        elif self._registration.redshift < 0.095:
            return '0.0900'
        elif self._registration.redshift < 0.105:
            return '0.1000'
        elif self._registration.redshift < 0.115:
            return '0.1100'
        elif self._registration.redshift < 0.125:
            return '0.1200'
        else:
            return None

    def _get_version_number(self):
        """
        Get the version number of the galaxy
        """
        count = session.query(Galaxy).filter(Galaxy.name == self._registration.galaxy_name).count()
        return count + 1

    def _sort_layers(self):
        """
        Look at the layers of a HDU and order them based on the effective wavelength stored in the header
        """
        names = []
        for layer in range(self._layer_count):
            hdu = self._hdu_list[layer]
            filter_name = hdu.header['MAGPHYSN']
            if filter_name is None:
                raise LookupError('The layer {0} does not have MAGPHYSN in it'.format(layer))
            names.append(filter_name)

            found_filter = False
            for name in self._filter_bands:
                if filter_name == name:
                    found_filter = True
                    break

            if not found_filter:
                raise LookupError('The filter {0} in the fits file is not expected'.format(filter_name))

        layers = []
        for filter_name in self._filter_bands:
            found_it = False
            for i in range(len(names)):
                if names[i] == filter_name:
                    layers.append(i)
                    found_it = True
                    break
            if not found_it:
                layers.append(-1)

        self._layer_order = layers

    def _store_fits_header(self):
        """
        Store the FITS headers we need to remember
        """
        header = self._hdu_list[0].header
        for keyword in header:
            for pattern in HEADER_PATTERNS:
                if pattern.search(keyword):
                    fh = FitsHeader()
                    fh.galaxy_id = self._galaxy.galaxy_id
                    fh.keyword = keyword
                    fh.value = header[keyword]
                    session.add(fh)

                    if keyword == 'RA_CENT':
                        self._galaxy.ra_cent = float(fh.value)
                    elif keyword == 'DEC_CENT':
                        self._galaxy.dec_cent = float(fh.value)

    def _update_current(self):
        """
        The current galaxy is current - mark all the others as npot
        """
        session.execute("update galaxy set current = false where name = '"+ self._registration.galaxy_name + "'")

## ######################################################################## ##
##
## Where it all starts
##
## ######################################################################## ##

# Normal operation
files_processed = 0
if args['register'] is None:
    FILES_TO_PROCESS = WG_THRESHOLD - count + WG_HIGH_WATER_MARK

    # Get registered FITS files and generate work units until we've refilled the queue to at least the high water mark
    while files_processed < FILES_TO_PROCESS:
        LOG.info("Added %d of %d", files_processed, FILES_TO_PROCESS)
        registration = session.query(Register).filter(Register.create_time == None).order_by(desc(Register.priority), Register.register_time).first()
        if registration is None:
            LOG.info('No registrations waiting')
            break
        else:
            if os.path.isfile(registration.filename):
                LOG.info('Processing %s %d', registration.galaxy_name, registration.priority)
                fit2wu = Fit2Wu()
                (work_units_added, pixel_count) = fit2wu.process_file(registration)
                # One WU = MIN_QUORUM Results
                files_processed += (work_units_added * MIN_QUORUM)
                os.remove(registration.filename)
                registration.create_time = datetime.now()
            else:
                LOG.error('The file %s does not exist', registration.filename)
                registration.create_time = datetime.now()

            session.commit()

# We want an explict galaxy to load
else:
    registration = session.query(Register).filter(and_(Register.register_id == args['register'], Register.create_time == None)).first()
    if registration is None:
        LOG.info('No registration waiting with the id %d', args['register'])
    else:
        if os.path.isfile(registration.filename):
            LOG.info('Processing %s %d', registration.galaxy_name, registration.priority)
            fit2wu = Fit2Wu()
            (work_units_added, pixel_count) = fit2wu.process_file(registration)
            files_processed = work_units_added * MIN_QUORUM
            os.remove(registration.filename)
            registration.create_time = datetime.now()
        else:
            LOG.error('The file %s does not exist', registration.filename)
            registration.create_time = datetime.now()

        session.commit()

LOG.info('Done - added %d Results', files_processed)
