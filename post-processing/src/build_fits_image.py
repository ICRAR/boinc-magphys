#! /usr/bin/env python2.7
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
Build a fits image from the data in the database
"""
from __future__ import print_function
import argparse
import glob
import logging
import os
import numpy
import pyfits
import sys
from string import maketrans
from datetime import datetime
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func, and_
from config import DB_LOGIN
from database.database_support_core import PARAMETER_NAME, AREA, GALAXY, FITS_HEADER, PIXEL_RESULT, PIXEL_PARAMETER, PIXEL_HISTOGRAM
from utils.writeable_dir import WriteableDir

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

parser = argparse.ArgumentParser('Build images from the POGS results')
parser.add_argument('-o','--output_dir', action=WriteableDir, nargs=1, help='where the images will be written')
parser.add_argument('-m', '--median', action='store_true', help='also generate the images using the median value')
parser.add_argument('-p', '--highest_prob_bin_v', action='store_true', help='also generate the images using the highest probability bin value')
parser.add_argument('names', nargs='*', help='optional the name of tha galaxies to produce')
args = vars(parser.parse_args())

OUTPUT_DIRECTORY = args['output_dir']

# First check the galaxy exists in the database
engine = create_engine(DB_LOGIN)
connection = engine.connect()

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

    update_time = connection.execute(select([func.max(AREA.c.update_time)]).where(AREA.c.galaxy_id == galaxy[GALAXY.c.galaxy_id])).scalar()
    LOG.info('{0}_V{1} file min_mtime = {2} - DB update_time = {3}'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number], min_mtime, update_time))
    if update_time is None:
        return False
    return update_time > min_mtime

TRANSLATE_TABLE = maketrans(' ^', '__')
IMAGE_NAMES = []
for parameter_name in connection.execute(select([PARAMETER_NAME.c.name]).order_by(PARAMETER_NAME.c.parameter_name_id)):
    IMAGE_NAMES.append(parameter_name[0].translate(TRANSLATE_TABLE, '()'))


query = select([GALAXY])
if len(args['names']) > 0:
    LOG.info('Building FITS files for the galaxies {0}'.format(args['names']))
    query = query.where(GALAXY.c.name.in_(args['names']))
else:
    LOG.info('Building FITS files for all the galaxies')

median = args['median']
highest_prob_bin_v_ = args['highest_prob_bin_v']

for galaxy in connection.execute(query):
    galaxy__name = galaxy[GALAXY.c.name]
    galaxy__version_number = galaxy[GALAXY.c.version_number]
    galaxy__dimension_x = galaxy[GALAXY.c.dimension_x]
    galaxy__dimension_y = galaxy[GALAXY.c.dimension_y]
    LOG.info('Working on galaxy %s (%d) %d x %d', galaxy__name, galaxy__version_number, galaxy__dimension_x, galaxy__dimension_y)

    # Do we have an old version
    need_to_run = True

    # Create the directory to hold the fits files
    if galaxy__version_number == 1:
        directory = '{0}/{1}'.format(OUTPUT_DIRECTORY, galaxy__name)
    else:
        directory = '{0}/{1}_V{2}'.format(OUTPUT_DIRECTORY, galaxy__name, galaxy__version_number)

    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        need_to_run = check_need_to_run(directory, galaxy)

    # If we don't need to run - don't
    if not need_to_run:
        continue

    # A vagary of PyFits/NumPy is the order of the x & y indexes is reversed
    # See page 13 of the PyFITS User Guide
    array_best_fit = numpy.empty((galaxy__dimension_y, galaxy__dimension_x, len(IMAGE_NAMES)), dtype=numpy.float)
    array_best_fit.fill(numpy.NaN)

    array_median = None
    if median:
        array_median = numpy.empty((galaxy__dimension_y, galaxy__dimension_x, len(IMAGE_NAMES)), dtype=numpy.float)
        array_median.fill(numpy.NaN)

    array_highest_prob_bin_v = None
    if highest_prob_bin_v_:
        array_highest_prob_bin_v = numpy.empty((galaxy__dimension_y, galaxy__dimension_x, len(IMAGE_NAMES)), dtype=numpy.float)
        array_highest_prob_bin_v.fill(numpy.NaN)

    # Get the header values
    header = {}
    for row in connection.execute(select([FITS_HEADER]).where(FITS_HEADER.c.galaxy_id == galaxy[GALAXY.c.galaxy_id])):
        header[row[FITS_HEADER.c.keyword]] = row[FITS_HEADER.c.value]

    # Begin the transaction
    transaction = connection.begin()

    # Return the rows
    previous_x = -1
    for row in connection.execute(select([PIXEL_RESULT]).where(PIXEL_RESULT.c.galaxy_id == galaxy[GALAXY.c.galaxy_id])):
        row__x = row[PIXEL_RESULT.c.x]
        row__y = row[PIXEL_RESULT.c.y]
        if row__x != previous_x:
            previous_x = row__x
            print("Processing row {0}".format(previous_x), end="\r")
            sys.stdout.flush()
        array_best_fit[row__y, row__x, 0]  = row[PIXEL_RESULT.c.fmu_sfh]
        array_best_fit[row__y, row__x, 1]  = row[PIXEL_RESULT.c.fmu_ir]
        array_best_fit[row__y, row__x, 2]  = row[PIXEL_RESULT.c.mu]
        array_best_fit[row__y, row__x, 3]  = row[PIXEL_RESULT.c.tauv]
        array_best_fit[row__y, row__x, 4]  = row[PIXEL_RESULT.c.s_sfr]
        array_best_fit[row__y, row__x, 5]  = row[PIXEL_RESULT.c.m]
        array_best_fit[row__y, row__x, 6]  = row[PIXEL_RESULT.c.ldust]
        array_best_fit[row__y, row__x, 7]  = row[PIXEL_RESULT.c.t_w_bc]
        array_best_fit[row__y, row__x, 8]  = row[PIXEL_RESULT.c.t_c_ism]
        array_best_fit[row__y, row__x, 9]  = row[PIXEL_RESULT.c.xi_c_tot]
        array_best_fit[row__y, row__x, 10] = row[PIXEL_RESULT.c.xi_pah_tot]
        array_best_fit[row__y, row__x, 11] = row[PIXEL_RESULT.c.xi_mir_tot]
        array_best_fit[row__y, row__x, 12] = row[PIXEL_RESULT.c.x_w_tot]
        array_best_fit[row__y, row__x, 13] = row[PIXEL_RESULT.c.tvism]
        array_best_fit[row__y, row__x, 14] = row[PIXEL_RESULT.c.mdust]
        array_best_fit[row__y, row__x, 15] = row[PIXEL_RESULT.c.sfr]

        if median or highest_prob_bin_v_:
            for pixel_parameter in connection.execute(select([PIXEL_PARAMETER]).where(PIXEL_PARAMETER.c.pxresult_id == row[PIXEL_RESULT.c.pxresult_id])):
                if 1 <= pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] <= 16:
                    index = pixel_parameter[PIXEL_PARAMETER.c.parameter_name_id] - 1
                    if median:
                        array_median[row__y, row__x, index] = pixel_parameter[PIXEL_PARAMETER.c.percentile50]

                    if highest_prob_bin_v_:
                        # Have we worked this value out before
                        if pixel_parameter[PIXEL_PARAMETER.c.high_prob_bin] is None:
                            pixel_histogram = connection.execute(select([PIXEL_HISTOGRAM]).where(
                                and_(PIXEL_HISTOGRAM.c.pxresult_id == row[PIXEL_RESULT.c.pxresult_id],
                                     PIXEL_HISTOGRAM.c.pxparameter_id == pixel_parameter[PIXEL_PARAMETER.c.pxparameter_id],
                                     PIXEL_HISTOGRAM.c.hist_value ==
                                        select([func.max(PIXEL_HISTOGRAM.c.hist_value)]).
                                            where(and_(PIXEL_HISTOGRAM.c.pxresult_id == row[PIXEL_RESULT.c.pxresult_id],
                                                       PIXEL_HISTOGRAM.c.pxparameter_id == pixel_parameter[PIXEL_PARAMETER.c.pxparameter_id]))))).first()


                            if pixel_histogram is not None:
                                array_highest_prob_bin_v[row__y, row__x, index] = pixel_histogram[PIXEL_HISTOGRAM.c.x_axis]

                                # Update the database
                                connection.execute(PIXEL_PARAMETER.update().
                                    where(PIXEL_PARAMETER.c.pxparameter_id == pixel_parameter[PIXEL_PARAMETER.c.pxparameter_id]).
                                    values(high_prob_bin = pixel_histogram[PIXEL_HISTOGRAM.c.x_axis]))

                        else:
                            array_highest_prob_bin_v[row__y, row__x, index] = pixel_parameter[PIXEL_PARAMETER.c.high_prob_bin]

    # Commit any changes
    transaction.commit()

    name_count = 0
    utc_now = datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%S')
    for name in IMAGE_NAMES:
        hdu = pyfits.PrimaryHDU(array_best_fit[:,:,name_count])
        hdu_list = pyfits.HDUList([hdu])
        # Write the header
        hdu_list[0].header.update('MAGPHYST', name, 'MAGPHYS Parameter')
        hdu_list[0].header.update('DATE', utc_now)
        hdu_list[0].header.update('GALAXYID', galaxy.galaxy_id, 'The POGS Galaxy Id')
        hdu_list[0].header.update('VRSNNMBR', galaxy.version_number, 'The POGS Galaxy Version Number')
        hdu_list[0].header.update('REDSHIFT', str(galaxy.redshift), 'The POGS Galaxy redshift')
        hdu_list[0].header.update('SIGMA', str(galaxy.sigma), 'The POGS Galaxy sigma')

        for key, value in header.items():
            hdu_list[0].header.update(key, value)

        if galaxy.version_number == 1:
            hdu_list.writeto('{0}/{1}_{2}.fits'.format(directory, galaxy__name, name), clobber=True)
        else:
            hdu_list.writeto('{0}/{1}_V{3}_{2}.fits'.format(directory, galaxy__name, name, galaxy.version_number), clobber=True)
        name_count += 1

    # If the medians are required produce them
    if median and array_median is not None:
        name_count = 0
        for name in IMAGE_NAMES:
            hdu = pyfits.PrimaryHDU(array_median[:,:,name_count])
            hdu_list = pyfits.HDUList([hdu])
            # Write the header
            hdu_list[0].header.update('MAGPHYST', name, 'MAGPHYS Parameter Median')
            hdu_list[0].header.update('DATE', utc_now)
            hdu_list[0].header.update('GALAXYID', galaxy.galaxy_id, 'The POGS Galaxy Id')
            hdu_list[0].header.update('VRSNNMBR', galaxy.version_number, 'The POGS Galaxy Version Number')
            hdu_list[0].header.update('REDSHIFT', str(galaxy.redshift), 'The POGS Galaxy redshift')
            hdu_list[0].header.update('SIGMA', str(galaxy.sigma), 'The POGS Galaxy sigma')

            for key, value in header.items():
                hdu_list[0].header.update(key, value)

            if galaxy.version_number == 1:
                hdu_list.writeto('{0}/{1}_{2}_median.fits'.format(directory, galaxy__name, name), clobber=True)
            else:
                hdu_list.writeto('{0}/{1}_V{3}_{2}_median.fits'.format(directory, galaxy__name, name, galaxy.version_number), clobber=True)
            name_count += 1

    if highest_prob_bin_v_ and array_highest_prob_bin_v is not None:
        name_count = 0
        for name in IMAGE_NAMES:
            hdu = pyfits.PrimaryHDU(array_highest_prob_bin_v[:,:,name_count])
            hdu_list = pyfits.HDUList([hdu])
            # Write the header
            hdu_list[0].header.update('MAGPHYST', name, 'MAGPHYS Parameter Highest Probability Bin Value')
            hdu_list[0].header.update('DATE', utc_now)
            hdu_list[0].header.update('GALAXYID', galaxy.galaxy_id, 'The POGS Galaxy Id')
            hdu_list[0].header.update('VRSNNMBR', galaxy.version_number, 'The POGS Galaxy Version Number')
            hdu_list[0].header.update('REDSHIFT', str(galaxy.redshift), 'The POGS Galaxy redshift')
            hdu_list[0].header.update('SIGMA', str(galaxy.sigma), 'The POGS Galaxy sigma')

            for key, value in header.items():
                hdu_list[0].header.update(key, value)

            if galaxy.version_number == 1:
                hdu_list.writeto('{0}/{1}_{2}_high_prob_bin.fits'.format(directory, galaxy__name, name), clobber=True)
            else:
                hdu_list.writeto('{0}/{1}_V{3}_{2}_high_prob_bin.fits'.format(directory, galaxy__name, name, galaxy.version_number), clobber=True)

LOG.info('Done')
