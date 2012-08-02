"""
Fabric to be run on the BOINC server to configure things
"""
from glob import glob
from os.path import splitext
from fabric.context_managers import cd
from fabric.decorators import task
from fabric.operations import local

APP_NAME="magphys_wrapper"
PLATFORMS=["windows_x86_64", "windows_intelx86", "x86_64-apple-darwin", "x86_64-pc-linux-gnu", "i686-pc-linux-gnu"]

def copy_files(app_version = 1):
    """Copy the application files

    Copy the application files to where they need to live
    """
    for platform in PLATFORMS:
        local('mkdir -p /home/ec2-user/projects/pogs/apps/{0}/{1}/{2}'.format(APP_NAME, app_version, platform))

        for file in glob('/home/ec2-user/boinc-magphys/client/platforms/{0}/*'.format(platform)):
            local('cp {0} /home/ec2-user/projects/pogs/apps/{1}/{2}/{3}'.format(file, APP_NAME, app_version, platform))
        for file in glob('/home/ec2-user/boinc-magphys/client/platforms/common/*'):
            local('cp {0} /home/ec2-user/projects/pogs/apps/{1}/{2}/{3}'.format(file, APP_NAME, app_version, platform))

def sign_files(app_version = 1):
    """Sign the files

    Sign the application files
    """
    copy_files(app_version)
    for platform in PLATFORMS:
        for file in glob('/home/ec2-user/projects/pogs/apps/{0}/{1}/{2}/*'.format(APP_NAME, app_version, platform)):
            path_ext = splitext(file)
            if len(path_ext) == 2 and (path_ext[1] == '.sig' or path_ext[1] == '.xml'):
                # Ignore this one
                pass
            else:
                local('/home/ec2-user/boinc/tools/sign_executable {0} /home/ec2-user/projects/pogs/keys/code_sign_private | tee {0}.sig'.format(file))

@task
def setup_website():
    """Setup the website

    Copy the config files and restart the httpd daemon
    """
    local('sudo cp /home/ec2-user/projects/pogs/pogs.httpd.conf /etc/httpd/conf.d')
    local('sudo /etc/init.d/httpd restart')

@task
def create_first_version():
    """Create the first version

    Create the first versions of the files
    """
    local('cp -R /home/ec2-user/boinc-magphys/server/config/templates /home/ec2-user/projects/pogs')
    local('cp -R /home/ec2-user/boinc-magphys/server/config/project.xml /home/ec2-user/projects/pogs')
    sign_files()

    # Not sure why, but the with cd() doesn't work
    local('cd /home/ec2-user/projects/pogs; yes | bin/update_versions')
    local('cd /home/ec2-user/projects/pogs; bin/xadd')

@task
def start_daemons():
    """Start the BOINC daemons

    Run the BOINC script to start the daemons
    """
    local('cd /home/ec2-user/projects/pogs; bin/start')
