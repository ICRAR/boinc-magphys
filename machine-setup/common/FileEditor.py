#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013-2013
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
Edit a file using the stream editor
"""
import os
import shutil
from common.StreamEditor import StreamEditor


class FileEditor(StreamEditor):
    def __call__(self, edit_file):
        """Edit a file

        :param edit_file: the filename to edit
         """
        if os.path.isfile(edit_file):
            # We have a file
            (directory, tail) = os.path.split(edit_file)
            if os.access(directory, os.W_OK):
                # Copy the file
                shutil.copy(edit_file, edit_file + '.bak')
                with open(edit_file, 'r') as f:
                    text = f.read()
                text = StreamEditor.__call__(self, text)

                with open(edit_file, 'w') as f:
                    f.write(text)
            else:
                raise IOError('Cannot write to {0}'.format(directory))
        else:
            raise IOError('File {0} not found'.format(edit_file))
