# Generation of work units: overview

# Prerequisites

* AWS running at least a small model - this uses more memory than a micro model provides
* MySQL locally installed
* Python >=2.7.1 (tested on Python 2.7.1 (r271:86832, Jun 16 2011, 16:59:05))

# New Method

A galaxy is registered ready for processing.
The registration says where the files are, names, red-shift, etc.
The WU generator takes a image and breaks in into WU and loads them into the BOINC server.

## Registering Runs

To avoid having to store 100's of MBs of model files on the server we do this in two stages

### Step 1  (Local machine)

$ ./create_file_details.py input_dir output_dir
$ ./create_file_details.py ~/boinc-magphys/runs/0001 ~/boinc-magphys/server/runs/0001

* **input_dir** where the *.lbr files are stored
* **output_dir** where the output file is written

### Step 2 (Boinc Server)

$ ./load_run_details.py run_id dir_with_files url_prefix comment
$ ./load_run_details.py 1 /home/ec2-user/boinc-magphys/server/runs/0001 http://boinc-download.icrar.org/runs/0001/ 'PS Filters + SDSSu' 6 8.85
$ ./load_run_details.py 2 /home/ec2-user/boinc-magphys/server/runs/0002 http://boinc-download.icrar.org/runs/0002/ 'SDSS Only' 5.5 8.85

* **run_id** is the run id to be used
* **dir_with_files** where the filters.dat and file_details.dat files can be found as we need to record the md5sum and size
* **url_prefix** the URL prefix to the files
* **comment** a description of the run
* **fpops_est** the GFlops est
* **cobblestone_factor** the cobblestone factor for this run

## Register Galaxy

$ ./register_fits_file.py Filename Redshift Galaxy Type Sigma Priority Run_id
$ ./register_fits_file.py /home/ec2-user/galaxies/POGS_IC0089.fits    0.0181  IC0089   S0     0.05    0  1
$ ./register_fits_file.py /home/ec2-user/galaxies/POGS_IC0089.fits    0.0181  IC0089   S0     /home/ec-user/galaxies/POGSNR_IC0089.fits    0  1

* **Filename** is the absolute path to the FITS file contain the image of the galaxy
* **Redshift** is the redshift of the Galaxy
* **Galaxy** is the name to be used for this galaxy
* **Type** the hubble type of the galaxy
* **Sigma** the sigma to be used on the flux values extracted from the FITS file
* **Priority** the priority of the galaxy - the higher the number the quicker it will be queued and processed
* **Run_id** the run id these fits files are associated with

## Autoload

**./fits2wu.py** - when run with no arguments the file looks in work_generation.settings to get thresholds and values. It then converts galaxies in order of priority and registration time into work units
If the could is called with -r or --register flag it will find that registration and convert it into work units
