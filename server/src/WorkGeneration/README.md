# Generation of work units: overview

*fits2pixels.py* takes a FITS file as input and cuts it up into squares which are inserted into a database. This database is then queried by *pixels2obsfiles.py* which creates a specified number of observations files (one file per square). The third script, which will move observations files into the BOINC project's download hierarchy and call **create_work**, is not yet written.

# Prerequisites

* MySQL locally installed
* Python >=2.7.1 (tested on Python 2.7.1 (r271:86832, Jun 16 2011, 16:59:05))

## Python scripts

MySQL Connector/Python can be installed with either **sudo easy_install mysql-connector** or **sudo pip mysql-connector**
  
Note that the scripts assume that they can use the MySQL "root" user without password.
  
# Example run

    $ cd /path/to/this/directory
    $ mysql -u root < create_link_database.sql # DROPS THE magphys_wu SCHEMA and recreates it
    $ python ./fits2pixels.py /Users/astrogeek/Documents/ICRAR/POGS_NGC628_v3.fits
    $ python ./pixels2obsfiles.py 123 /Users/astrogeek/Documents/ICRAR/obsfiles
    $ ./not_yet_written_script /Users/astrogeek/Documents/ICRAR/obsfiles
	
