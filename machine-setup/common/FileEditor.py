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
                text = StreamEditor.__call__(text)

                with open(file, 'w') as f:
                    f.write(text)
            else:
                raise IOError('Cannot write to {0}'.format(dir))
        else:
            raise IOError('File {0} not found'.format(file))
