"""
Edit the various configuration files as required for a single server installation.

This code uses the fact that the fileinput module can do inplace editing. When it is set up in inplace mode writing to sys.stdout is
redirected to the file
"""

import fileinput
import sys


def edit_config_xml():
    """
    Edit /home/ec2-user/projects/pogs/config.xml

    1. Add the daemons
    2. Add the locality scheduling
    """
    for line in fileinput.input(['/home/ec2-user/projects/pogs/config.xml'], inplace=True):
        if line.rstrip() == '  </daemons>':
            sys.stdout.write('''    <daemon>
      <cmd>
        /home/ec2-user/boinc-magphys/server/src/Validator/magphys_validator -d 3 --app magphys_wrapper --credit_from_wu --update_credited_job
      </cmd>
    </daemon>
    <daemon>
      <cmd>
        python2.7 /home/ec2-user/boinc-magphys/server/src/assimilator/magphys_assimilator.py -d 3 -app magphys_wrapper
      </cmd>
    </daemon>
  </daemons>
  <locality_scheduling/>
''')
        else:
            sys.stdout.write(line)

def edit_project_inc():
    """
    Edit /home/ec2-user/projects/pogs/html/project/project.inc
    """
    for line in fileinput.input(['/home/ec2-user/projects/pogs/html/project/project.inc'], inplace=True):
        if line.rstrip() == 'define("PROJECT", "REPLACE WITH PROJECT NAME");':
            sys.stdout.write('define("PROJECT", "theSkyNet POGS - the PS1 Optical Galaxy Survey");\n')
        elif line.rstrip() == 'define("COPYRIGHT_HOLDER", "REPLACE WITH COPYRIGHT HOLDER");':
            sys.stdout.write('define("COPYRIGHT_HOLDER", "The International Centre for Radio Astronomy Research");\n')
        elif line.rstrip() == 'define("STYLESHEET", "white.css");':
            sys.stdout.write('define("STYLESHEET", "black.css");\n')
        else:
            sys.stdout.write(line)

def edit_user_php():
    """
    Edit /home/ec2-user/projects/pogs/html/user/index.php
    """
    for line in fileinput.input(['/home/ec2-user/projects/pogs/html/user/index.php'], inplace=True):
        if line.rstrip() == '            XXX is a research project that uses volunteers':
            sys.stdout.write('            POGS is a research project that uses volunteers\n')
        elif line.rstrip() == '            to do research in XXX.':
            sys.stdout.write('''            to do research in astronomy.
We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.
We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.''')
        elif line.rstrip() == '            XXX is a research project that uses Internet-connected':
            sys.stdout.write('            POGS is a research project that uses Internet-connected\n')
        elif line.rstrip() == '            computers to do research in XXX.':
            sys.stdout.write('''            computers to do research in astronomy.
We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.
We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.''')
        elif line.rstrip() == '        XXX is based at':
            sys.stdout.write('        POGS is based at\n')
        elif line.rstrip() == '        [describe your institution, with link to web page]':
            sys.stdout.write('         The International Centre for Radio Astronomy Research.\n')
        elif line.rstrip() == '':
            sys.stdout.write('\n')
        else:
            sys.stdout.write(line)

def edit_create_forums_php():
    """
    Edit /home/ec2-user/projects/pogs/html/ops/create_forums.php
    """
    for line in fileinput.input(['/home/ec2-user/projects/pogs/html/ops/create_forums.php'], inplace=True):
        if line.rstrip() ==  'die("edit script to use your forum names, and remove the die()\n");':
            pass    # Do nothing
        else:
            sys.stdout.write(line)

# Make the changes to the files
edit_config_xml()
edit_project_inc()
edit_user_php()
edit_create_forums_php()
