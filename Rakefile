require 'rake'

#These steps are known to work with following BOINC server version:
#URL: http://boinc.berkeley.edu/svn/branches/server_stable
#Revision: 25070
#Last Changed Date: 2012-01-10 21:17:51 -0500 (Tue, 10 Jan 2012)


BOINC_SRC=ENV["BOINC_SRC"]
BOINC_TOOLS_DIR="#{BOINC_SRC}/tools"
PROJECT_NAME="magphys"
PROJECT_ROOT="/home/boincadm/boincprojects/#{PROJECT_NAME}"
BASE_URL = "http://www.boinc-magphys.org"
DB_NAME="magphys"
DB_USER="magphys"
DB_PWD="xx"
APP_NAME="wrapper"
APP_VERSION=1.0
BUILD_PLATFORM="i686-pc-linux-gnu"
PLATFORMS=["i686-pc-linux-gnu", "windows_intelx86", "i686-apple-darwin", "x86_64-apple-darwin"]
PLATFORM_DIR = "#{PROJECT_ROOT}/apps/#{APP_NAME}/#{APP_VERSION}"
MAGPHYS_DATA_DIR = "/home/boincadm/magphys/download"
DB_ROOT_PWD="xxx"

desc 'create BOINC MySQL user'
task :create_user do
  sh "mysql -u root -e \"CREATE USER 'magphys'@'localhost' IDENTIFIED BY 'xx';\""
  sh "mysql -u root -e \"GRANT ALL ON #{DB_NAME}.* TO 'magphys'@'localhost';\""
end

desc 'create project'
task :create_project => :create_user do
  sh "yes | #{BOINC_TOOLS_DIR}/make_project --no_query --url_base #{BASE_URL} --srcdir #{BOINC_SRC} --db_name #{DB_NAME} --db_user #{DB_USER} --db_passwd #{DB_PWD} --project_root #{PROJECT_ROOT} --drop_db_first --delete_prev_inst #{PROJECT_NAME}"
  cp "config/project.xml", "#{PROJECT_ROOT}"
  sh "#{PROJECT_ROOT}/bin/xadd"
  sh "chown -R boincadm:boincadm #{PROJECT_ROOT}"
end

desc 'setup project website'
task :setup_website do
  sh "cp #{PROJECT_ROOT}/magphys.httpd.conf /etc/apache2/sites-available"
  sh "a2ensite magphys.httpd.conf"
  sh "/etc/init.d/apache2 reload"  
end

task :clean do
  rm "platforms/#{BUILD_PLATFORM}/fit_sed" if File.exists?("platforms/#{BUILD_PLATFORM}/fit_sed")
  rm "platforms/#{BUILD_PLATFORM}/wrapper" if File.exists?("platforms/#{BUILD_PLATFORM}/wrapper")
end

desc 'compile binaries for the current build platform'
task :compile => :clean do
  sh "make -C src/magphys clean all; cd ../.."
  cp "src/magphys/fit_sed", "platforms/#{BUILD_PLATFORM}", :preserve => true
  # wrapper depends on include and library files from the BOINC src directory. The wrapper Makefile requires the env var ENV[BOINC_SRC] to work.
  sh "make -C src/wrapper"  
  cp "src/wrapper/wrapper", "platforms/#{BUILD_PLATFORM}", :preserve => true
end

desc 'copy to apps/platform directory'
task :copy_files do
  PLATFORMS.each { |platform|
     mkdir_p "#{PLATFORM_DIR}/#{platform}" 
     cp FileList["platforms/#{platform}/*"], "#{PLATFORM_DIR}/#{platform}", :preserve => true
     cp "config/job.xml", "#{PLATFORM_DIR}/#{platform}/job_#{platform}.xml", :preserve => true
  }
end

desc 'sign files'
task :sign_files => :copy_files do
  PLATFORMS.each { |platform|
    FileList["#{PLATFORM_DIR}/#{platform}/*"].exclude("#{PLATFORM_DIR}/#{platform}/version.xml").to_a().each { |f| 
    sh "#{BOINC_TOOLS_DIR}/sign_executable #{f} #{PROJECT_ROOT}/keys/code_sign_private | tee #{f}.sig"
    }
  }
end

desc 'update versions'
task :update_versions => :sign_files do
  sh "cd #{PROJECT_ROOT}; yes | #{PROJECT_ROOT}/bin/update_versions"
end

desc 'create work'
task :create_work do
  cp_r "config/templates", "#{PROJECT_ROOT}"
  sh "cd #{PROJECT_ROOT}; #{PROJECT_ROOT}/bin/create_work -appname wrapper -wu_name test -wu_template templates/fitsed_wu -result_template templates/fitsed_result"
end
