### This is a [BOINC WrapperApp](http://boinc.berkeley.edu/trac/wiki/WrapperApp) for [MagPhys](http://www.iap.fr/magphys/magphys/MAGPHYS.html)

#### To compile BOINC wrapper on windows:

1. Open the `win_build/samples.sln` file in Visual Studio 2010.
2. Download the [ssl dependency](http://boinc.berkeley.edu/trac/browser/trunk/boinc_depends_win_vs2010) ([svn url](http://boinc.berkeley.edu/svn/trunk/boinc_depends_win_vs2010/openssl/))
3. Modify the include path to add directory for ssl include files downloaded previously.
4. Build following [these instructions](http://boinc.berkeley.edu/trac/wiki/CompileClient#BuildingtheclientwithVisualStudio2005andVisualStudio2005ExpressEdition)

  __Use Cygwin gfortran to compile Magphys.__

#### To compile BOINC wrapper on Mac:

1. cd to `mac_build`.
2. Download wxMac-2.8.10, curl-7.21.3, and c-ares-1.7.4 according to instructions [here](http://boinc.berkeley.edu/trac/wiki/MacBuild)
3. `source setupForBOINC.sh --clean`
4. `source ./BuildMacBOINC.sh -lib` (only the boinc lib is needed to compile the wrapper)
5. `cd samples/wrapper`
6. `./BuildMacWrapper.sh`

