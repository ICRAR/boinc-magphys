"""
Fabric to be run on the BOINC server to configure things
"""

# Add the parent directory to the path
import sys
sys.path.append('..')

from glob import glob
from os.path import splitext, split
from fabric.decorators import task
from fabric.operations import local, prompt
from fabric.state import env
import socket
from common.FileEditor import FileEditor

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
        <physical_name>infrared_dce08_z0.0100.lbr_{1}</physical_name>
        <copy_file/>
        <logical_name>infrared_dce08_z0.0100.lbr</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>starformhist_cb07_z0.0100.lbr_{1}</physical_name>
        <copy_file/>
        <logical_name>starformhist_cb07_z0.0100.lbr</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>infrared_dce08_z0.0200.lbr_{1}</physical_name>
        <copy_file/>
        <logical_name>infrared_dce08_z0.0200.lbr</logical_name>
        <gzip/>
    </file>
    <file>
        <physical_name>starformhist_cb07_z0.0200.lbr_{1}</physical_name>
        <copy_file/>
        <logical_name>starformhist_cb07_z0.0200.lbr</logical_name>
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
def edit_files():
    # Edit project.inc
    file_editor = FileEditor()
    file_editor.substitute('REPLACE WITH PROJECT NAME', to='theSkyNet {0} - the PS1 Optical Galaxy Survey'.format(env.project_name.upper()))
    file_editor.substitute('REPLACE WITH COPYRIGHT HOLDER', to='The International Centre for Radio Astronomy Research')
    file_editor.substitute('"white.css"', to='"black.css"')
    file_editor.substitute('define("FORUM_QA_MERGED_MODE", false);', to='define("FORUM_QA_MERGED_MODE", true);')
    file_editor.substitute('admin@$master_url', to='theskynet.boinc@gmail.com')
    file_editor.substitute('moderator1@$master_url|moderator2@$master_url', to='theskynet.boinc@gmail.com')
    file_editor('/home/ec2-user/projects/{0}/html/project/project.inc'.format(env.project_name))

    # Edit config.xml
    file_editor = FileEditor()
    file_editor.substitute('  <tasks>', end='</daemons>', to='''
  <tasks>
    <task>
      <cmd> antique_file_deleter -d 2 </cmd>
      <period> 24 hours </period>
      <disabled> 0 </disabled>
      <output> antique_file_deleter.out </output>
    </task>
    <task>
      <cmd>db_dump -d 2 --dump_spec ../db_dump_spec.xml</cmd>
      <period> 12 hours </period>
      <disabled> 0 </disabled>
      <output> db_dump.out </output>
    </task>
    <task>
      <cmd> run_in_ops ./update_uotd.php </cmd>
      <period> 1 days </period>
      <disabled> 0 </disabled>
      <output> update_uotd.out </output>
    </task>
    <task>
      <cmd> run_in_ops ./update_forum_activities.php </cmd>
      <period> 1 hour </period>
      <disabled> 0 </disabled>
      <output> update_forum_activities.out </output>
    </task>
    <task>
      <cmd> update_stats </cmd>
      <period> 12 hours </period>
      <disabled> 0 </disabled>
      <output> update_stats.out </output>
    </task>
    <task>
      <cmd> run_in_ops ./update_profile_pages.php </cmd>
      <period> 48 hours </period>
      <disabled> 0 </disabled>
      <output> update_profile_pages.out </output>
    </task>
    <task>
      <cmd> run_in_ops ./team_import.php </cmd>
      <period> 24 hours </period>
      <disabled> 1 </disabled>
      <output> team_import.out </output>
    </task>
    <task>
      <cmd> run_in_ops ./notify.php </cmd>
      <period> 24 hours </period>
      <disabled> 1 </disabled>
      <output> notify.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/server/src/credit/assign_credit.py -app magphys_wrapper </cmd>
      <period> 24 hours </period>
      <disabled> 0 </disabled>
      <output> assign_credit.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/server/src/credit/update_credit.py -app magphys_wrapper </cmd>
      <period> 24 hours </period>
      <disabled> 0 </disabled>
      <output> update_credit.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/post-processing/src/build_png_image.py </cmd>
      <period> 3 hour </period>
      <disabled> 0 </disabled>
      <output> build_png_image.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/server/src/work_generation/obsfiles2wu.py /home/ec2-user/f2wu /home/ec2-user/projects/{0} -t 10000.format(env.project_name) + </cmd>
      <period> 3 hour </period>
      <disabled> 0 </disabled>
      <output> obsfiles2wu.out </output>
    </task>
    <task>
      <cmd>census</cmd>
      <period>1 day</period>
      <output> census.out </output>
    </task>
  </tasks>
  <daemons>
    <daemon>
      <cmd> feeder -d 2 --priority_order_create_time </cmd>
    </daemon>
    <daemon>
      <cmd> transitioner -d 2 </cmd>
    </daemon>
    <daemon>
      <cmd> file_deleter -d 2 </cmd>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/magphys_validator/magphys_validator -d 3 --app magphys_wrapper --credit_from_wu --update_credited_job </cmd>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper -mod 2 0 </cmd>
      <output> assimilator.0.log </output>
      <pid> assimilator.0.pid </pid>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper -mod 2 1 </cmd>
      <output> assimilator.1.log </output>
      <pid> assimilator.1.pid </pid>
    </daemon>
  </daemons>''')
    file_editor.substitute('<one_result_per_user_per_wu>', end='</one_result_per_user_per_wu>',to='''
    <prefer_primary_platform>1</prefer_primary_platform>
    <one_result_per_user_per_wu/>
    <max_wus_in_progress>10</max_wus_in_progress>
    <shmem_work_items>200</shmem_work_items>
    <feeder_query_size>300</feeder_query_size>
    <reliable_priority_on_over>5</reliable_priority_on_over>
    <delete_delay_hours>24</delete_delay_hours>
    <one_result_per_host_per_wu/>''')
    file_editor('/home/ec2-user/projects/{0}/config.xml'.format(env.project_name))

@task
def setup_postfix():
    """Setup the relocated file

    The relocated file needs the hostname
    """
    host_name = socket.gethostname()
    local('''sudo su -l root -c 'echo "ec2-user@{0}.ec2.internal  theskynet.boinc@gmail.com
root@{0}.ec2.internal      theskynet.boinc@gmail.com
apache@{0}.ec2.internal    theskynet.boinc@gmail.com" >> /etc/postfix/generic' '''.format(host_name))
    local('sudo postmap /etc/postfix/generic')

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
