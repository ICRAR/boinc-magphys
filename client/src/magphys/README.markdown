### This is the source for [MagPhys](http://www.iap.fr/magphys/magphys/MAGPHYS.html)

A number of the large model files have been omitted from the repository.
* InfraredLIB.bin - 1.29GB
* OptiLIB_cb07.bin - 1.54GB
* OptiLIBis_cb07.bin - 1.54GB


To learn more about MagPhys take a look at the magphys-readme.pdf file in the download.

#### To compile MagPhys on Windows:
1. The Makefile relies on Cgywin being installed
2. Use Makefile.cygwin

#### To compile MagPhys on Linux:
1. The Makefile has been modified to link the final executable (fit_sed_skynet) as a single executable with no shared libraries.
2. Use gfortran 4.4+ to compile
3. Use the Makefile.linux to use the Linux path

#### To compile MagPhys on Mac:

1. The Makefile has been modified to link the final executable (fit_sed_skynet) as a single executable with no shared libraries.
2. Use gfortran 4.6.2+ to compile
3. Use the Makefile.mac to use the OS X path
