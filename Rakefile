require 'rake'

#These steps are known to work with following BOINC server version:
# Recommended version per http://boinc.berkeley.edu/download_all.php on 2012-05-11

PROJECT_NAME="pogs"
PROJECT_ROOT="/home/ec2-user/boinc/projects/#{PROJECT_NAME}"
APP_NAME="magphys_wrapper"
APP_VERSION=1.0
PLATFORMS=["windows_x86_64", "x86_64-apple-darwin", "x86_64-pc-linux-gnu"]
PLATFORM_DIR = "#{PROJECT_ROOT}/apps/#{APP_NAME}/#{APP_VERSION}"
BOINC_TOOLS_DIR="/opt/boinc/tools"

desc 'setup project website'
task :setup_website do
  sh "cp #{PROJECT_ROOT}/#{PROJECT_NAME}.httpd.conf /etc/httpd/conf.d"
  sh "/etc/init.d/httpd restart"
end

desc 'copy to apps/platform directory'
task :copy_files do
  cp_r "server/config/templates", "#{PROJECT_ROOT}"

  PLATFORMS.each { |platform|
     mkdir_p "#{PLATFORM_DIR}/#{platform}" 
     cp FileList["client/platforms/#{platform}/*"], "#{PLATFORM_DIR}/#{platform}", :preserve => true
     cp "server/config/job.xml", "#{PLATFORM_DIR}/#{platform}/job_#{platform}.xml", :preserve => true
     cp FileList["client/platforms/common/*"], "#{PLATFORM_DIR}/#{platform}", :preserve => true
  }
  
  cp "server/config/project.xml", "#{PROJECT_ROOT}", :preserve => true
  
  # Now added
  sh "#{PROJECT_ROOT}/bin/xadd"
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
# cp_r "server/config/templates", "#{PROJECT_ROOT}"
# It appears as though create_work requires the number of "input files" to match the number of files mentioned in the template,
# even in cases where the files are not local. I suspect this is a bug in the supplied make_work application. We will write our
# own work generator eventually and this is only for test purposes anyway, so for now let's supply enough arguments to make
# create_work happy.
  sh "cd #{PROJECT_ROOT}; #{PROJECT_ROOT}/bin/create_work -appname #{APP_NAME} -wu_name test -wu_template templates/fitsed_wu -result_template templates/fitsed_result 1 2 3 4 5 6 7 8"
end

desc 'starts the BOINC daemons'
task :start_daemons do
 sh "cd #{PROJECT_ROOT}; #{PROJECT_ROOT}/bin/xadd"
 sh "cd #{PROJECT_ROOT}; #{PROJECT_ROOT}/bin/start"
end
