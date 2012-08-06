"""
Fabric to be run on the BOINC server to configure things
"""
from glob import glob
from os.path import splitext, split
from fabric.decorators import task
from fabric.operations import local, prompt
from fabric.state import env

APP_NAME="magphys_wrapper"
PLATFORMS=["windows_x86_64", "windows_intelx86", "x86_64-apple-darwin", "x86_64-pc-linux-gnu", "i686-pc-linux-gnu"]
WINDOWS_PLATFORMS=["windows_x86_64", "windows_intelx86"]

def create_version_xml(platform, app_version, directory, exe):
    """
    Create the version.xml file
    """
    outfile = open(directory + '/version.xml', 'w')
    outfile.write('''<version>
    <file>
        <physical_name>wrapper_{0}{2}_{1}</physical_name>
        <main_program/>
        <copy_file/>
        <logical_name>wrapper</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>fit_sed_{0}{2}_{1}</physical_name>
        <copy_file/>
        <logical_name>fit_sed</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>concat_{0}{2}_{1}</physical_name>
        <copy_file/>
        <logical_name>concat</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>filters.dat_{1}</physical_name>
        <copy_file/>
        <logical_name>filters.dat</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>infrared_dce08_z0.0000.lbr_{1}</physical_name>
        <copy_file/>
        <logical_name>infrared_dce08_z0.0000.lbr</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>starformhist_cb07_z0.0000.lbr_{1}</physical_name>
        <copy_file/>
        <logical_name>starformhist_cb07_z0.0000.lbr</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>zlibs.dat_{1}</physical_name>
        <copy_file/>
        <logical_name>zlibs.dat</logical_name>
    </file>
</version>'''.format(platform, app_version, exe))
    outfile.close()

def copy_files(app_version):
    """Copy the application files

    Copy the application files to where they need to live
    """
    for platform in PLATFORMS:
        local('mkdir -p /home/ec2-user/projects/{3}/apps/{0}/{1}/{2}'.format(APP_NAME, app_version, platform, env.project_name))

        for file in glob('/home/ec2-user/boinc-magphys/client/platforms/{0}/*'.format(platform)):
            head, tail = split(file)
            local('cp {0} /home/ec2-user/projects/{4}/apps/{1}/{2}/{3}/{5}_{2}'.format(file, APP_NAME, app_version, platform, env.project_name, tail))
        for file in glob('/home/ec2-user/boinc-magphys/client/platforms/common/*'):
            head, tail = split(file)
            local('cp {0} /home/ec2-user/projects/{4}/apps/{1}/{2}/{3}/{5}_{2}'.format(file, APP_NAME, app_version, platform, env.project_name, tail))
        if platform in WINDOWS_PLATFORMS:
            create_version_xml(platform, app_version, '/home/ec2-user/projects/{3}/apps/{0}/{1}/{2}'.format(APP_NAME, app_version, platform, env.project_name), '.exe')
        else:
            create_version_xml(platform, app_version, '/home/ec2-user/projects/{3}/apps/{0}/{1}/{2}'.format(APP_NAME, app_version, platform, env.project_name), '')

def sign_files(app_version):
    """Sign the files

    Sign the application files
    """
    for platform in PLATFORMS:
        for file in glob('/home/ec2-user/projects/{3}/apps/{0}/{1}/{2}/*'.format(APP_NAME, app_version, platform, env.project_name)):
            path_ext = splitext(file)
            if len(path_ext) == 2 and (path_ext[1] == '.sig' or path_ext[1] == '.xml'):
                # Ignore this one
                pass
            else:
                local('/home/ec2-user/boinc/tools/sign_executable {0} /home/ec2-user/projects/{1}/keys/code_sign_private | tee {0}.sig'.format(file, env.project_name))

@task
def setup_website():
    """Setup the website

    Copy the config files and restart the httpd daemon
    """
    local('sudo cp /home/ec2-user/projects/{0}/{0}.httpd.conf /etc/httpd/conf.d'.format(env.project_name))
    local('sudo /etc/init.d/httpd restart')

@task
def create_first_version():
    """Create the first version

    Create the first versions of the files
    """
    local('cp -R /home/ec2-user/boinc-magphys/server/config/templates /home/ec2-user/projects/{0}'.format(env.project_name))
    local('cp -R /home/ec2-user/boinc-magphys/server/config/project.xml /home/ec2-user/projects/{0}'.format(env.project_name))

    copy_files(1)
    sign_files(1)

    # Not sure why, but the with cd() doesn't work
    local('cd /home/ec2-user/projects/{0}; bin/xadd'.format(env.project_name))
    local('cd /home/ec2-user/projects/{0}; yes | bin/update_versions'.format(env.project_name))

@task
def create_new_version():
    """Create a new version

    Create a new version of the application
    """
    app_version = prompt('Application version: ')
    prompt('BOINC project name: ', 'project_name')
    copy_files(app_version)
    sign_files(app_version)

    # Not sure why, but the with cd() doesn't work
    local('cd /home/ec2-user/projects/{0}; yes | bin/update_versions'.format(env.project_name))

@task
def start_daemons():
    """Start the BOINC daemons

    Run the BOINC script to start the daemons
    """
    local('cd /home/ec2-user/projects/{0}; bin/start'.format(env.project_name))
