#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
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
</version>'''.format(platform, app_version, exe))
    outfile.close()

def copy_files(app_version):
    """
    Copy the application files

    Copy the application files to where they need to live
    """
    for platform in PLATFORMS:
        local('mkdir -p /home/ec2-user/projects/{3}/apps/{0}/{1}/{2}'.format(APP_NAME, app_version, platform, env.project_name))

        for file in glob('/home/ec2-user/boinc-magphys/client/platforms/{0}/*'.format(platform)):
            head, tail = split(file)
            local('cp {0} /home/ec2-user/projects/{4}/apps/{1}/{2}/{3}/{5}_{2}'.format(file, APP_NAME, app_version, platform, env.project_name, tail))
        if platform in WINDOWS_PLATFORMS:
            create_version_xml(platform, app_version, '/home/ec2-user/projects/{3}/apps/{0}/{1}/{2}'.format(APP_NAME, app_version, platform, env.project_name), '.exe')
        else:
            create_version_xml(platform, app_version, '/home/ec2-user/projects/{3}/apps/{0}/{1}/{2}'.format(APP_NAME, app_version, platform, env.project_name), '')

def sign_files(app_version):
    """
    Sign the files

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
    """
    Edit the files as we need them
    """
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
      <cmd> run_in_ops ./autolock.php --ndays 30 </cmd>
      <period> 1 days </period>
      <disabled> 0 </disabled>
      <output> autolock.out </output>
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
      <cmd> /home/ec2-user/boinc-magphys/server/src/work_generation/fits2wu.py </cmd>
      <period> 9 minutes </period>
      <disabled> 0 </disabled>
      <output> fits2wu.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/server/src/docmosis/docmosis_worker.py </cmd>
      <period> 4 min </period>
      <disabled> 0 </disabled>
      <output> docmosis_worker.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/server/src/archive/delete_galaxy_task.py </cmd>
      <period> 30 minutes </period>
      <disabled> 0 </disabled>
      <output> delete_galaxy_task.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/server/src/archive/archive_hdf5_galaxy.py -o /home/ec2-user/archive </cmd>
      <period> 30 minutes </period>
      <disabled> 0 </disabled>
      <output> archive_hdf5_galaxy.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/server/src/archive/processed_galaxy.py </cmd>
      <period> 4 hours </period>
      <disabled> 0 </disabled>
      <output> processed_galaxy.out </output>
    </task>
    <task>
      <cmd> /home/ec2-user/boinc-magphys/server/src/archive/store_files.py -d /home/ec2-user/archive/to_store/ </cmd>
      <period> 4 hours </period>
      <disabled> 0 </disabled>
      <output> store_files.out </output>
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
      <pid_file> magphys_validator.pid </pid_file>
      <output> magphys_validator.log </output>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper -mod 6 0 </cmd>
      <output> assimilator.0.log </output>
      <pid_file> assimilator.0.pid </pid_file>
      <disabled>0</disabled>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper -mod 6 1 </cmd>
      <output> assimilator.1.log </output>
      <pid_file> assimilator.1.pid </pid_file>
      <disabled>0</disabled>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper -mod 6 2 </cmd>
      <output> assimilator.2.log </output>
      <pid_file> assimilator.2.pid </pid_file>
      <disabled>0</disabled>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper -mod 6 3 </cmd>
      <output> assimilator.3.log </output>
      <pid_file> assimilator.3.pid </pid_file>
      <disabled>0</disabled>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper -mod 6 4 </cmd>
      <output> assimilator.4.log </output>
      <pid_file> assimilator.4.pid </pid_file>
      <disabled>0</disabled>
    </daemon>
    <daemon>
      <cmd> /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper -mod 6 5 </cmd>
      <output> assimilator.5.log </output>
      <pid_file> assimilator.5.pid </pid_file>
      <disabled>0</disabled>
    </daemon>
  </daemons>'''.format(env.project_name))
    file_editor.substitute('<one_result_per_user_per_wu>', end='</one_result_per_user_per_wu>',to='''
    <prefer_primary_platform>1</prefer_primary_platform>
    <max_wus_in_progress>10</max_wus_in_progress>
    <shmem_work_items>200</shmem_work_items>
    <feeder_query_size>300</feeder_query_size>
    <reliable_priority_on_over>5</reliable_priority_on_over>
    <delete_delay_hours>24</delete_delay_hours>
    <msg_to_host/>
    <one_result_per_user_per_wu/>
    <one_result_per_host_per_wu/>''')
    file_editor('/home/ec2-user/projects/{0}/config.xml'.format(env.project_name))

@task
def setup_postfix():
    """
    Setup the relocated file

    The relocated file needs the hostname
    """
    host_name = socket.gethostname()
    local('''sudo su -l root -c 'echo "ec2-user@{0}.ec2.internal  {1}@gmail.com
root@{0}.ec2.internal      {1}@gmail.com
apache@{0}.ec2.internal    {1}@gmail.com" >> /etc/postfix/generic' '''.format(host_name, env.gmail_account))
    local('sudo postmap /etc/postfix/generic')

@task
def setup_website():
    """
    Setup the website

    Copy the config files and restart the httpd daemon
    """
    local('sudo cp /home/ec2-user/projects/{0}/{0}.httpd.conf /etc/httpd/conf.d'.format(env.project_name))
    local('sudo /etc/init.d/httpd restart')

@task
def create_first_version():
    """
    Create the first version

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
    """
    Create a new version

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
    """
    Start the BOINC daemons

    Run the BOINC script to start the daemons
    """
    local('cd /home/ec2-user/projects/{0}; bin/start'.format(env.project_name))
