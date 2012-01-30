### BOINC Server Setup Instructions

Follow [the instructions for setting up BOINC server on debian](http://wiki.debian.org/BOINC/ServerGuide/).

Once the server is setup with BOINC stable version these instructions below can be used to setup the magphys `fit_sed` program for distribution. We use the [wrapper app](http://wiki.debian.org/BOINC/ServerGuide/WrapperApp) to run the MagPhys (Fortran77) code under BOINC.

#### Rake tasks for the WrapperApp setup:

1. Create project.xml with platforms and wrapper app:

  `./make_project --url_base "http://www.boinc-magphys.org" --db_name magphys --db_user magphys --db_passwd magphyspw --project_root ~/boincprojects/magphys --drop_db_first --delete_prev_inst magphys`

2. Website setup:
  ```sh
  chmod g+w -R .
  chmod -R o+x html/inc
  sudo cp magphys.httpd.conf /etc/apache2/sites-available
  sudo a2ensite magphys.httpd.conf
  sudo /etc/init.d/apache2 reload
  a2enmod rewrite
  a2enmod deflate
  ```

3. Create directory structure: `apps/wrapper/<version>/<platform>/<binaries>`:
  `-- binaries to include wrapper and the application binaries, job.xml file.`

4. `bin/xadd`

5. Sign executables:
  ```
  ~/boinc/tools/sign_executable wrapper_6.12_i686-pc-linux-gnu ../../keys/code_sign_private | tee wrapper_6.12_i686-pc-linux-gnu.sig
  ~/boinc/tools/sign_executable fit_sed ../../keys/code_sign_private | tee fit_sed.sig
  ```

6. `bin/update_versions`

7. Setup templates for work unit and result:

  `bin/create_work -appname wrapper -wu_name test -wu_template templates/fitsed_wu -result_template templates/fitsed_result zlibs.dat filters.dat observations.dat infrared_dce08_z0.4600.lbr starformhist_cb07_z0.4600.lbr OptiLIB_cb07.bin OptiLIBis_cb07.bin InfraredLIB.bin`

8. Start daemons:
  ```
  bin/start
  bin/status
  ```

To install client on debian:
  ```
  sudo apt-get boinc-client boinc-manager
  /etc/init.d/boinc-client start
  Start the GUI for manager: System Tools -> BoincManager
  ```

The working directory for client is: `/var/lib/boinc-client`, configuration is in `/etc/default/boinc-client`.

