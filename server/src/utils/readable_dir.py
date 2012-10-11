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
Check a directory is readable for argparse
"""
import argparse
import os

class ReadableDir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) != 1:
            raise argparse.ArgumentTypeError("ReadableDir:{0} is not a valid path".format(values))
        prospective_dir=values[0]
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("ReadableDir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("ReadableDir:{0} is not a writeable dir".format(prospective_dir))

