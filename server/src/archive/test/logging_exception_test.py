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
Testing the logging of exception
"""
from utils.logging_helper import config_logger
import sys

LOG = config_logger(__name__)


def throws():
    LOG.info('In throws()')
    raise RuntimeError('this is the error message')


def main():
    LOG.info('In main')
    try:
        throws()
        return 0
    except Exception:
        LOG.exception('Error from throws():')
        return 1

if __name__ == '__main__':
    sys.exit(main())
