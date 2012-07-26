import logging
import sys
import os
import subprocess

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

if len(sys.argv) != 3 and len(sys.argv) != 4:
    print "usage:   %(me)s observations_directory boinc_project_root [files_to_process]" % {'me':sys.argv[0]}
    print "example: %(me)s /home/ec2-user/f2wu /home/ec2-user/projects/pogs 100" % {'me':sys.argv[0]}
    sys.exit(-10)

APP_NAME = "magphys_wrapper"
FILE_DIR = sys.argv[1]
BOINC_PROJECT_ROOT = sys.argv[2]
if len(sys.argv) == 4:
    FILES_TO_PROCESS = sys.argv[3]
else:
    FILES_TO_PROCESS = sys.maxint

BIN_PATH = BOINC_PROJECT_ROOT + "/bin"
TEMPLATES_PATH = "templates"                      # In true BOINC style, this is magically relative to the project root

NUMBER_OF_HIGH_PRIO_WORK_UNITS = 100			  # Default number of work units to mark as high priority
DEFAULT_HIGH_PRIORITY = "100"
MIN_QUORUM = 2									  # Validator run when there are at least this many results for a work unit
TARGET_NRESULTS = MIN_QUORUM+1					  # Initially create this many instances of a work unit
DELAY_BOUND = 86400 * 30 						  # Clients must report results within a month
FPOPS_EST_PER_PIXEL = 1.898						  # Estimated number of gigaflops per pixel
FPOPS_BOUND_PER_PIXEL = FPOPS_EST_PER_PIXEL*15	  # Maximum number of gigaflops per pixel client will allow before terminating job
FPOPS_EXP = "e12"

# The BOINC scripts/apps do not feel at home outside their directory
os.chdir(BOINC_PROJECT_ROOT)
file_list = os.listdir(FILE_DIR)

def create_job_xml(file_name, pixels_in_file):
    new_full_path = subprocess.check_output([BIN_PATH + "/dir_hier_path", file_name]).rstrip()
    file = open(new_full_path, 'wb')
    file.write('<job_desc>\n')
    for i in range(1, pixels_in_file):
        file.write('''   <task>
      <application>fit_sed</application>
      <command_line>{0} filters.dat observations.dat</command_line>
      <stdout_filename>stdout_file</stdout_filename>
      <stderr_filename>stderr_file</stderr_filename>
   </task>
'''.format(i))
    file.write('</job_desc>\n')
    file.close()

files_processed = 0
for file_name in file_list:
    if file_name[0] == '.':
        continue	# Process everything but dot-files

    # Create the job file
    file_name_job = file_name + '.job.xml'

    pixels_in_file = sum(1 for line in open(FILE_DIR + "/" + file_name))-1
    LOG.info("Creating work unit from observations file %(file)s: %(pixels)d pixels" % {'file':file_name, 'pixels':pixels_in_file})

    args_params = [
        "--appname",         APP_NAME,
        "--min_quorum",      "%(min_quorum)s" % {'min_quorum':MIN_QUORUM},
        "--delay_bound",     "%(delay_bound)s" % {'delay_bound':DELAY_BOUND},
        "--target_nresults", "%(target_nresults)s" % {'target_nresults':TARGET_NRESULTS},
        "--wu_name",         file_name,
        "--wu_template",     TEMPLATES_PATH + "/fitsed_wu.xml",
        "--result_template", TEMPLATES_PATH + "/fitsed_result.xml",
        "--rsc_fpops_est",   "%(est)d%(exp)s" % {'est':FPOPS_EST_PER_PIXEL*pixels_in_file, 'exp':FPOPS_EXP},
        "--rsc_fpops_bound", "%(bound)d%(exp)s"  % {'bound':FPOPS_BOUND_PER_PIXEL*pixels_in_file, 'exp':FPOPS_EXP},
        "--additional_xml", "<credit>%(pixels)d</credit>" % {'pixels':pixels_in_file},
    ]
    args_files = [file_name, file_name_job]

    cmd_create_work = [
        BIN_PATH + "/create_work"
    ]
    cmd_create_work.extend(args_params)
    if files_processed <= NUMBER_OF_HIGH_PRIO_WORK_UNITS:
        cmd_create_work.extend(["--priority", DEFAULT_HIGH_PRIORITY])
    cmd_create_work.extend(args_files)

    # Copy file into BOINC's download hierarchy
    new_full_path = subprocess.check_output([BIN_PATH + "/dir_hier_path", file_name]).rstrip()
    os.rename(FILE_DIR + "/" + file_name, new_full_path)

    create_job_xml(file_name_job, pixels_in_file)

    # And "create work" = create the work unit
    if subprocess.call(cmd_create_work):
        LOG.error("Something went wrong; sorry")

    files_processed += 1

    if files_processed >= FILES_TO_PROCESS:
        break
