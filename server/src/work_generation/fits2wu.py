#! /usr/bin/env python2.7
"""
Convert a FITS file ready to be converted into Work Units
"""
from __future__ import print_function
from datetime import datetime

import logging
import os
import re
import json
import shutil
import math
import pyfits

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import desc
import sys
import subprocess
from config import boinc_db_login, wg_threshold, wg_high_water_mark, db_login, wg_sigma, wg_min_pixels_per_file, wg_row_height, wg_image_directory, wg_boinc_project_root
from database.boinc_database_support import Result
from database.database_support import Register, FitsHeader, Galaxy, Area, PixelResult
from image.fitsimage import FitsImage
from work_generation import FILTER_BANDS, ULTRAVIOLET_BANDS, OPTICAL_BANDS, INFRARED_BANDS

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

# select count(*) from result where server_state = 2
engine = create_engine(boinc_db_login)
Session = sessionmaker(bind=engine)
session = Session()
count = session.query(Result).filter(Result.server_state == 2).count()
session.close()

LOG.info('Checking pending = %d : threshold = %d', count, wg_threshold)

if count >= wg_threshold:
    LOG.info('Nothing to do')
    exit(0)

# Constants need
HEADER_PATTERNS = [re.compile('CDELT[0-9]+'),
                   re.compile('CROTA[0-9]+'),
                   re.compile('CRPIX[0-9]+'),
                   re.compile('CRVAL[0-9]+'),
                   re.compile('CTYPE[0-9]+'),
                   re.compile('EQUINOX'),
                   re.compile('EPOCH'),
                   re.compile('RA_CENT'),
                   re.compile('DEC_CENT'),
                   ]
APP_NAME = "magphys_wrapper"
BIN_PATH = wg_boinc_project_root + "/bin"
TEMPLATES_PATH = "templates"                    # In true BOINC style, this is magically relative to the project root
MIN_QUORUM = 2									# Validator run when there are at least this many results for a work unit
TARGET_NRESULTS = MIN_QUORUM 					# Initially create this many instances of a work unit
DELAY_BOUND = 86400 * 7 						# Clients must report results within a week
FPOPS_EST_PER_PIXEL = 3.312						# Estimated number of gigaflops per pixel
FPOPS_BOUND_PER_PIXEL = FPOPS_EST_PER_PIXEL*15	# Maximum number of gigaflops per pixel client will allow before terminating job
FPOPS_EXP = "e12"
COBBLESTONE_SCALING_FACTOR = 8.6

# The BOINC scripts/apps do not feel at home outside their directory
os.chdir(wg_boinc_project_root)

# Connect to the database - the login string is set in the database package
engine = create_engine(db_login)
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

class Status:
    """
    The status of the run
    """
    def __init__(self):
        self.pixel_count = 0
        self.work_units_added = 0

def store_fits_header(hdu_list, galaxy, galaxy_id):
    """
    Store the FITS headers we need to remember
    """
    header = hdu_list[0].header
    for keyword in header:
        for pattern in HEADER_PATTERNS:
            if pattern.search(keyword):
                fh = FitsHeader()
                fh.galaxy_id = galaxy_id
                fh.keyword = keyword
                fh.value = header[keyword]
                session.add(fh)

                if keyword == 'RA_CENT':
                    galaxy.ra_cent = float(fh.value)
                elif keyword == 'DEC_CENT':
                    galaxy.dec_cent = float(fh.value)

def sort_layers(hdu_list, layer_count):
    """
    Look at the layers of a HDU and order them based on the effective wavelength stored in the header
    """
    names = []
    for layer in range(layer_count):
        hdu = hdu_list[layer]
        filter_name = hdu.header['MAGPHYSN']
        if filter_name is None:
            raise LookupError('The layer {0} does not have MAGPHYSN in it'.format(layer))
        names.append(filter_name)

        found_filter = False
        for name in FILTER_BANDS:
            if filter_name == name:
                found_filter = True
                break

        if not found_filter:
            raise LookupError('The filter {0} in the fits file is not expected'.format(filter_name))

    layers = []
    for filter_name in FILTER_BANDS:
        found_it = False
        for i in range(len(names)):
            if names[i] == filter_name:
                layers.append(i)
                found_it = True
                break
        if not found_it:
            layers.append(-1)

    return layers

def create_job_xml(file_name, pixels_in_file):
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

def create_observation_file(filename, data, galaxy, pixels):
    new_full_path = subprocess.check_output([BIN_PATH + "/dir_hier_path", filename]).rstrip()
    outfile = open(new_full_path, 'w')
    outfile.write('#  %(data)s\n' % { 'data': json.dumps(data) })

    row_num = 0
    for pixel in pixels:
        outfile.write('pix%(id)s %(pixel_redshift)s ' % {'id':pixel.pixel_id, 'pixel_redshift':galaxy.redshift})
        for value in pixel.pixels:
            outfile.write("{0}  {1}  ".format(value, value * wg_sigma))

        outfile.write('\n')
        row_num += 1
    outfile.close()

