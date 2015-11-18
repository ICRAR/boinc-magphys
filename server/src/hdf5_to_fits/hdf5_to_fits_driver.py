__author__ = 'ict310'
from sqlalchemy import create_engine, select
from database.database_support_core import GALAXY
from hdf5_to_fits_mod import build_fits_image, zip_up_files
import os
import h5py
import shutil
from config import DB_LOGIN

engine = create_engine(DB_LOGIN)
connection = engine.connect()
galaxy = connection.execute(select([GALAXY]).where(GALAXY.c.galaxy_id == 94655)).first()

tmp_file = 'testfile.hdf5'

output_dir = os.path.abspath('./output')
int_flux_output = os.path.abspath('./output/intflux')
rad_output = os.path.abspath('./output/rad')

if not os.path.exists(output_dir):
    os.mkdir(output_dir)

if not os.path.exists(int_flux_output):
    os.mkdir(int_flux_output)

if not os.path.exists(rad_output):
    os.mkdir(rad_output)


TYPE_NORMAL = 0
TYPE_INT = 1
TYPE_RAD = 2

features = ['best_fit', 'percentile_50', 'highest_prob_bin', 'percentile_2_5', 'percentile_16', 'percentile_84', 'percentile_97_5']
layers = ['f_mu_sfh', 'f_mu_ir', 'mu_parameter', 'tau_v', 'ssfr_0_1gyr', 'm_stars', 'l_dust', 't_c_ism', 't_w_bc', 'xi_c_tot', 'xi_pah_tot', 'xi_mir_tot', 'xi_w_tot', 'tau_v_ism', 'm_dust', 'sfr_0_1gyr']
pixel_types = [TYPE_NORMAL, TYPE_RAD, TYPE_INT]

if os.path.isfile(tmp_file):
    int_flux_output = os.path.join(output_dir, 'intflux')
    rad_output = os.path.join(output_dir, 'rad')

    if not os.path.exists(int_flux_output):
        os.mkdir(int_flux_output)

    if not os.path.exists(rad_output):
        os.mkdir(rad_output)

    h5_file = h5py.File(tmp_file, 'r')
    galaxy_group = h5_file['galaxy']

    file_names = []
    int_file_names = []
    rad_file_names = []
    normal_file_names = []

    # Get each feature, then each layer and finally each pixel type.
    for feature in features:
        for layer in layers:
            for pixel_type in pixel_types:

                if pixel_type == TYPE_NORMAL:
                    pixel_group = galaxy_group['pixel']

                    file_names.append(build_fits_image(feature, layer, output_dir, galaxy_group,
                                                       galaxy_group.attrs['dimension_x'], galaxy_group.attrs['dimension_y'],
                                                       pixel_group, galaxy[GALAXY.c.name]))

                elif pixel_type == TYPE_INT:
                    pixel_group = galaxy_group['pixel']['special_pixels']['int_flux'] # galaxy/pixel/special_pixels/int_flux
                    build_fits_image(feature, layer, int_flux_output, galaxy_group,
                                     pixel_group.attrs['dimension_x'], pixel_group.attrs['dimension_y'],
                                     pixel_group, galaxy[GALAXY.c.name])

                elif pixel_type == TYPE_RAD:
                    pixel_group = galaxy_group['pixel']['special_pixels']['rad'] # galaxy/pixel/special_pixels/rad

                    build_fits_image(
                        feature,
                        layer,
                        rad_output,
                        galaxy_group,
                        pixel_group.attrs['dimension_x'],
                        pixel_group.attrs['dimension_y'],
                        pixel_group, galaxy[GALAXY.c.name]
                    )

    if len(int_file_names) > 0:
        file_names.append(int_flux_output)

    if len(rad_file_names) > 0:
        file_names.append(rad_output)

    zip_up_files(galaxy[GALAXY.c.name], file_names, output_dir)

    h5_file.close()
