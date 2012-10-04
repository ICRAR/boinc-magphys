#! /usr/bin/env python2.7
"""
Build a fits image from the data in the database
"""
from __future__ import print_function
import argparse
import glob
import logging
from datetime import datetime
import os
import numpy
import pyfits
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker
import sys
from sqlalchemy.sql.expression import func, and_
from config import db_login
from database.database_support import Galaxy, PixelResult, FitsHeader, PixelParameter, Area, PixelHistogram
from utils.writeable_dir import WriteableDir

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Build images from the POGS results')
parser.add_argument('-o','--output_dir', action=WriteableDir, nargs=1, help='where the images will be written')
parser.add_argument('-m', '--median', action='store_true', help='also generate the images using the median value')
parser.add_argument('-p', '--highest_prob_bin_v', action='store_true', help='also generate the images using the highest probability bin value')
parser.add_argument('names', nargs='*', help='optional the name of tha galaxies to produce')
args = vars(parser.parse_args())

output_directory = args['output_dir']

# First check the galaxy exists in the database
engine = create_engine(db_login)
Session = sessionmaker(bind=engine)
session = Session()

if len(args['names']) > 0:
    LOG.info('Building FITS files for the galaxies {0}'.format(args['names']))
    query = session.query(Galaxy).filter(Galaxy.name.in_(args['names']))
else:
    LOG.info('Building FITS files for all the galaxies')
    query = session.query(Galaxy)

galaxies = query.all()

PARAMETER_NAMES = { 'f_mu (IR)'    : ['f_mu_ir',      0],
                    'f_mu (SFH)'   : ['f_mu_sfh',     1],
                    'Ldust'        : ['ldust',        2],
                    'M(dust)'      : ['m_dust',       3],
                    'M(stars)'     : ['m_stars',      4],
                    'mu parameter' : ['mu_paramater', 5],
                    'SFR_0.1Gyr'   : ['sfr',          6],
                    'sSFR_0.1Gyr'  : ['s_sfr',        7],
                    'tau_V'        : ['tau_v',        8],
                    'tau_V^ISM'    : ['tau_v_ism',    9],
                    'T_C^ISM'      : ['t_c_ism',      10],
                    'T_W^BC'       : ['t_w_bc',       11],
                    'xi_C^tot'     : ['xi_c_tot',     12],
                    'xi_MIR^tot'   : ['xi_mir_tot',   13],
                    'xi_PAH^tot'   : ['xi_pah_tot',   14],
                    'xi_W^tot'     : ['xi_w_tot',     15],
                  }

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

def get_index(parameter_name):
    """
    Find the plane we should be using
    """
    tuple = PARAMETER_NAMES[parameter_name]
    if tuple is not None:
        return tuple[1]

    raise AttributeError('Invalid parameter {0}'.format(pixel_parameter.parameter_name))

def check_need_to_run(directory, galaxy):
    """
    Find out if any pixels have arrived since we processed the images in the directory
    """
    min_mtime = None
    for filename in glob.glob(directory + "/*"):
        mtime = os.path.getmtime(filename)
        if min_mtime is None:
            min_mtime = mtime
        else:
            min_mtime = min(min_mtime, mtime)

    # No files exist
    if min_mtime is None:
        return True

    # Convert to a datetime
    min_mtime = datetime.fromtimestamp(min_mtime)

    update_time = session.query(func.max(Area.update_time)).filter('galaxy_id = :galaxy_id').params(galaxy_id=galaxy.galaxy_id).first()
    LOG.info('{0}_V{1} file min_mtime = {2} - DB update_time = {3}'.format(galaxy.name, galaxy.version_number, min_mtime, update_time[0]))
    if update_time[0] is None:
        return False
    return update_time[0] > min_mtime

median = args['median']
highest_prob_bin_v_ = args['highest_prob_bin_v']

