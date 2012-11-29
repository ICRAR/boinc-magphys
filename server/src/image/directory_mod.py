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
Image generation functions
"""
import os
import hashlib

def filename_hash(name, hash_fanout):
    """
    Accepts a filename (without path) and the hash fanout.
    Returns the directory bucket where the file will reside.
    The hash fanout is typically provided by the project config file.
    """
    h = hex(int(hashlib.md5(name).hexdigest()[:8], 16) % hash_fanout)[2:]

    # check for the long L suffix. It seems like it should
    # never be present but that isn't the case
    if h.endswith('L'):
        h = h[:-1]
    return h

def get_file_path(dir_name, file_name, create):
    """
    Accepts a directory name and file name and returns the relative path to the file.
    This method accounts for file hashing and includes the directory
    bucket in the path returned.
    """
    hashed = filename_hash(file_name, 1024)
    hash_dir_name = os.path.join(dir_name,hashed)
    if os.path.isfile(hash_dir_name):
        pass
    elif os.path.isdir(hash_dir_name):
        pass
    elif create:
        os.mkdir(hash_dir_name)
    return os.path.join(dir_name,hashed,file_name)

def get_colour_image_path(imageDirName, imagePrefixName, colour, create):
    """
    Generates the relative path to the file given the directory name, image prefix
    and colour.  The file name is used to generate a hash to spread the files across
    many directories to avoid having too many files in a single directory.
    """
    return get_file_path(imageDirName, imagePrefixName + "_colour_" + str(colour) + ".png", create)

def get_thumbnail_colour_image_path(imageDirName, imagePrefixName, colour, create):
    """
    Generates the relative path to the file given the directory name, image prefix
    and colour.  The file name is used to generate a hash to spread the files across
    many directories to avoid having too many files in a single directory.
    """
    return get_file_path(imageDirName, imagePrefixName + "_tn_colour_" + str(colour) + ".png", create)
