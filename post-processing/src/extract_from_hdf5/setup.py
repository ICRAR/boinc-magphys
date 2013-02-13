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
Setup the distribution of the extract_from hdf5
"""
from distutils.core import setup

setup(name='extract_from_hdf5',
    version='0.1',
    description='Code to extract features from an HDF5 file and put them into a FITS file',
    author='Kevin Vinsen',
    author_email='kevin.vinsen@icrar.org',
    requires=['pyfits(>=3.0.8)', 'h5py(>=2.1.0)', 'numpy(>=1.6.2)'],
    py_modules=['extract_from_hdf5', 'extract_from_hdf5_mod'],
    packages=['utils'])
