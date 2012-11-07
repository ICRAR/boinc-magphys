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
import logging
import os
import json
import shutil
import math
import pyfits
import subprocess

from datetime import datetime
from sqlalchemy.sql.expression import select, func
from config import WG_MIN_PIXELS_PER_FILE, WG_ROW_HEIGHT, WG_IMAGE_DIRECTORY, WG_BOINC_PROJECT_ROOT
from database.database_support_core import GALAXY, REGISTER, AREA, PIXEL_RESULT, FILTER, RUN_FILTER, RUN_FILE, FITS_HEADER
from image.fitsimage import FitsImage
from work_generation import HEADER_PATTERNS, STAR_FORMATION_FILE, INFRARED_FILE

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

APP_NAME = 'magphys_wrapper'
BIN_PATH = WG_BOINC_PROJECT_ROOT + '/bin'
TEMPLATES_PATH1 = 'templates'                                          # In true BOINC style, this is magically relative to the project root
TEMPLATES_PATH2 = '/home/ec2-user/boinc-magphys/server/runs'           # Where the Server code is
MIN_QUORUM = 2                                                         # Validator run when there are at least this many results for a work unit
TARGET_NRESULTS = MIN_QUORUM                                           # Initially create this many instances of a work unit
DELAY_BOUND = 86400 * 5                                                # Clients must report results within 5 days
FPOPS_EST_PER_PIXEL = 6                                                # Estimated number of gigaflops per pixel
FPOPS_BOUND_PER_PIXEL = FPOPS_EST_PER_PIXEL*50                         # Maximum number of gigaflops per pixel client will allow before terminating job
FPOPS_EXP = "e12"
COBBLESTONE_SCALING_FACTOR = 8.85

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

