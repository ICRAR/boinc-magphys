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

$ ./create_file_details input_dir output_dir
$ ./create_file_details ~/boinc-magphys/runs/0001 ~/boinc-magphys/server/runs/0001

* **input_dir** where the *.lbr files are stored
* **output_dir** where the output file is written

### Step 2 (Boinc Server)

$ ./load_run_details.py run_id dir_with_files url_prefix comment
$ ./load_run_details.py 1 /home/ec2-user/boinc-magphys/server/runs/0001 http://boinc-download.icrar.org/runs/0001/ 'PS Filters + SDSSu'

* **run_id** is the run id to be used
* **dir_with_files** where the filters.dat and file_details.dat files can be found as we need to record the md5sum and size
* **url_prefix** the URL prefix to the files
* **comment** a description of the run

## Register Galaxy

$ ./register_fits_file.py Filename Redshift Galaxy Type Sigma Priority Run_id
$ ./register_fits_file.py /home/ec2-user/galaxies/POGS_IC0089.fits    0.0181  IC0089   S0     0.05    0  1

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


# Old method

*fits2obs.py* takes a FITS file as input and cuts it up into squares which are inserted into a database.
This database is then queried to create a specified number of observations files (one file per square).
The second script, which will move observations files into the BOINC project's download hierarchy and call **create_work**.

## Python scripts

MySQL Connector/Python can be installed with either **sudo pip-2.7 install mysql-connector**.

* **fits2obsfiles.py** works with a single FITS file as the smallest unit of work.
A FITS file can be processed only once, unless effort is made to make sure that the object name in it is changed.
Note that if multiple FITS files contain the exact same object name, an error (duplicate key in database) will be thrown and no processing will be made.
When the script has run, all non-empty squares in the FITS file will be inserted into the database along with their corresponding pixels ready for the results.
The observations files will have been generated. If the observations files are deleted or lost before **obsfiles2wu.py** has been called, some manual intervention is needed.
* **obsfiles2wu.py** looks into the specified directory and assumes that it contains *only* observations files; for each of them, it calls the appropriate magical BOINC commands to move them into the BOINC project's download hierarchy and create work units for them.

## Flow-control

In general, it is assumed that **fits2pixels.py** will be called occassionally, once per FITS file, and that **pixels2obsfiles.py** and **obsfiles2wu.py** will be called for small chunks (hundreds to thousands) or squares regularly.
The two latter scripts could perhaps be merged into one, eventually.

# Example run

    $ cd /path/to/this/directory
    $ mysql -u root < create_database.sql # DROPS THE magphys SCHEMA and recreates it
    $ python2.7 fits2obsfiles.py /home/ec2-user/galaxies/POGS_NGC628_v3.fits 0.001 /home/ec2-user/f2wu /home/ec2-user/galaxyImages NGC628
    $ python2.7 obsfiles2wu.py /home/ec2-user/f2wu /home/ec2-user/projects/pogs 10

Note that *obsfiles2wu* will move the observations files into the BOINC project's download hierarchy.

