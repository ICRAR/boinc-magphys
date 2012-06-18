import sys
import os
from subprocess import call
from subprocess import check_output

if(len(sys.argv) != 3):
	print "usage:   %(me)s observations_directory boinc_project_root" % {'me':sys.argv[0]}
	print "example: %(me)s /home/ec2-user/f2wu /home/ec2-user/projects/pogs" % {'me':sys.argv[0]}
	sys.exit(-10)

APP_NAME = "magphys_wrapper"
FILE_DIR = sys.argv[1]
BOINC_PROJECT_ROOT = sys.argv[2]
BIN_PATH = BOINC_PROJECT_ROOT + "/bin"
TEMPLATES_PATH = "templates" # In true BOINC style, this is magically relative to the project root

FPOPS_EXP = "e9"
FPOPS_EST_PER_PIXEL = 650						# Estimated number of gigaflops per pixel 
FPOPS_BOUND_PER_PIXEL = FPOPS_EST_PER_PIXEL*15	# Maximum number of gigaflops per pixel client will allow before terminating job

# The BOINC scripts/apps do not feel at home outside their directory
os.chdir(BOINC_PROJECT_ROOT)

file_list = os.listdir(FILE_DIR);

for file_name in file_list:
	if file_name[0] == '.': continue	# Process everything but dot-files

	pixels_in_file = sum(1 for line in open(FILE_DIR + "/" + file_name))-1
	print("Creating work unit from observations file %(file)s: %(pixels)d pixels" % {'file':file_name, 'pixels':pixels_in_file})

	new_full_path = check_output([BIN_PATH + "/dir_hier_path", file_name]).rstrip()	
	os.rename(FILE_DIR + "/" + file_name, new_full_path)

	cmd_create_work = [
		BIN_PATH + "/create_work",
		"--appname",         APP_NAME,
		"--wu_name",         file_name,
		"--wu_template",     TEMPLATES_PATH + "/fitsed_wu",
		"--result_template", TEMPLATES_PATH + "/fitsed_result",
		"--rsc_fpops_est",   "%(est)d%(exp)s" % {'est':FPOPS_EST_PER_PIXEL*pixels_in_file, 'exp':FPOPS_EXP},
		"--rsc_fpops_bound", "%(bound)d%(exp)s"  % {'bound':FPOPS_BOUND_PER_PIXEL*pixels_in_file, 'exp':FPOPS_EXP},
		file_name,
		"filter_spec.dat", "zlibs.dat", "infrared_dce08_z0.0000.lbr", "starformhist_cb07_z0.0000.lbr"		
	]
	
	if call(cmd_create_work):
		print "Something went wrong; sorry"
