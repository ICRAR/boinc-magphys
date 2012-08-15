"""
Build a fits image from the data in the database
"""
import argparse
import logging
from datetime import datetime
import numpy
import pyfits
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
from config import db_login
from database.database_support import Galaxy, PixelResult, FitsHeader
from utils.writeable_dir import WriteableDir

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Build images from the POGS results')
parser.add_argument('-o','--output_dir', action=WriteableDir, nargs=1, help='where the images will be written')
parser.add_argument('names', nargs='*', help='optional the name of tha galaxies to produce')
args = vars(parser.parse_args())

output_directory = args['output_dir']

# First check the galaxy exists in the database
engine = create_engine(db_login)
Session = sessionmaker(bind=engine)
session = Session()

if len(args['names']) > 0:
    LOG.info('Building FITS files for the galaxies {0}\n'.format(args['names']))
    query = session.query(Galaxy).filter(Galaxy.name.in_(args['names']))
else:
    LOG.info('Building FITS files for all the galaxies\n')
    query = session.query(Galaxy)

galaxies = query.all()

IMAGE_NAMES = [ 'fmu_sfh',
                'fmu_ir',
                'mu',
                'tauv',
                's_sfr',
                'm',
                'ldust',
                't_w_bc',
                't_c_ism',
                'xi_c_tot',
                'xi_pah_tot',
                'xi_mir_tot',
                'x_w_tot',
                'tvism',
                'mdust',
                'sfr',
              ]

for galaxy in galaxies:
    LOG.info('Working on galaxy %s\n', galaxy.name)
    array = numpy.empty((galaxy.dimension_x, galaxy.dimension_y, len(IMAGE_NAMES)), dtype=numpy.float)
    array.fill(numpy.NaN)

    # Get the header values
    header = {}
    for row in session.query(FitsHeader).filter(FitsHeader.galaxy_id == galaxy.galaxy_id).all():
        header[row.keyword] = row.value

    # Return the rows
    for row in session.query(PixelResult).filter(PixelResult.galaxy_id == galaxy.galaxy_id).all():
        array[row.x, row.y, 0] = row.fmu_sfh
        array[row.x, row.y, 1] = row.fmu_ir
        array[row.x, row.y, 2] = row.mu
        array[row.x, row.y, 3] = row.tauv
        array[row.x, row.y, 4] = row.s_sfr
        array[row.x, row.y, 5] = row.m
        array[row.x, row.y, 6] = row.ldust
        array[row.x, row.y, 7] = row.t_w_bc
        array[row.x, row.y, 8] = row.t_c_ism
        array[row.x, row.y, 9] = row.xi_c_tot
        array[row.x, row.y, 10] = row.xi_pah_tot
        array[row.x, row.y, 11] = row.xi_mir_tot
        array[row.x, row.y, 12] = row.x_w_tot
        array[row.x, row.y, 13] = row.tvism
        array[row.x, row.y, 14] = row.mdust
        array[row.x, row.y, 15] = row.sfr

    name_count = 0
    for name in IMAGE_NAMES:
        hdu = pyfits.PrimaryHDU(array[:,:,name_count])
        hdu_list = pyfits.HDUList([hdu])
        # Write the header
        hdu_list[0].header.update('MAGPHYST', name, 'MAGPHYS Parameter')
        hdu_list[0].header.update('DATE', datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%S'))
        for key, value in header.items():
            hdu_list[0].header.update(key, value)

        hdu_list.writeto('{0}/{1}_{2}.fits'.format(output_directory, galaxy.name, name), clobber=True)
        name_count += 1
