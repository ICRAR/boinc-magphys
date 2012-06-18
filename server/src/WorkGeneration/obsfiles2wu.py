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

exp = "e9"
FPOPS_EST_PER_PIXEL = 650						# Estimated number of gigaflops per pixel 
FPOPS_BOUND_PER_PIXEL = FPOPS_EST_PER_PIXEL*15	# Maximum number of gigaflops per pixel client will allow before terminating job

# The BOINC scripts/apps do not feel at home outside their directory
os.chdir(BOINC_PROJECT_ROOT)

file_list = os.listdir(FILE_DIR);

for file in file_list:
	if file[0] == '.': continue	# Process everything but dot-files

	## TODO
	## TODO: open file, count lines and calculate totel est/bounc FLOPS
	## TODO

	new_full_path = check_output([BIN_PATH + "/dir_hier_path", file]).rstrip()
	
	print("Creating work unit from observations file %(file)s" % {'file':file})
	os.rename(FILE_DIR + "/" + file, new_full_path)

	cmd_create_work = [
		BIN_PATH + "/create_work",
		"--appname",         APP_NAME,
		"--wu_name",         file,
		"--wu_template",     TEMPLATES_PATH + "/fitsed_wu",
		"--result_template", TEMPLATES_PATH + "/fitsed_result",
		"--rsc_fpops_est",   FPOPS_EST_PER_PIXEL + FPOPS_EXP,
		"--rsc_fpops_bound", FPOPS_BOUND_PER_PIXEL + FPOPS_EXP,
		file,
		"filter_spec.dat", "zlibs.dat", "infrared_dce08_z0.0000.lbr", "starformhist_cb07_z0.0000.lbr"		
	]
	
	if call(cmd_create_work):
		print "Something went wrong; sorry"
