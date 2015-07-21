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
The definitions for using SQLAlchemy Core

"""

from sqlalchemy import MetaData, Table, Column, Integer, String, Float, TIMESTAMP, ForeignKey, BigInteger, Numeric

##########################################################################
##########################################################################

##########################################################################
#
# If you change this file change the database_support.py file to
# match the change
#
##########################################################################

##########################################################################
##########################################################################

MAGPHYS_METADATA = MetaData()

AREA = Table('area',
             MAGPHYS_METADATA,
             Column('area_id', BigInteger, primary_key=True, autoincrement=True),
             Column('galaxy_id', BigInteger, ForeignKey('galaxy.galaxy_id')),
             Column('top_x', Integer),
             Column('top_y', Integer),
             Column('bottom_x', Integer),
             Column('bottom_y', Integer),
             Column('workunit_id', BigInteger),
             Column('update_time', TIMESTAMP)
             )

AREA_USER = Table('area_user',
                  MAGPHYS_METADATA,
                  Column('areauser_id', BigInteger, primary_key=True, autoincrement=True),
                  Column('area_id', BigInteger, ForeignKey('area.area_id')),
                  Column('userid', Integer),
                  Column('create_time', TIMESTAMP)
                  )

FILTER = Table('filter',
               MAGPHYS_METADATA,
               Column('filter_id', Integer, primary_key=True),
               Column('name', String(30)),
               Column('eff_lambda', Numeric(10, 4)),
               Column('filter_number', Integer),
               Column('ultraviolet', Integer),
               Column('optical', Integer),
               Column('infrared', Integer),
               Column('label', String(20))
               )

FITS_HEADER = Table('fits_header',
                    MAGPHYS_METADATA,
                    Column('fitsheader_id', BigInteger, primary_key=True, autoincrement=True),
                    Column('galaxy_id', BigInteger, ForeignKey('galaxy.galaxy_id')),
                    Column('keyword', String(128)),
                    Column('value', String(128)),
                    Column('comment', String(128)),
                    )

GALAXY = Table('galaxy',
               MAGPHYS_METADATA,
               Column('galaxy_id', BigInteger, primary_key=True, autoincrement=True),
               Column('run_id', BigInteger, ForeignKey('run.run_id')),
               Column('name', String(128)),
               Column('dimension_x', Integer),
               Column('dimension_y', Integer),
               Column('dimension_z', Integer),
               Column('redshift', Numeric(7, 5)),
               Column('create_time', TIMESTAMP),
               Column('image_time', TIMESTAMP),
               Column('version_number', Integer),
               Column('galaxy_type', String(10)),
               Column('ra_cent', Float),
               Column('dec_cent', Float),
               Column('sigma', Numeric(3, 2)),
               Column('pixel_count', Integer),
               Column('pixels_processed', Integer),
               Column('status_id', Integer, ForeignKey('galaxy_status.galaxy_status_id')),
               Column('status_time', TIMESTAMP),
               Column('original_image_checked', TIMESTAMP),
               )

GALAXY_STATUS = Table('galaxy_status',
                      MAGPHYS_METADATA,
                      Column('galaxy_status_id', Integer, primary_key=True),
                      Column('description', String(250)),
                      )

GALAXY_USER = Table('galaxy_user',
                    MAGPHYS_METADATA,
                    Column('galaxy_user_id', BigInteger, primary_key=True, autoincrement=True),
                    Column('galaxy_id', BigInteger, ForeignKey('galaxy.galaxy_id'), nullable=False),
                    Column('userid', Integer, nullable=False),
                    Column('create_at', TIMESTAMP, nullable=False)
                    )

IMAGE_FILTERS_USED = Table('image_filters_used',
                           MAGPHYS_METADATA,
                           Column('image_filters_used_id', BigInteger, primary_key=True),
                           Column('image_number', Integer),
                           Column('galaxy_id', BigInteger, ForeignKey('galaxy.galaxy_id')),
                           Column('filter_id_red', Integer, ForeignKey('filter.filter_id')),
                           Column('filter_id_green', Integer, ForeignKey('filter.filter_id')),
                           Column('filter_id_blue', Integer, ForeignKey('filter.filter_id')),
                           )

PARAMETER_NAME = Table('parameter_name',
                       MAGPHYS_METADATA,
                       Column('parameter_name_id', Integer, primary_key=True, autoincrement=True),
                       Column('name', String(100)),
                       Column('column_name', String(100)),
                       )

PIXEL_RESULT = Table('pixel_result',
                     MAGPHYS_METADATA,
                     Column('pxresult_id', BigInteger, primary_key=True, autoincrement=True),
                     Column('area_id', BigInteger, ForeignKey('area.area_id')),
                     Column('galaxy_id', BigInteger, ForeignKey('galaxy.galaxy_id')),
                     Column('x', Integer),
                     Column('y', Integer),
                     Column('workunit_id', BigInteger),
                     Column('fmu_sfh', Float),
                     Column('fmu_ir', Float),
                     Column('mu', Float),
                     Column('tauv', Float),
                     Column('s_sfr', Float),
                     Column('m', Float),
                     Column('ldust', Float),
                     Column('t_w_bc', Float),
                     Column('t_c_ism', Float),
                     Column('xi_c_tot', Float),
                     Column('xi_pah_tot', Float),
                     Column('xi_mir_tot', Float),
                     Column('xi_w_tot', Float),
                     Column('tvism', Float),
                     Column('mdust', Float),
                     Column('sfr', Float),
                     )

REGISTER = Table('register',
                 MAGPHYS_METADATA,
                 Column('register_id', BigInteger, primary_key=True, nullable=False),
                 Column('galaxy_name', String(128), nullable=False),
                 Column('redshift', Numeric(7, 5), nullable=False),
                 Column('sigma', Numeric(3, 2), nullable=False),
                 Column('galaxy_type', String(10), nullable=False),
                 Column('filename', String(1000), nullable=False),
                 Column('sigma_filename', String(1000)),
                 Column('rad_filename', String(1000)),
                 Column('rad_sigma_filename', String(1000)),
                 Column('int_filename', String(1000)),
                 Column('int_sigma_filename', String(1000)),
                 Column('priority', Integer, nullable=False),
                 Column('register_time', TIMESTAMP, nullable=False),
                 Column('create_time', TIMESTAMP),
                 Column('run_id', BigInteger, ForeignKey('run.run_id'), nullable=False)
                 )

RUN = Table('run',
            MAGPHYS_METADATA,
            Column('run_id', BigInteger, primary_key=True),
            Column('short_description', String(250)),
            Column('long_description', String(1000)),
            Column('directory', String(1000)),
            Column('fpops_est', Float),
            Column('cobblestone_factor', Float),
            )

RUN_FILTER = Table('run_filter',
                   MAGPHYS_METADATA,
                   Column('run_filter_id', BigInteger, primary_key=True),
                   Column('run_id', BigInteger, ForeignKey('run.run_id')),
                   Column('filter_id', BigInteger, ForeignKey('filter.filter_id'))
                   )

HDF5_REQUEST = Table('hdf5_request',
                     MAGPHYS_METADATA,
                     Column('hdf5_request_id', BigInteger, primary_key=True),
                     Column('profile_id', BigInteger, nullable=False),
                     Column('email', String(256), nullable=False),
                     Column('created_at', TIMESTAMP, nullable=False),
                     Column('updated_at', TIMESTAMP, nullable=False),
                     )

HDF5_FEATURE = Table('hdf5_feature',
                     MAGPHYS_METADATA,
                     Column('hdf5_feature_id', BigInteger, primary_key=True),
                     Column('argument_name', String(100), nullable=False),
                     Column('description', String(100), nullable=False),
                     Column('created_at', TIMESTAMP, nullable=False),
                     Column('updated_at', TIMESTAMP, nullable=False),
                     )

HDF5_LAYER = Table('hdf5_layer',
                   MAGPHYS_METADATA,
                   Column('hdf5_layer_id', BigInteger, primary_key=True),
                   Column('argument_name', String(100), nullable=False),
                   Column('description', String(100), nullable=False),
                   Column('created_at', TIMESTAMP, nullable=False),
                   Column('updated_at', TIMESTAMP, nullable=False),
                   )

HDF5_REQUEST_GALAXY = Table('hdf5_request_galaxy',
                            MAGPHYS_METADATA,
                            Column('hdf5_request_galaxy_id', BigInteger, primary_key=True),
                            Column('hdf5_request_id', BigInteger, ForeignKey('hdf5_request.hdf5_request_id')),
                            Column('galaxy_id', BigInteger, ForeignKey('galaxy.galaxy_id')),
                            Column('link', String(1000)),
                            Column('state', Integer, nullable=False),
                            Column('link_expires_at', TIMESTAMP)
                            )

HDF5_REQUEST_FEATURE = Table('hdf5_request_feature',
                             MAGPHYS_METADATA,
                             Column('hdf5_request_feature_id', BigInteger, primary_key=True),
                             Column('hdf5_request_id', BigInteger, ForeignKey('hdf5_request.hdf5_request_id')),
                             Column('hdf5_feature_id', BigInteger, ForeignKey('hdf5_feature.hdf5_feature_id')),
                             )

HDF5_REQUEST_LAYER = Table('hdf5_request_layer',
                           MAGPHYS_METADATA,
                           Column('hdf5_request_layer_id', BigInteger, primary_key=True),
                           Column('hdf5_request_id', BigInteger, ForeignKey('hdf5_request.hdf5_request_id')),
                           Column('hdf5_layer_id', BigInteger, ForeignKey('hdf5_layer.hdf5_layer_id')),
                           )

HDF5_REQUEST_PIXEL_TYPE = Table('hdf5_request_pixel_type',
                                MAGPHYS_METADATA,
                                Column('hdf5_request_pixel_type_id', BigInteger, primary_key=True),
                                Column('hdf5_request_id', BigInteger, ForeignKey('hdf5_request.hdf5_request_id')),
                                Column('hdf5_pixel_type_id', BigInteger, ForeignKey('hdf5_pixel_type.hdf5_pixel_type_id')),
                                )

HDF5_PIXEL_TYPE = Table('hdf5_pixel_type',
                        MAGPHYS_METADATA,
                        Column('hdf5_pixel_type_id', BigInteger, primary_key=True),
                        Column('argument_name', String(100), nullable=False),
                        Column('description', String(100), nullable=False),
                        Column('created_at', TIMESTAMP, nullable=False),
                        Column('updated_at', TIMESTAMP, nullable=False),
                        )

TAG = Table('tag',
            MAGPHYS_METADATA,
            Column('tag_id', BigInteger, primary_key=True),
            Column('tag_text', String(200), nullable=False),
            Column('created_at', TIMESTAMP, nullable=False),
            )

TAG_REGISTER = Table('tag_register',
                     MAGPHYS_METADATA,
                     Column('tag_register_id', BigInteger, primary_key=True),
                     Column('tag_id', BigInteger, ForeignKey('tag.tag_id')),
                     Column('register_id', BigInteger, ForeignKey('register.register_id')),
                     Column('created_at', TIMESTAMP, nullable=False),
                     )

TAG_GALAXY = Table('tag_galaxy',
                   MAGPHYS_METADATA,
                   Column('tag_galaxy_id', BigInteger, primary_key=True),
                   Column('tag_id', BigInteger, ForeignKey('tag.tag_id')),
                   Column('galaxy_id', BigInteger, ForeignKey('galaxy.galaxy_id')),
                   Column('created_at', TIMESTAMP, nullable=False),
                   )

USER_PIXEL = Table('user_pixel',
                   MAGPHYS_METADATA,
                   Column('userid', BigInteger, primary_key=True),
                   Column('pixel_count', Integer)
                   )
