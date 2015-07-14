__author__ = 'ict310'

"""
For testing the archiver on a single SED file.
"""

from archive_hdf5_mod_specials import store_area
from config import DB_LOGIN
from sqlalchemy import create_engine
import h5py

galaxy_id = 276
h5_file = h5py.File('testfile', 'w')
galaxy_group = h5_file.create_group('galaxy')
area_group = galaxy_group.create_group('area')

engine = create_engine(DB_LOGIN)
connection = engine.connect()

store_area(connection, galaxy_id, area_group)

h5_file.flush()
h5_file.close()
