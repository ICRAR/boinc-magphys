#! /usr/bin/env python2.7
"""
Convert observations into WU
"""
import argparse
import json
import logging
import shutil
import sys
import os
import subprocess
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from config import boinc_db_login
from database.boinc_database_support import Result
from utils.readable_dir import ReadableDir
from utils.writeable_dir import WriteableDir

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser()
parser.add_argument('observations_directory', action=ReadableDir, nargs=1, help='where observation files will be read from')
parser.add_argument('boinc_project_root', action=WriteableDir, nargs=1, help='where the WU will be written too')
parser.add_argument('-fp', '--files_to_process', type=int, help='the number of files to process')
parser.add_argument('-p', '--priority', type=int, help='the priority of the WUs')
parser.add_argument('-t', '--threshold', type=int, help='if the number is less than this threshold add records')
args = vars(parser.parse_args())

# A single WU will generate 2 results so 1500 WU adds 3000 pending results
HIGH_WATER_MARK = 1500

# Do we need to run this
if args['threshold'] is not None:
    # select count(*) from result where server_state = 2
    engine = create_engine(boinc_db_login)
    Session = sessionmaker(bind=engine)
    session = Session()
    count = session.query(Result).filter(Result.server_state == 2).count()
    session.close()

    if args['files_to_process'] is None:
        LOG.info('Checking pending = %d : threshold = %d', count, args['threshold'])
    else:
        LOG.info('Checking pending = %d : threshold = %d : files = %d', count, args['threshold'], args['files_to_process'])

    if count >= args['threshold']:
        LOG.info('Nothing to do')
        exit(0)

    if args['files_to_process'] is None:
        args['files_to_process'] = args['threshold'] - count + HIGH_WATER_MARK

APP_NAME = "magphys_wrapper"
FILE_DIR = args['observations_directory']
BOINC_PROJECT_ROOT = args['boinc_project_root']
if args['files_to_process'] is not None:
    FILES_TO_PROCESS = args['files_to_process']
else:
    FILES_TO_PROCESS = sys.maxint

LOG.info('Files to process %d', FILES_TO_PROCESS)

BIN_PATH = BOINC_PROJECT_ROOT + "/bin"
TEMPLATES_PATH = "templates"                    # In true BOINC style, this is magically relative to the project root

MIN_QUORUM = 2									# Validator run when there are at least this many results for a work unit
TARGET_NRESULTS = MIN_QUORUM 					# Initially create this many instances of a work unit
DELAY_BOUND = 86400 * 7 						# Clients must report results within a week
FPOPS_EST_PER_PIXEL = 3.312						# Estimated number of gigaflops per pixel
FPOPS_BOUND_PER_PIXEL = FPOPS_EST_PER_PIXEL*15	# Maximum number of gigaflops per pixel client will allow before terminating job
FPOPS_EXP = "e12"
COBBLESTONE_SCALING_FACTOR = 8.6

# The BOINC scripts/apps do not feel at home outside their directory
os.chdir(BOINC_PROJECT_ROOT)

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

def file_details(filename):
    f = open(filename, 'rb')
    line = f.readline()
    f.close()
    list = json.loads(line[1:])
    data = list[0]

    return data['pixels'], data['area_id']

files_processed = 0
for file_name in sorted(os.listdir(FILE_DIR)):
    # Create the job file
    file_name_job = file_name + '.job.xml'

    pixels_in_file, area_id = file_details(FILE_DIR + "/" + file_name)
    LOG.info("Creating work unit from observations file %(file)s: %(pixels)d pixels " % {'file':file_name, 'pixels':pixels_in_file})

    args_params = [
        "--appname",         APP_NAME,
        "--min_quorum",      "%(min_quorum)s" % {'min_quorum':MIN_QUORUM},
        "--max_success_results", "4",
        "--delay_bound",     "%(delay_bound)s" % {'delay_bound':DELAY_BOUND},
        "--target_nresults", "%(target_nresults)s" % {'target_nresults':TARGET_NRESULTS},
        "--wu_name",         file_name,
        "--wu_template",     TEMPLATES_PATH + "/fitsed_wu.xml",
        "--result_template", TEMPLATES_PATH + "/fitsed_result.xml",
        "--rsc_fpops_est",   "%(est)d%(exp)s" % {'est':FPOPS_EST_PER_PIXEL*pixels_in_file, 'exp':FPOPS_EXP},
        "--rsc_fpops_bound", "%(bound)d%(exp)s"  % {'bound':FPOPS_BOUND_PER_PIXEL*pixels_in_file, 'exp':FPOPS_EXP},
        "--rsc_memory_bound", "1e8",
        "--rsc_disk_bound", "5e8",
        "--additional_xml", "<credit>%(credit).03f</credit>" % {'credit':pixels_in_file*COBBLESTONE_SCALING_FACTOR},
        "--opaque",   str(area_id)
    ]
    args_files = [file_name, file_name_job]
    cmd_create_work = [
        BIN_PATH + "/create_work"
    ]
    cmd_create_work.extend(args_params)

    if args['priority'] is not None:
        cmd_create_work.extend(["--priority", args['priority']])

    cmd_create_work.extend(args_files)

    # Copy file into BOINC's download hierarchy
    new_full_path = subprocess.check_output([BIN_PATH + "/dir_hier_path", file_name]).rstrip()
    shutil.move(FILE_DIR + "/" + file_name, new_full_path)

    create_job_xml(file_name_job, pixels_in_file)

    # And "create work" = create the work unit
    if subprocess.call(cmd_create_work):
        LOG.error("Something went wrong; sorry")

    files_processed += 1

    if files_processed >= FILES_TO_PROCESS:
        break

LOG.info('Added %d files', files_processed)
