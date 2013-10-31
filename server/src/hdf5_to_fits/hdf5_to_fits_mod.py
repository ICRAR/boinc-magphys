#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
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
The functions to convert an HDF5 layer to a fits file
"""
import traceback
import pyfits
import os
import shutil
import smtplib
import tarfile
import tempfile
import numpy
import h5py
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from sqlalchemy import select
from sqlalchemy.sql.expression import distinct
from archive.archive_hdf5_mod import OUTPUT_FORMAT_1_03, get_chunks, OUTPUT_FORMAT_1_00, get_size, MAX_X_Y_BLOCK
from config import DELETED, STORED
from database.database_support_core import HDF5_FEATURE, HDF5_REQUEST_FEATURE, HDF5_REQUEST_LAYER, HDF5_LAYER, GALAXY, HDF5_REQUEST_GALAXY
from utils.logging_helper import config_logger
from utils.name_builder import get_key_hdf5, get_files_bucket, get_downloads_bucket, get_hdf5_to_fits_key, get_downloads_url
from utils.s3_helper import S3Helper
from os.path import dirname, exists
from configobj import ConfigObj

LOG = config_logger(__name__)

FROM_EMAIL = None
SMTP_SERVER = None
PORT = 0
EMAIL_USERNAME = None
EMAIL_PASSWORD = None

db_file_name = dirname(__file__) + '/hdf5_to_fits.settings'
if exists(db_file_name):
    config = ConfigObj(db_file_name)
    FROM_EMAIL = config['FROM_EMAIL']
    SMTP_SERVER = config['SMTP_SERVER']
    PORT = int(config['PORT'])
    EMAIL_USERNAME = config['EMAIL_USERNAME']
    EMAIL_PASSWORD = config['EMAIL_PASSWORD']

else:
    FROM_EMAIL = 'kevin.vinsen@icrar.org'
    SMTP_SERVER = 'smtp.ivec.org'

print("""
FROM_EMAIL       = {0}
SMTP_SERVER      = {1}""".format(FROM_EMAIL, SMTP_SERVER))

FEATURES = {
    'best_fit': 0,
    'percentile_50': 1,
    'highest_prob_bin': 2,
    'percentile_2_5': 3,
    'percentile_16': 4,
    'percentile_84': 5,
    'percentile_97_5': 6,
}

LAYERS = {
    'f_mu_sfh': 0,
    'f_mu_ir': 1,
    'mu_parameter': 2,
    'tau_v': 3,
    'ssfr_0_1gyr': 4,
    'm_stars': 5,
    'l_dust': 6,
    't_c_ism': 7,
    't_w_bc': 8,
    'xi_c_tot': 9,
    'xi_pah_tot': 10,
    'xi_mir_tot': 11,
    'xi_w_tot': 12,
    'tau_v_ism': 13,
    'm_dust': 14,
    'sfr_0_1gyr': 15,
}


def get_features_layers_galaxies(connection, request_id):
    """
    Get the features, layers and hdf5_request_galaxy_ids
    :param connection: the database connection
    :param request_id: the request id
    :return:
    """
    features = []
    for feature in connection.execute(select([HDF5_FEATURE], distinct=True).select_from(HDF5_FEATURE.join(HDF5_REQUEST_FEATURE)).where(HDF5_REQUEST_FEATURE.c.hdf5_request_id == request_id)):
        if feature[HDF5_FEATURE.c.argument_name] == 'f0':
            features.append('best_fit')
        if feature[HDF5_FEATURE.c.argument_name] == 'f1':
            features.append('percentile_50')
        if feature[HDF5_FEATURE.c.argument_name] == 'f2':
            features.append('highest_prob_bin')
        if feature[HDF5_FEATURE.c.argument_name] == 'f3':
            features.append('percentile_2_5')
        if feature[HDF5_FEATURE.c.argument_name] == 'f4':
            features.append('percentile_16')
        if feature[HDF5_FEATURE.c.argument_name] == 'f5':
            features.append('percentile_84')
        if feature[HDF5_FEATURE.c.argument_name] == 'f6':
            features.append('percentile_97_5')

    layers = []
    for layer in connection.execute(select([HDF5_LAYER], distinct=True).select_from(HDF5_LAYER.join(HDF5_REQUEST_LAYER)).where(HDF5_REQUEST_LAYER.c.hdf5_request_id == request_id)):
        if layer[HDF5_LAYER.c.argument_name] == 'l0':
            layers.append('f_mu_sfh')
        if layer[HDF5_LAYER.c.argument_name] == 'l1':
            layers.append('f_mu_ir')
        if layer[HDF5_LAYER.c.argument_name] == 'l2':
            layers.append('mu_parameter')
        if layer[HDF5_LAYER.c.argument_name] == 'l3':
            layers.append('tau_v')
        if layer[HDF5_LAYER.c.argument_name] == 'l4':
            layers.append('ssfr_0_1gyr')
        if layer[HDF5_LAYER.c.argument_name] == 'l5':
            layers.append('m_stars')
        if layer[HDF5_LAYER.c.argument_name] == 'l6':
            layers.append('l_dust')
        if layer[HDF5_LAYER.c.argument_name] == 'l7':
            layers.append('t_c_ism')
        if layer[HDF5_LAYER.c.argument_name] == 'l8':
            layers.append('t_w_bc')
        if layer[HDF5_LAYER.c.argument_name] == 'l9':
            layers.append('xi_c_tot')
        if layer[HDF5_LAYER.c.argument_name] == 'l10':
            layers.append('xi_pah_tot')
        if layer[HDF5_LAYER.c.argument_name] == 'l11':
            layers.append('xi_mir_tot')
        if layer[HDF5_LAYER.c.argument_name] == 'l12':
            layers.append('xi_w_tot')
        if layer[HDF5_LAYER.c.argument_name] == 'l13':
            layers.append('tau_v_ism')
        if layer[HDF5_LAYER.c.argument_name] == 'l14':
            layers.append('m_dust')
        if layer[HDF5_LAYER.c.argument_name] == 'l15':
            layers.append('sfr_0_1gyr')

    hdf5_request_galaxy_ids = []
    for galaxy_request in connection.execute(select([HDF5_REQUEST_GALAXY], distinct=True).where(HDF5_REQUEST_GALAXY.c.hdf5_request_id == request_id)):
        hdf5_request_galaxy_ids.append(HDF5RequestDetails(galaxy_request[HDF5_REQUEST_GALAXY.c.hdf5_request_galaxy_id], galaxy_request[HDF5_REQUEST_GALAXY.c.galaxy_id]))

    return features, layers, hdf5_request_galaxy_ids


def get_features_and_layers_cmd_line(args):
    """
    Get the features and layers
    :param args:
    :return:
    """
    features = []
    if args['best_fit']:
        features.append('best_fit')
    if args['percentile_50']:
        features.append('percentile_50')
    if args['highest_prob_bin']:
        features.append('highest_prob_bin')
    if args['percentile_2_5']:
        features.append('percentile_2_5')
    if args['percentile_16']:
        features.append('percentile_16')
    if args['percentile_84']:
        features.append('percentile_84')
    if args['percentile_97_5']:
        features.append('percentile_97_5')

    layers = []
    if args['f_mu_sfh']:
        layers.append('f_mu_sfh')
    if args['f_mu_ir']:
        layers.append('f_mu_ir')
    if args['mu_parameter']:
        layers.append('mu_parameter')
    if args['tau_v']:
        layers.append('tau_v')
    if args['ssfr_0_1gyr']:
        layers.append('ssfr_0_1gyr')
    if args['m_stars']:
        layers.append('m_stars')
    if args['l_dust']:
        layers.append('l_dust')
    if args['t_c_ism']:
        layers.append('t_c_ism')
    if args['t_w_bc']:
        layers.append('t_w_bc')
    if args['xi_c_tot']:
        layers.append('xi_c_tot')
    if args['xi_pah_tot']:
        layers.append('xi_pah_tot')
    if args['xi_mir_tot']:
        layers.append('xi_mir_tot')
    if args['xi_w_tot']:
        layers.append('xi_w_tot')
    if args['tau_v_ism']:
        layers.append('tau_v_ism')
    if args['m_dust']:
        layers.append('m_dust')
    if args['sfr_0_1gyr']:
        layers.append('sfr_0_1gyr')

    return features, layers


def get_hdf5_file(s3Helper, output_dir, galaxy_name, run_id, galaxy_id):
    """
    Get the HDF file

    :param galaxy_name: the name of the galaxy
    :param run_id: the run id
    :param galaxy_id: the galaxy id
    :return:
    """
    bucket_name = get_files_bucket()
    key = get_key_hdf5(galaxy_name, run_id, galaxy_id)
    tmp_file = get_temp_file('.hdf5', 'pogs', output_dir)

    s3Helper.get_file_from_bucket(bucket_name=bucket_name, key_name=key, file_name=tmp_file)
    return tmp_file


def get_temp_file(extension, file_name, output_dir):
    """
    Get a temporary file
    """
    tmp = tempfile.mkstemp(extension, file_name, output_dir, False)
    tmp_file = tmp[0]
    os.close(tmp_file)
    return tmp[1]


def generate_files(connection, hdf5_request_galaxy_ids, email, features, layers):
    """
    Get the FITS files for this request

    :param hdf5_request_galaxy_ids: the galaxy id
    :param email:
    :param features:
    :param layers:
    :return:
    """
    uuid_string = str(uuid.uuid4())
    results = []
    for hdf5_request_galaxy in hdf5_request_galaxy_ids:
        result = HDF5ToFitsResult()
        results.append(result)
        connection.execute(HDF5_REQUEST_GALAXY.update().where(HDF5_REQUEST_GALAXY.c.hdf5_request_galaxy_id == hdf5_request_galaxy.hdf5_request_galaxy_id).values(state=1))
        try:
            galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == hdf5_request_galaxy.galaxy_id)).first()
            result.galaxy_name = galaxy[GALAXY.c.name]
            LOG.info('Processing {0} ({1}) for {2}'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.galaxy_id], email))

            # make sure the galaxy is available
            if galaxy[GALAXY.c.status_id] == STORED or galaxy[GALAXY.c.status_id] == DELETED:
                output_dir = tempfile.mkdtemp()
                try:
                    s3Helper = S3Helper()
                    LOG.info('Getting HDF5 file to {0}'.format(output_dir))
                    tmp_file = get_hdf5_file(s3Helper, output_dir, galaxy[GALAXY.c.name], galaxy[GALAXY.c.run_id], galaxy[GALAXY.c.galaxy_id])
                    LOG.info('File stored in {0}'.format(tmp_file))

                    # We have the file
                    if os.path.isfile(tmp_file):
                        h5_file = h5py.File(tmp_file, 'r')
                        galaxy_group = h5_file['galaxy']
                        pixel_group = galaxy_group['pixel']

                        file_names = []
                        for feature in features:
                            for layer in layers:
                                LOG.info('Processing {0} - {1}'.format(feature, layer))
                                file_names.append(build_fits_image(feature, layer, output_dir, galaxy_group, pixel_group, galaxy[GALAXY.c.name]))

                        h5_file.close()
                        url = zip_files(s3Helper, galaxy[GALAXY.c.name], uuid_string, file_names, output_dir)
                        connection.execute(HDF5_REQUEST_GALAXY.update().
                                           where(HDF5_REQUEST_GALAXY.c.hdf5_request_galaxy_id == hdf5_request_galaxy.hdf5_request_galaxy_id).
                                           values(state=2, link=url, link_expires_at=datetime.now() + timedelta(days=10)))
                        result.error = None
                        result.link = url
                finally:
                    # Delete the temp files now we're done
                    shutil.rmtree(output_dir)

            else:
                connection.execute(HDF5_REQUEST_GALAXY.update().
                                   where(HDF5_REQUEST_GALAXY.c.hdf5_request_galaxy_id == hdf5_request_galaxy.hdf5_request_galaxy_id).
                                   values(state=3))
                result.error = 'Cannot process {0} ({1}) as the HDF5 file has not been generated'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.galaxy_id])
                LOG.info(result.error)
        except:
            LOG.error('Major error')
            result.error = traceback.format_exc()
            connection.execute(HDF5_REQUEST_GALAXY.update().
                               where(HDF5_REQUEST_GALAXY.c.hdf5_request_galaxy_id == hdf5_request_galaxy.hdf5_request_galaxy_id).
                               values(state=3))

    send_email(email, results, features, layers)


def zip_files(s3Helper, galaxy_name, uuid_string, file_names, output_dir):
    """
    Zip the files and send the email

    :param galaxy_name: the galaxy to process
    :param email: the email to explain progress
    :param file_names: the fits files to be bundled
    :return:
    """
    # Tar up all the images
    tar_file = zip_up_files(galaxy_name, file_names, output_dir)

    # Copy to S3
    bucket_name = get_downloads_bucket()
    key = get_hdf5_to_fits_key(uuid_string, galaxy_name)
    s3Helper.add_file_to_bucket(bucket_name, key, tar_file)
    url = '{0}/{1}'.format(get_downloads_url(), key)

    return url


def send_email(email, results, features, layers):
    """
    Send and email to the user with a message
    :param email: the users email address
    :param results: the results
    :param features: the features
    :param layers: the layers
    :return:
    """
    subject, message = get_final_message(results, features, layers)
    # Build the message
    LOG.info('''send_email {0}
{1}
{2}'''.format(email, subject, message))
    message = MIMEText(message)
    message['Subject'] = subject
    message['To'] = email
    message['From'] = FROM_EMAIL

    # Send it - connect to the server
    smtp = smtplib.SMTP(SMTP_SERVER, PORT)

    # Do we have a username / password
    if EMAIL_USERNAME is not None and EMAIL_PASSWORD is not None:
        smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    smtp.sendmail(FROM_EMAIL, [email], message.as_string())
    smtp.quit()


def zip_up_files(galaxy_name, file_names, output_dir):
    """
    Zip all the files up into a file

    :param output_dir: the output directory
    :param galaxy_name: the galaxy name
    :param file_names: the files to add
    :return:
    """
    tar_file_name = get_temp_file('.tar.gz', galaxy_name, output_dir)
    with tarfile.open(tar_file_name, 'w:gz') as tar_file:
        for file_name in file_names:
            tar_file.add(file_name, arcname=os.path.basename(file_name))
            os.remove(file_name)

    return tar_file_name


def get_final_message(results, features, layers):
    """
    Build the email message to send

    :param results: the UUID string
    :param features: the features
    :param layers: the layers
    :return: the built message
    """
    subject = ''
    string = 'You requested the following galaxies:\n'
    galaxy_count = 0
    for result in results:
        string += ' * {0}\n'.format(result.galaxy_name)
        if galaxy_count == 0:
            subject = result.galaxy_name
        elif galaxy_count < 10:
            subject += ', {0}'.format(result.galaxy_name)

        elif galaxy_count == 10:
            subject += ', ...'
        galaxy_count += 1

    string += 'The following features:\n'
    for feature in features:
        string += ' * {0}\n'.format(feature)

    string += 'The following layers:\n'
    for layer in layers:
        string += ' * {0}\n'.format(layer)

    string += '''
These files have been put in a gzip files one per galaxy. The files will be available for 10 days and will then be deleted. The links are as follows:
'''
    errors = False
    for result in results:
        if result.error is None:
            string += ' * {0} {1}\n'.format(result.galaxy_name, result.link)
        else:
            errors = True

    if errors:
        string += ''' The following errors occurred:
'''
        for result in results:
            if result.error is not None:
                string += '''-- {0} --
{1}
'''.format(result.galaxy_name, result.error)
    return subject, string


def build_fits_image(feature, layer, output_directory, galaxy_group, pixel_group, galaxy_name):
    """
    Extract a feature from the HDF5 file into a FITS file

    :param feature: the feature we want
    :param layer: the layer we want
    :param output_directory: where to write the result
    :param galaxy_group: the hdf5 galaxy_group
    :param pixel_group: the hdf5 pixel_group
    :return:
    """
    feature_index = FEATURES[feature]
    layer_index = LAYERS[layer]

    # I need to reshape the array as pyfits uses y, x whilst the hdf5 uses x, y
    dimension_x = galaxy_group.attrs['dimension_x']
    dimension_y = galaxy_group.attrs['dimension_y']
    data = numpy.empty((dimension_y, dimension_x), dtype=numpy.float)
    data.fill(numpy.NaN)

    output_format = galaxy_group.attrs['output_format']
    if output_format == OUTPUT_FORMAT_1_03:
        # If we only have one block then quickly copy it
        if dimension_x <= MAX_X_Y_BLOCK and dimension_y <= MAX_X_Y_BLOCK:
            pixel_data = pixel_group['pixels_0_0']
            for x in range(dimension_x):
                data[:, x] = pixel_data[x, :, layer_index, feature_index]
        else:
            for block_x in get_chunks(dimension_x):
                for block_y in get_chunks(dimension_y):
                    pixel_data = pixel_group['pixels_{0}_{1}'.format(block_x, block_y)]

                    size_x = get_size(block_x, dimension_x)
                    size_y = get_size(block_y, dimension_y)

                    x_offset = block_x * MAX_X_Y_BLOCK
                    y_offset = block_y * MAX_X_Y_BLOCK
                    # Copy the block back
                    for x in range(size_x):
                        data[y_offset:y_offset+size_y, x + x_offset] = pixel_data[x, :, layer_index, feature_index]
    else:
        pixel_data = pixel_group['pixels']

        for x in range(dimension_x):
            data[:, x] = pixel_data[x, :, layer_index, feature_index]

    utc_now = datetime.utcnow().strftime('%Y-%m-%dT%H:%m:%S')
    hdu = pyfits.PrimaryHDU(data)
    hdu_list = pyfits.HDUList([hdu])

    # Write our details first in the header
    hdu_list[0].header.update('MAGPHYST', layer, 'MAGPHYS Parameter')
    hdu_list[0].header.update('DATE', utc_now, 'Creation UTC (CCCC-MM-DD) date of FITS header')
    hdu_list[0].header.update('GALAXYID', galaxy_group.attrs['galaxy_id'], 'The POGS Galaxy Id')
    hdu_list[0].header.update('REDSHIFT', str(galaxy_group.attrs['redshift']), 'The POGS Galaxy redshift')
    hdu_list[0].header.update('SIGMA', str(galaxy_group.attrs['sigma']), 'The POGS Galaxy sigma')
    hdu_list[0].header.update('RUNID', galaxy_group.attrs['run_id'], 'The POGS run id')

    for fits_header in galaxy_group['fits_header']:
        keyword = fits_header[0]
        if keyword not in ['SIMPLE', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2', 'EXTEND', 'DATE']:
            if output_format == OUTPUT_FORMAT_1_00 or keyword == 'COMMENT' or keyword == 'HISTORY':
                hdu_list[0].header.update(keyword, fits_header[1])
            else:
                hdu_list[0].header.update(keyword, fits_header[1], fits_header[2])

    # Write the file
    file_name = os.path.join(output_directory, '{0}.{1}.{2}.fits'.format(galaxy_name, feature, layer))
    hdu_list.writeto(file_name, clobber=True)
    return file_name


class HDF5RequestDetails:
    def __init__(self, hdf5_request_galaxy_id, galaxy_id):
        self.hdf5_request_galaxy_id = hdf5_request_galaxy_id
        self.galaxy_id = galaxy_id


class HDF5ToFitsResult:
    def __init__(self):
        self.link = None
        self.error = None
        self.galaxy_name = None