class Fit2Wu:
    """
    Convert a fit file to a wu
    """
    def __init__(self, connection, limit):
        self._pixel_count = 0
        self._work_units_added = 0
        self._signal_noise_hdu = None
        self._connection = connection
        self._limit = limit

    def process_file(self, registration):
        """
        Process a registration.
        """
        self._registration = registration

        # Have we files that we can use for this?
        self._rounded_redshift = self._get_rounded_redshift()
        if self._rounded_redshift is None:
            LOG.error('No models matching the redshift of %.4f', registration.redshift)
            return 0

        self._hdu_list = pyfits.open(registration.filename, memmap=True)
        self._layer_count = len(self._hdu_list)

        # Do we need to open and sort the S/N Ratio file
        if registration.sigma_filename is not None:
            self._sigma = 0.0
            self._signal_noise_hdu = pyfits.open(registration.sigma_filename, memmap=True)
            if self._layer_count != len(self._signal_noise_hdu):
                LOG.error('The layer counts do not match %d vs %d', self._layer_count, len(self._signal_noise_hdu))
                return 0, 0
        else:
            self._sigma = float(registration.sigma)

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
        datetime_now = datetime.now()
        result = self._connection.execute(GALAXY.insert().values(name = registration[REGISTER.c.galaxy_name],
             dimension_x = self._end_x,
             dimension_y = self._end_y,
             dimension_z = self._layer_count,
             redshift = registration[REGISTER.c.redshift],
             sigma = registration[REGISTER.c.sigma],
             create_time = datetime_now,
             image_time = datetime_now,
             version_number = version_number,
             galaxy_type = registration[REGISTER.c.galaxy_type],
             ra_cent = 0,
             dec_cent = 0,
             current = True,
             pixel_count = 0,
             pixels_processed = 0,
             run_id = registration[REGISTER.c.run_id]))
        self._galaxy_id = result.inserted_primary_key
        self._galaxy_name = registration[REGISTER.c.galaxy_name]
        LOG.info("Writing %s to database", self._galaxy_name)

        # Store the fits header
        self._store_fits_header()

        # Get the filters we're using for this run and sort the layers
        self._get_filters_sort_layers()

        # Build the template file we need if necessary
        self._build_template_file()

        # Now break up the galaxy into chunks
        self._break_up_galaxy()
        self._connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == self._galaxy_id).values(pixel_count = self._pixel_count))

        LOG.info('Building the images')
        image = FitsImage(self._connection)
        image.buildImage(registration.filename, WG_IMAGE_DIRECTORY, filePrefixName, False, self._galaxy_id)

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
        self._template_file = '{0}/{1:=04d}/fitsed_wu_{2}.xml'.format(TEMPLATES_PATH2, self._registration.run_id, self._rounded_redshift)
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
    </file_info>
    <file_info>
        <number>3</number>
    </file_info>
    <file_info>
        <number>4</number>
        <sticky/>
        <url>{1}</url>
        <md5_cksum>{2}</md5_cksum>
        <nbytes>{3}</nbytes>
    </file_info>
    <file_info>
        <number>5</number>
        <sticky/>
        <url>{4}</url>
        <md5_cksum>{5}</md5_cksum>
        <nbytes>{6}</nbytes>
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
</input_template>'''.format(self._rounded_redshift, star_formation.file_name, star_formation.md5_hash, star_formation.size, infrared.file_name, infrared.md5_hash, infrared.size))
            file.close()

    def _create_areas(self, pix_y):
        """
        Create a area - we try to make them squares, but they aren't as the images have dead zones
        """
        area_insert = AREA.insert()
        pixel_result_insert = PIXEL_RESULT.insert()
        pix_x = 0
        while pix_x < self._end_x:
            # Are we limiting the number created
            if self._limit is not None and self._work_units_added > self._limit:
                break

            max_x, pixels = self._get_pixels(pix_x, pix_y)
            if len(pixels) > 0:
                area = Area(pix_x, pix_y, max_x, min(pix_y + WG_ROW_HEIGHT, self._end_y))
                result1 = self._connection.execute(area_insert.values(galaxy_id = self._galaxy_id,
                    top_x = area.top_x,
                    top_y = area.top_y,
                    bottom_x = area.bottom_x,
                    bottom_y = area.bottom_y))
                area.area_id = result1.inserted_primary_key

                for pixel in pixels:
                    result2 = self._connection.execute(pixel_result_insert.values(galaxy_id = self._galaxy_id,
                        area_id = area.area_id,
                        y = pixel.y,
                        x = pixel.x))

                    pixel.pixel_id = result2.inserted_primary_key
                    self._pixel_count += 1

                # Write the pixels
                self._create_output_file(area, pixels)
                self._work_units_added += 1

            pix_x = max_x + 1

    def _create_filters_dat(self, file_name_filters):
        source = '{0}/{1:=04d}/filters.dat'.format(TEMPLATES_PATH2, self._registration.run_id)
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

    def _create_model_files(self, file_name_star_formation_history, file_name_infrared):
        """
        Create dummy model files
        """
        new_full_path = subprocess.check_output([BIN_PATH + '/dir_hier_path', file_name_star_formation_history]).rstrip()
        file = open(new_full_path, 'wb')
        file.write(' 1  {0}'.format(self._rounded_redshift))
        file.close()

        new_full_path = subprocess.check_output([BIN_PATH + '/dir_hier_path', file_name_infrared]).rstrip()
        file = open(new_full_path, 'wb')
        file.write(' 1  {0}'.format(self._rounded_redshift))
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
            outfile.write('pix%(id)s %(pixel_redshift)s ' % {'id':pixel.pixel_id, 'pixel_redshift':self._registration[REGISTER.c.redshift]})
            for pixel_value in pixel.pixels:
                outfile.write("{0}  {1}  ".format(pixel_value.value, pixel_value.sigma))

            outfile.write('\n')
            row_num += 1
        outfile.close()

    def _create_output_file(self, area, pixels):
        """
        Write an output file for this area
        """
        pixels_in_area = len(pixels)
        filename = '%(galaxy)s_area%(area)s' % { 'galaxy':self._galaxy_name, 'area':area.area_id}
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
        data = [{'galaxy':self._galaxy_name, 'area_id':area.area_id, 'pixels':pixels_in_area, 'top_x':area.top_x, 'top_y':area.top_y, 'bottom_x':area.bottom_x, 'bottom_y':area.bottom_y,}]
        self._create_observation_file(filename, data, pixels)
        self._create_job_xml(file_name_job, pixels_in_area)
        self._create_filters_dat(file_name_filters)
        self._create_zlib_dat(file_name_zlib)
        self._create_model_files(file_name_star_formation_history, file_name_infrared)

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
        for filter in self._connection.execute(select([FILTER.c.name], from_obj=FILTER.join(RUN_FILTER, RUN_FILTER.c.run_id == self._registration[REGISTER.c.run_id])).order_by(FILTER.c.eff_lambda)):
            list_filter_names.append(filter)

        # The order of the filters will be there order in the fits file so record the name and its position
        names = []
        for layer in range(self._layer_count):
            hdu = self._hdu_list[layer]
            filter_name = hdu.header['MAGPHYSN']
            if filter_name is None:
                raise LookupError('The layer {0} does not have MAGPHYSN in it'.format(layer))
            names.append(filter_name)

            found_filter = False
            for filter in list_filter_names:
                if filter_name == filter:
                    found_filter = True
                    break

            if not found_filter:
                raise LookupError('The filter {0} in the fits file is not expected'.format(filter_name))

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
        for filter in list_filter_names:
            found_it = False
            for i in range(len(names)):
                if names[i] == filter:
                    layers.append(i)
                    if filter.infrared == 1:
                        self._infrared_bands[filter] = i

                    if filter.optical == 1:
                        self._optical_bands[filter] = i

                    if filter.ultraviolet == 1:
                        self._ultraviolet_bands[filter] = i
                    found_it = True
                    break

            if not found_it:
                layers.append(-1)

        self._layer_order = layers

    def _get_model_files(self):
        """
        Get the two model files we need
        """
        star_formation = None
        infrared = None
        for run_file in self._connection.execute(select([RUN_FILE]).where(RUN_FILE.c.run_id == self._registration[REGISTER.c.run_id]).filter(RUN_FILE.c.redshift == self._rounded_redshift)):
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
        star_formation_history = '{0:=04d}_starformhist_cb07_z{1}.lbr'.format(self._registration.run_id, self._rounded_redshift)
        infrared =  '{0:=04d}_infrared_dce08_z{1}.lbr'.format(self._registration.run_id, self._rounded_redshift)
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
                        pixels.append(PixelValue(0,0))
                    else:
                        # A vagary of PyFits/NumPy is the order of the x & y indexes is reversed
                        # See page 13 of the PyFITS User Guide
                        pixel = self._hdu_list[layer].data[y, x]
                        if math.isnan(pixel) or pixel == 0.0:
                            # A zero tells MAGPHYS - we have no value here
                            pixels.append(PixelValue(0,0))
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
        count = self._connection.execute(select([func.count(GALAXY.c.galaxy_id)]).where(GALAXY.c.name == self._registration[REGISTER.c.galaxy_name])).first()
        return count[0] + 1

    def _store_fits_header(self):
        """
        Store the FITS headers we need to remember
        """
        insert = FITS_HEADER.insert()
        header = self._hdu_list[0].header
        for keyword in header:
            for pattern in HEADER_PATTERNS:
                if pattern.search(keyword):
                    value = header[keyword]
                    LOG.info('{0} {1} {2} {3]'.format(self._galaxy_id, keyword, value, insert.values(galaxy_id = self._galaxy_id, keyword = keyword, value = value)))
                    self._connection.execute(insert.values(galaxy_id = self._galaxy_id, keyword = keyword, value = value))

                    if keyword == 'RA_CENT':
                        self._connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == self._galaxy_id).values(ra_cent = float(value)))
                    elif keyword == 'DEC_CENT':
                        self._connection.execute(GALAXY.update().where(GALAXY.c.galaxy_id == self._galaxy_id).values(dec_cent = float(value)))

    def _update_current(self):
        """
        The current galaxy is current - mark all the others as npot
        """
        self._connection.execute(GALAXY.update().where(GALAXY.c.name == self._registration[REGISTER.c.galaxy_name]).values(current = False))