for galaxy in galaxies:
    LOG.info('Working on galaxy %s (%d) %d x %d', galaxy.name, galaxy.version_number, galaxy.dimension_x, galaxy.dimension_y)

    # Do we have an old version
    need_to_run = True

    # Create the directory to hold the fits files
    if galaxy.version_number == 1:
        directory = '{0}/{1}'.format(output_directory, galaxy.name)
    else:
        directory = '{0}/{1}_V{2}'.format(output_directory, galaxy.name, galaxy.version_number)

    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        need_to_run = check_need_to_run(directory, galaxy)

    # If we don't need to run - don't
    if not need_to_run:
        continue

    # A vagary of PyFits/NumPy is the order of the x & y indexes is reversed
    # See page 13 of the PyFITS User Guide
    array_best_fit = numpy.empty((galaxy.dimension_y, galaxy.dimension_x, len(IMAGE_NAMES)), dtype=numpy.float)
    array_best_fit.fill(numpy.NaN)

    array_median = None
    if median:
        array_median = numpy.empty((galaxy.dimension_y, galaxy.dimension_x, len(PARAMETER_NAMES)), dtype=numpy.float)
        array_median.fill(numpy.NaN)

    array_highest_prob_bin_v = None
    if highest_prob_bin_v_:
        array_highest_prob_bin_v = numpy.empty((galaxy.dimension_y, galaxy.dimension_x, len(PARAMETER_NAMES)), dtype=numpy.float)
        array_highest_prob_bin_v.fill(numpy.NaN)

    # Get the header values
    header = {}
    for row in session.query(FitsHeader).filter(FitsHeader.galaxy_id == galaxy.galaxy_id).all():
        header[row.keyword] = row.value

    # Return the rows
    previous_x = -1
    for row in session.query(PixelResult).filter(PixelResult.galaxy_id == galaxy.galaxy_id).all():
        if row.x != previous_x:
            previous_x = row.x
            print("Processing row {0}".format(previous_x), end="\r")
            sys.stdout.flush()
        array_best_fit[row.y, row.x, 0] = row.fmu_sfh
        array_best_fit[row.y, row.x, 1] = row.fmu_ir
        array_best_fit[row.y, row.x, 2] = row.mu
        array_best_fit[row.y, row.x, 3] = row.tauv
        array_best_fit[row.y, row.x, 4] = row.s_sfr
        array_best_fit[row.y, row.x, 5] = row.m
        array_best_fit[row.y, row.x, 6] = row.ldust
        array_best_fit[row.y, row.x, 7] = row.t_w_bc
        array_best_fit[row.y, row.x, 8] = row.t_c_ism
        array_best_fit[row.y, row.x, 9] = row.xi_c_tot
        array_best_fit[row.y, row.x, 10] = row.xi_pah_tot
        array_best_fit[row.y, row.x, 11] = row.xi_mir_tot
        array_best_fit[row.y, row.x, 12] = row.x_w_tot
        array_best_fit[row.y, row.x, 13] = row.tvism
        array_best_fit[row.y, row.x, 14] = row.mdust
        array_best_fit[row.y, row.x, 15] = row.sfr

        if median or highest_prob_bin_v_:
            for pixel_parameter in session.query(PixelParameter).filter(PixelParameter.pxresult_id == row.pxresult_id).all():
                index = get_index(pixel_parameter.parameter_name)
                if median:
                    array_median[row.y, row.x, index] = pixel_parameter.percentile50

                if highest_prob_bin_v_:
                    # Have we worked this value out before
                    if pixel_parameter.high_prob_bin_value is None:
                        mhv = session.query(func.max(PixelHistogram.hist_value).label('max_hist_value')).filter(
                            and_(PixelHistogram.pxresult_id == row.pxresult_id,
                                PixelHistogram.pxparameter_id == pixel_parameter.pxparameter_id)).subquery('mhv')
                        pixel_histogram = session.query(PixelHistogram).filter(
                            and_(PixelHistogram.pxresult_id == row.pxresult_id,
                                PixelHistogram.pxparameter_id == pixel_parameter.pxparameter_id,
                                PixelHistogram.hist_value == mhv.c.max_hist_value)).first()

                        if pixel_histogram is not None:
                            array_highest_prob_bin_v[row.y, row.x, index] = pixel_histogram.x_axis
                            pixel_parameter.high_prob_bin_value = pixel_histogram.x_axis

                    else:
                        array_highest_prob_bin_v[row.y, row.x, index] = pixel_parameter.high_prob_bin_value

    # Commit any changes
    session.commit()

    name_count = 0
    for name in IMAGE_NAMES:
        hdu = pyfits.PrimaryHDU(array_best_fit[:,:,name_count])
        hdu_list = pyfits.HDUList([hdu])
        # Write the header
        hdu_list[0].header.update('MAGPHYST', name, 'MAGPHYS Parameter')
        hdu_list[0].header.update('DATE', datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%S'))
        hdu_list[0].header.update('GALAXYID', galaxy.galaxy_id, 'The POGS Galaxy Id')
        hdu_list[0].header.update('VRSNNMBR', galaxy.version_number, 'The POGS Galaxy Version Number')
        hdu_list[0].header.update('REDSHIFT', galaxy.redshift, 'The POGS Galaxy redshift')
        hdu_list[0].header.update('SIGMA', galaxy.sigma, 'The POGS Galaxy sigma')

        for key, value in header.items():
            hdu_list[0].header.update(key, value)

        if galaxy.version_number == 1:
            hdu_list.writeto('{0}/{1}_{2}.fits'.format(directory, galaxy.name, name), clobber=True)
        else:
            hdu_list.writeto('{0}/{1}_V{3}_{2}.fits'.format(directory, galaxy.name, name, galaxy.version_number), clobber=True)
        name_count += 1

    # If the medians are required produce them
    if median and array_median is not None:
        for k, tuple in PARAMETER_NAMES.iteritems():
            hdu = pyfits.PrimaryHDU(array_median[:,:,tuple[1]])
            hdu_list = pyfits.HDUList([hdu])
            # Write the header
            hdu_list[0].header.update('MAGPHYST', k, 'MAGPHYS Parameter Median')
            hdu_list[0].header.update('DATE', datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%S'))
            hdu_list[0].header.update('GALAXYID', galaxy.galaxy_id, 'The POGS Galaxy Id')
            hdu_list[0].header.update('VRSNNMBR', galaxy.version_number, 'The POGS Galaxy Version Number')
            hdu_list[0].header.update('REDSHIFT', galaxy.redshift, 'The POGS Galaxy redshift')
            hdu_list[0].header.update('SIGMA', galaxy.sigma, 'The POGS Galaxy sigma')

            for key, value in header.items():
                hdu_list[0].header.update(key, value)

            if galaxy.version_number == 1:
                hdu_list.writeto('{0}/{1}_{2}_median.fits'.format(directory, galaxy.name, tuple[0]), clobber=True)
            else:
                hdu_list.writeto('{0}/{1}_V{3}_{2}_median.fits'.format(directory, galaxy.name, tuple[0], galaxy.version_number), clobber=True)

    if highest_prob_bin_v_ and array_highest_prob_bin_v is not None:
        for k, tuple in PARAMETER_NAMES.iteritems():
            hdu = pyfits.PrimaryHDU(array_highest_prob_bin_v[:,:,tuple[1]])
            hdu_list = pyfits.HDUList([hdu])
            # Write the header
            hdu_list[0].header.update('MAGPHYST', k, 'MAGPHYS Parameter Highest Probability Bin Value')
            hdu_list[0].header.update('DATE', datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%S'))
            hdu_list[0].header.update('GALAXYID', galaxy.galaxy_id, 'The POGS Galaxy Id')
            hdu_list[0].header.update('VRSNNMBR', galaxy.version_number, 'The POGS Galaxy Version Number')
            hdu_list[0].header.update('REDSHIFT', galaxy.redshift, 'The POGS Galaxy redshift')
            hdu_list[0].header.update('SIGMA', galaxy.sigma, 'The POGS Galaxy sigma')

            for key, value in header.items():
                hdu_list[0].header.update(key, value)

            if galaxy.version_number == 1:
                hdu_list.writeto('{0}/{1}_{2}_high_prob_bin_value.fits'.format(directory, galaxy.name, tuple[0]), clobber=True)
            else:
                hdu_list.writeto('{0}/{1}_V{3}_{2}_high_prob_bin_value.fits'.format(directory, galaxy.name, tuple[0], galaxy.version_number), clobber=True)

LOG.info('Done')