def create_output_file(galaxy, area, pixels, priority):
    """
        Write an output file for this area
    """
    pixels_in_area = len(pixels)
    data = [{'galaxy':galaxy.name, 'area_id':area.area_id, 'pixels':pixels_in_area, 'top_x':area.top_x, 'top_y':area.top_y, 'bottom_x':area.bottom_x, 'bottom_y':area.bottom_y,}]
    filename = '%(galaxy)s_area%(area)s' % { 'galaxy':galaxy.name, 'area':area.area_id}
    file_name_job = filename + '.job.xml'
    LOG.info("Creating work unit %s : %d pixels ", filename, pixels_in_area)

    args_params = [
        "--appname",         APP_NAME,
        "--min_quorum",      "%(min_quorum)s" % {'min_quorum':MIN_QUORUM},
        "--max_success_results", "4",
        "--delay_bound",     "%(delay_bound)s" % {'delay_bound':DELAY_BOUND},
        "--target_nresults", "%(target_nresults)s" % {'target_nresults':TARGET_NRESULTS},
        "--wu_name",         filename,
        "--wu_template",     TEMPLATES_PATH + "/fitsed_wu.xml",
        "--result_template", TEMPLATES_PATH + "/fitsed_result.xml",
        "--rsc_fpops_est",   "%(est)d%(exp)s" % {'est':FPOPS_EST_PER_PIXEL*pixels_in_area, 'exp':FPOPS_EXP},
        "--rsc_fpops_bound", "%(bound)d%(exp)s"  % {'bound':FPOPS_BOUND_PER_PIXEL*pixels_in_area, 'exp':FPOPS_EXP},
        "--rsc_memory_bound", "1e8",
        "--rsc_disk_bound", "5e8",
        "--additional_xml", "<credit>%(credit).03f</credit>" % {'credit':pixels_in_area*COBBLESTONE_SCALING_FACTOR},
        "--opaque",   str(area.area_id),
        "--priority", '{0}'.format(priority)
    ]
    args_files = [filename, file_name_job]
    cmd_create_work = [
        BIN_PATH + "/create_work"
    ]
    cmd_create_work.extend(args_params)
    cmd_create_work.extend(args_files)

    # Copy files into BOINC's download hierarchy
    create_observation_file(filename, data, galaxy, pixels)
    create_job_xml(file_name_job, pixels_in_area)

    # And "create work" = create the work unit
    subprocess.call(cmd_create_work)

def enough_layers(pixels):
    """
        Are there enough layers with data in them to warrant counting this pixel?
    """
    uv_layers = 0
    for layer_id in ULTRAVIOLET_BANDS.values():
        if pixels[layer_id] > 0:
            uv_layers += 1

    optical_layers = 0
    for layer_id in OPTICAL_BANDS.values():
        if pixels[layer_id] > 0:
            optical_layers += 1

    ir_layers = 0
    for layer_id in INFRARED_BANDS.values():
        if pixels[layer_id] > 0:
            ir_layers += 1

    if optical_layers >= 4:
        return True

    if optical_layers == 3 and (uv_layers >= 1 or ir_layers >= 1):
        return True

    # Not enough layers
    return False

def get_pixels(hdu_list, pix_x, pix_y, end_x, end_y, layer_order):
    """
        Retrieves pixels from each pair of (x, y) coordinates specified in pix_x and pix_y.
        Returns pixels only from those coordinates where there is data in more than
        MIN_LIVE_CHANNELS_PER_PIXEL channels. Pixels are retrieved in the order specified in
        the global LAYER_ORDER list.
    """
    result = []
    max_x = pix_x
    x = pix_x
    while x < end_x:
        for y in range(pix_y, pix_y + wg_row_height):
            # Have we moved off the edge
            if y >= end_y:
                continue

            pixels = []
            for layer in layer_order:
                if layer == -1:
                    # The layer is missing
                    pixels.append(0)
                else:
                    # A vagary of PyFits/NumPy is the order of the x & y indexes is reversed
                    # See page 13 of the PyFITS User Guide
                    pixel = hdu_list[layer].data[y, x]
                    if math.isnan(pixel) or pixel == 0.0:
                        # A zero tells MAGPHYS - we have no value here
                        pixels.append(0)
                    else:
                        pixels.append(pixel)

            if enough_layers(pixels):
                result.append(Pixel(x, y, pixels))

        max_x = x
        if len(result) > wg_min_pixels_per_file:
            break

        x += 1

    return max_x, result

