require 'rake'

#These steps are known to work with following BOINC server version:
#URL: http://boinc.berkeley.edu/svn/branches/server_stable
#Revision: 25070
#Last Changed Date: 2012-01-10 21:17:51 -0500 (Tue, 10 Jan 2012)

BOINC_SRC="/home/boincadm/boinc"
BOINC_TOOLS_DIR="#{BOINC_SRC}/tools"
PROJECT_NAME="magphys"
PROJECT_ROOT="/home/boincadm/boincprojects/#{PROJECT_NAME}"
BASE_URL = "http://www.boinc-magphys.org"
DB_NAME="magphys"
DB_USER="magphys"
DB_PWD="xx"
APP_NAME="wrapper"
APP_VERSION=1.0
BOINC_PLATFORM="i686-pc-linux-gnu"
PLATFORM_DIR = "#{PROJECT_ROOT}/apps/#{APP_NAME}/#{APP_VERSION}/#{BOINC_PLATFORM}"
INPUT_FILES = FileList["zlibs.dat" "filters.dat" "observations.dat" "infrared_dce08_z0.4600.lbr" "starformhist_cb07_z0.4600.lbr" "OptiLIB_cb07.bin" "OptiLIBis_cb07.bin" "InfraredLIB.bin"]
MAGPHYS_DATA_DIR = "/home/boincadm/magphys/download"
DB_ROOT_PWD="xxx"

desc 'drop project database'
task :drop_project_db do
  sh "mysql -uroot -p#{DB_ROOT_PWD} -e \"drop database #{DB_NAME};\""
end

desc 'setup project database'
task :setup_project_db do
  sh "mysql -uroot -p#{DB_ROOT_PWD} -e \"create database #{DB_NAME};\""
  sh "mysql -uroot -p#{DB_ROOT_PWD} -e \"grant all on #{DB_NAME}.* to #{DB_USER}@'%' identified by '#{DB_PWD}';\""
end

desc 'create project'
task :create_project => :setup_project_db do
  sh "echo 'Y' | xargs -n 1 | #{BOINC_TOOLS_DIR}/make_project --no_query --url_base #{BASE_URL} --srcdir #{BOINC_SRC} --db_name #{DB_NAME} --db_user #{DB_USER} --db_passwd #{DB_PWD} --project_root #{PROJECT_ROOT} --drop_db_first --delete_prev_inst #{PROJECT_NAME}"
  cp "config/project.xml", "#{PROJECT_ROOT}"
  sh "#{PROJECT_ROOT}/bin/xadd"
end

desc 'setup project website'
task :setup_website do
  sh "sudo cp magphys.httpd.conf /etc/apache2/sites-available"
  sh "sudo a2ensite magphys.httpd.conf"
  sh "sudo /etc/init.d/apache2 reload"
end

task :clean do
  rm_r 'build' if File.exists?("build")
  mkdir_p "build/#{BOINC_PLATFORM}"
end

desc 'compile binaries'
task :compile => :clean do
  sh "make -C src/magphys clean all; cd ../.."
  cp "src/magphys/fit_sed", "build/#{BOINC_PLATFORM}"
  # wrapper depends on include and library files from the BOINC src directory. This must be set in wrapper Makefile for this to work.
  sh "make -C src/wrapper; cd ../.."  
  cp "src/wrapper/wrapper", "build/#{BOINC_PLATFORM}"
end

desc 'copy to apps/platform directory'
task :copy_files => :compile do
  mkdir_p "#{PLATFORM_DIR}"
  ["build/#{BOINC_PLATFORM}/wrapper", "build/#{BOINC_PLATFORM}/fit_sed", "config/job.xml", "config/version.xml"].each { |f| 
    cp f, "#{PLATFORM_DIR}" 
  }
end

desc 'sign files'
task :sign_files => :copy_files do
  ["wrapper", "fit_sed", "job.xml"].each { |f| 
    sh "#{BOINC_TOOLS_DIR}/sign_executable #{PLATFORM_DIR}/#{f} #{PROJECT_ROOT}/keys/code_sign_private | tee #{PLATFORM_DIR}/#{f}.sig"
  }
end

desc 'update versions'
task :update_versions => :sign_files do
  sh "cd #{PROJECT_ROOT}; echo \"y\" | xargs -n 1 | #{PROJECT_ROOT}/bin/update_versions"
end