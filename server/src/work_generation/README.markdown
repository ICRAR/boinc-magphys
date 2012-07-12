# Generation of work units: overview

*fits2pixels.py* takes a FITS file as input and cuts it up into squares which are inserted into a database. This database is then queried by *pixels2obsfiles.py* which creates a specified number of observations files (one file per square). The third script, which will move observations files into the BOINC project's download hierarchy and call **create_work**, is not yet written.

# Prerequisites

* AWS running at least a small model - this uses more memory than a micro model provides
* MySQL locally installed
* Python >=2.7.1 (tested on Python 2.7.1 (r271:86832, Jun 16 2011, 16:59:05))

## Python scripts

MySQL Connector/Python can be installed with either **sudo easy_install-2.7 mysql-connector** or **sudo pip-2.7 install mysql-connector**. Note that the scripts assume that they can use the MySQL "root" user without password.

* **fits2obsfiles.py** works with a single FITS file as the smallest unit of work. A FITS file can be processed only once, unless effort is made to make sure that the object name in it is changed. Note that if multiple FITS files contain the exact same object name, an error (duplicate key in database) will be thrown and no processing will be made. When the script has run, all non-empty squares in the FITS file will be inserted into the database along with their corresponding pixels ready for the results. The observations files will have been generated. If the observations files are deleted or lost before **obsfiles2wu.py** has been called, some manual intervention is needed.
* **obsfiles2wu.py** looks into the specified directory and assumes that it contains *only* observations files; for each of them, it calls the appropriate magical BOINC commands to move them into the BOINC project's download hierarchy and create work units for them.

## Flow-control

In general, it is assumed that **fits2pixels.py** will be called occassionally, once per FITS file, and that **pixels2obsfiles.py** and **obsfiles2wu.py** will be called for small chunks (hundreds to thousands) or squares regularly. The two latter scripts could perhaps be merged into one, eventually.

# Example run

    $ cd /path/to/this/directory
    $ mysql -u root < create_link_database.sql # DROPS THE magphys_wu SCHEMA and recreates it
    $ python2.7 fits2obsfile.py /home/ec2-user/galaxies/POGS_NGC628_v3.fits /home/ec2-user/f2wu NGC628
    $ python2.7 obsfiles2wu.py /home/ec2-user/f2wu /home/ec2-user/projects/pogs 10

Note that *obsfiles2wu* will move the observations files into the BOINC project's download hierarchy.

