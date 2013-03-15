#! /usr/bin/env python2.7
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
Put back the area user details deleted by accident

http://cortex.ivec.org:7780/QUERY?query=files_list&format=list
http://cortex.ivec.org:7780/REtrieVE?file_id=NGC3055.hdf5
"""

import StringIO
import logging
import argparse
import os
import urllib2
import subprocess

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

class WriteableDir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) != 1:
            raise argparse.ArgumentTypeError("WriteableDir:{0} is not a valid path".format(values))
        prospective_dir=values[0]
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("WriteableDir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.W_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("WriteableDir:{0} is not a writeable dir".format(prospective_dir))

parser = argparse.ArgumentParser('Copy files from NGAS on Cortex to a directory specified')
parser.add_argument('-d','--dir', action=WriteableDir, nargs=1, help='where the HDF5 files are to be written to')
args = vars(parser.parse_args())

DIR = args['dir']
if DIR is None:
    parser.print_help()
    exit(1)

# Get the list of files
response = urllib2.urlopen("http://cortex.ivec.org:7780/QUERY?query=files_list&format=list")
web_page = response.read()
file_set = set()

for line in StringIO.StringIO(web_page):
    items = line.split()

    file_name = items[2]
    file_size = items[5]

    if int(file_size) > 0 and file_name not in file_set:
        LOG.info("{0} - {1}".format(file_name, file_size))
        file_set.add(file_name)
        path_name = os.path.join(DIR, file_name)
        subprocess.call("wget -O {0} http://cortex.ivec.org:7780/RETRIEVE?file_id={1}".format(path_name, file_name), shell=True)
