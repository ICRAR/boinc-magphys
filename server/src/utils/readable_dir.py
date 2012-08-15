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