def create_areas(status, galaxy, hdu_list, pix_y, end_x, end_y, layer_order, priority):
    """
    Create a area - we try to make them squares, but they aren't as the images have dead zones
    """
    pix_x = 0
    while pix_x < end_x:
        max_x, pixels = get_pixels(hdu_list, pix_x, pix_y, end_x, end_y, layer_order)
        if len(pixels) > 0:
            area = Area()
            area.galaxy_id = galaxy.galaxy_id
            area.top_x = pix_x
            area.top_y = pix_y
            area.bottom_x = max_x
            area.bottom_y = min(pix_y + wg_row_height, end_y)
            session.add(area)
            session.flush()

            for pixel in pixels:
                pixel_result = PixelResult()
                pixel_result.galaxy_id = galaxy.galaxy_id
                pixel_result.area_id = area.area_id
                pixel_result.x = pixel.x
                pixel_result.y = pixel.y
                session.add(pixel_result)
                session.flush()

                pixel.pixel_id = pixel_result.pxresult_id
                status.pixel_count += 1

            # Write the pixels
            create_output_file(galaxy, area, pixels, priority)
            status.work_units_added += 1

        pix_x = max_x + 1

def break_up_galaxy(galaxy, hdu_list, end_x, end_y, layer_order, priority):
    status = Status()
    start_y = 0
    for pix_y in range(start_y, end_y, wg_row_height):
        str = "Scanned %(pct_done)3d%% of image" % { 'pct_done':100*(pix_y-start_y)/(end_y-start_y) }
        print(str, end="\r")
        sys.stdout.flush()
        create_areas(status, galaxy, hdu_list, pix_y, end_x, end_y, layer_order, priority)

    return status

def get_version_number(galaxy_name):
    count = session.query(Galaxy).filter(Galaxy.name == galaxy_name).count()
    return count + 1

def update_current(galaxy_name):
    session.execute("update galaxy set current = false where name = '"+ galaxy_name + "'")

def process_file(register):
    hdu_list = pyfits.open(register.filename, memmap=True)
    layer_count = len(hdu_list)

    end_y = hdu_list[0].data.shape[0]
    end_x = hdu_list[0].data.shape[1]

    LOG.info("Image dimensions: %(x)d x %(y)d x %(z)d => %(pix).2f Mpixels" % {'x':end_x,'y':end_y,'z':layer_count,'pix':end_x*end_y/1000000.0})

    # Update the version number
    version_number = get_version_number(register.galaxy_name)
    if version_number > 1:
        update_current(register.galaxy_name)

    filePrefixName = register.galaxy_name + "_" + str(version_number)
    fitsFileName = filePrefixName + ".fits"

    # Create and save the object
    galaxy = Galaxy()
    galaxy.name = register.galaxy_name
    galaxy.dimension_x = end_x
    galaxy.dimension_y = end_y
    galaxy.dimension_z = layer_count
    galaxy.redshift = register.redshift
    datetime_now = datetime.now()
    galaxy.create_time = datetime_now
    galaxy.image_time = datetime_now
    galaxy.version_number = version_number
    galaxy.galaxy_type = register.galaxy_type
    galaxy.ra_cent = 0
    galaxy.dec_cent = 0
    galaxy.current = True
    galaxy.pixel_count = 0
    galaxy.pixels_processed = 0
    session.add(galaxy)

    # Flush to the DB so we can get the id
    session.flush()

    LOG.info("Wrote %(object)s to database" % { 'object':galaxy.name })

    # Store the fits header
    store_fits_header(hdu_list, galaxy, galaxy.galaxy_id)
    layer_order = sort_layers(hdu_list, layer_count)
    status = break_up_galaxy(galaxy, hdu_list, end_x, end_y, layer_order, register.priority)
    galaxy.pixel_count = status.pixel_count
    session.flush()

    LOG.info('Building the images')
    image = FitsImage()
    image.buildImage(register.filename, wg_image_directory, filePrefixName, "asinh", False, False, False)

    shutil.copyfile(register.filename, image.get_file_path(wg_image_directory, fitsFileName, True))

    return status

## ######################################################################## ##
##
## Where it all starts
##
## ######################################################################## ##

files_processed = 0
FILES_TO_PROCESS = wg_threshold - count + wg_high_water_mark

# Get registered FITS files and generate work units until we've refilled the queue to at least the high water mark
while files_processed < FILES_TO_PROCESS:
    register = session.query(Register).filter(Register.create_time == None).order_by(desc(Register.priority), Register.register_time).first()
    if register is None:
        LOG.info('No registrations waiting')
    elif os.path.exists(register.filename):
        LOG.info('Processing %s %d', register.galaxy_name, register.priority)
        status = process_file(register)
        files_processed += status.work_units_added
        os.remove(register.filename)
        register.create_time = datetime.now()
    else:
        LOG.error('The file %s does not exits', register.filename)
        register.create_time = datetime.now()

    session.commit()

LOG.info('Done - added %d WUs', files_processed)
