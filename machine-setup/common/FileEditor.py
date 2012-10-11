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
Edit a file using the stream editor
"""
import os
import shutil
from common.StreamEditor import StreamEditor

class FileEditor(StreamEditor):
    def __call__(self, file):
        """Edit a file

        :param file: the filename to edit
         """
        if os.path.isfile(file):
            # We have a file
            (dir, tail) = os.path.split(file)
            if os.access(dir, os.W_OK):
                # Copy the file
                shutil.copy(file, file + '.bak')
                with open(file, 'r') as f:
                    text = f.read()
                text = StreamEditor.__call__(self, text)

                with open(file, 'w') as f:
                    f.write(text)
            else:
                raise IOError('Cannot write to {0}'.format(dir))
        else:
            raise IOError('File {0} not found'.format(file))
