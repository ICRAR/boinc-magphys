#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
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
Setup the wrappers around the BOINC 'C' libraries
"""

from distutils.core import setup
from distutils.extension import Extension
import os
from Cython.Build import cythonize

PY_BOINC = "py_boinc"
SOURCES = ['cy_create_work_unit.pyx','c_project/create_work.cpp']

if os.path.exists('/home/ec2-user'):
    INCLUDE_DIRS = ['/home/ec2-user/boinc/sched',
                    '/home/ec2-user/boinc/api',
                    '/home/ec2-user/boinc/lib',
                    '/home/ec2-user/boinc/db',
                    '/home/ec2-user/boinc/tools',
                    '/home/ec2-user/boinc',
                    '/usr/include/mysql55']
    LIBRARY_DIRS = ['/usr/lib64/mysql/']
    extensions = [Extension(PY_BOINC,
                            sources=SOURCES,
                            include_dirs=INCLUDE_DIRS,
                            library_dirs=LIBRARY_DIRS,
                            extra_objects=['/home/ec2-user/boinc/sched/libsched.a',
                                           '/home/ec2-user/boinc/lib/libboinc.a',
                                           '/home/ec2-user/boinc/lib/libboinc_crypt.a',
                                           '/home/ec2-user/boinc/api/libboinc_api.a'],
                            libraries=["mysqlclient"],
                            )]
else:
    INCLUDE_DIRS = ['/Users/kevinvinsen/Documents/ICRAR/work/boinc',
                    '/Users/kevinvinsen/Documents/ICRAR/work/boinc/db',
                    '/Users/kevinvinsen/Documents/ICRAR/work/boinc/sched',
                    '/Users/kevinvinsen/Documents/ICRAR/work/boinc/lib',
                    '/Users/kevinvinsen/Documents/ICRAR/work/boinc/clientgui/mac',
                    '/Users/kevinvinsen/Documents/ICRAR/work/boinc/tools',
                    '/usr/local/mysql-5.5.14-osx10.6-x86_64/include',]
    LIBRARY_DIRS = ['/Users/kevinvinsen/Documents/ICRAR/work/boinc/mac_build/build/Development',
                    '/usr/local/mysql-5.5.14-osx10.6-x86_64/lib']

    extensions = [Extension('create_work111',
                            sources=SOURCES,
                            include_dirs=INCLUDE_DIRS,
                            library_dirs=LIBRARY_DIRS,
                            libraries=["boinc", "boinc_api", "mysqlclient"],
                            )]
setup(
    name=PY_BOINC,
    version='1.0',
    ext_modules=cythonize(
        extensions,
        name=PY_BOINC,
        language="c")
)
