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
The definitions for using SQLAlchemy Core

"""

from sqlalchemy import MetaData, Table, Column,Integer, String, Float, TIMESTAMP, ForeignKey, BigInteger, Boolean, Numeric

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
    Column('area_id'    , BigInteger, primary_key=True, autoincrement=True),
    Column('galaxy_id'  , BigInteger, ForeignKey('galaxy.galaxy_id')),
    Column('top_x'      , Integer),
    Column('top_y'      , Integer),
    Column('bottom_x'   , Integer),
    Column('bottom_y'   , Integer),
    Column('workunit_id', BigInteger),
    Column('update_time', TIMESTAMP)
)

AREA_USER = Table('area_user',
    MAGPHYS_METADATA,
    Column('areauser_id', BigInteger, primary_key=True, autoincrement=True),
    Column('area_id'    , BigInteger, ForeignKey('area.area_id')),
    Column('userid'     , Integer),
    Column('create_time', TIMESTAMP)
)

FILTER = Table('filter',
    MAGPHYS_METADATA,
    Column('filter_id'    , Integer, primary_key=True),
    Column('name'         , String(30)),
    Column('eff_lambda'   , Numeric(10,4)),
    Column('filter_number', Integer),
    Column('ultraviolet'  , Integer),
    Column('optical'      , Integer),
    Column('infrared'     , Integer),
    Column('label'        , String(20))
)

FITS_HEADER = Table('fits_header',
    MAGPHYS_METADATA,
    Column('fitsheader_id', BigInteger, primary_key=True, autoincrement=True),
    Column('galaxy_id'    , BigInteger, ForeignKey('galaxy.galaxy_id')),
    Column('keyword'      , String(128)),
    Column('value'        , String(128))
)

GALAXY = Table('galaxy',
    MAGPHYS_METADATA,
    Column('galaxy_id'       , BigInteger, primary_key=True, autoincrement=True),
    Column('run_id'          , BigInteger, ForeignKey('run.run_id')),
    Column('name'            , String(128)),
    Column('dimension_x'     , Integer),
    Column('dimension_y'     , Integer),
    Column('dimension_z'     , Integer),
    Column('redshift'        , Numeric(7,5)),
    Column('create_time'     , TIMESTAMP),
    Column('image_time'      , TIMESTAMP),
    Column('version_number'  , Integer),
    Column('current'         , Boolean),
    Column('galaxy_type'     , String(10)),
    Column('ra_cent'         , Float),
    Column('dec_cent'        , Float),
    Column('sigma'           , Numeric(3,2)),
    Column('pixel_count'     , Integer),
    Column('pixels_processed', Integer),
    Column('status_id'       , Integer, ForeignKey('galaxy_status.galaxy_status_id')),
)

GALAXY_STATUS = Table('galaxy_status',
    MAGPHYS_METADATA,
    Column('galaxy_status_id', Integer, primary_key=True),
    Column('description'     , String(250)),
)

IMAGE_FILTERS_USED = Table('image_filters_used',
    MAGPHYS_METADATA,
    Column('image_filters_used_id', BigInteger, primary_key=True),
    Column('image_number'         , Integer),
    Column('galaxy_id'            , BigInteger, ForeignKey('galaxy.galaxy_id')),
    Column('filter_id_red'        , Integer, ForeignKey('filter.filter_id')),
    Column('filter_id_green'      , Integer, ForeignKey('filter.filter_id')),
    Column('filter_id_blue'       , Integer, ForeignKey('filter.filter_id')),
)

PARAMETER_NAME = Table('parameter_name',
    MAGPHYS_METADATA,
    Column('parameter_name_id', Integer, primary_key=True, autoincrement=True),
    Column('name'             , String(100))
)

PIXEL_FILTER = Table('pixel_filter',
    MAGPHYS_METADATA,
    Column('pxfilter_id'              , BigInteger, primary_key=True, autoincrement=True),
    Column('pxresult_id'              , BigInteger, ForeignKey('pixel_result.pxresult_id')),
    Column('filter_name'              , String(100)),
    Column('observed_flux'            , Float),
    Column('observational_uncertainty', Float),
    Column('flux_bfm'                 , Float)
)

PIXEL_HISTOGRAM = Table('pixel_histogram',
    MAGPHYS_METADATA,
    Column('pxhistogram_id', BigInteger, primary_key=True, autoincrement=True),
    Column('pxparameter_id', BigInteger, ForeignKey('pixel_parameter.pxparameter_id')),
    Column('pxresult_id'   , BigInteger, ForeignKey('pixel_result.pxresult_id')),
    Column('x_axis'        , Float),
    Column('hist_value'    , Float)
)

PIXEL_PARAMETER = Table('pixel_parameter',
    MAGPHYS_METADATA,
    Column('pxparameter_id'   , BigInteger, primary_key=True, autoincrement=True),
    Column('pxresult_id'      , BigInteger, ForeignKey('pixel_result.pxresult_id')),
    Column('parameter_name_id', Integer),
    Column('percentile2_5'    , Float),
    Column('percentile16'     , Float),
    Column('percentile50'     , Float),
    Column('percentile84'     , Float),
    Column('percentile97_5'   , Float),
    Column('high_prob_bin'    , Float),
    Column('first_prob_bin'   , Float),
    Column('last_prob_bin'    , Float),
    Column('bin_step'         , Float)
)

PIXEL_RESULT = Table('pixel_result',
    MAGPHYS_METADATA,
    Column('pxresult_id', BigInteger, primary_key=True, autoincrement=True),
    Column('area_id'    , BigInteger, ForeignKey('area.area_id')),
    Column('galaxy_id'  , BigInteger, ForeignKey('galaxy.galaxy_id')),
    Column('x'          , Integer),
    Column('y'          , Integer),
    Column('workunit_id', BigInteger),
    Column('i_sfh'      , Float),
    Column('i_ir'       , Float),
    Column('chi2'       , Float),
    Column('redshift'   , Float),
    Column('fmu_sfh'    , Float),
    Column('fmu_ir'     , Float),
    Column('mu'         , Float),
    Column('tauv'       , Float),
    Column('s_sfr'      , Float),
    Column('m'          , Float),
    Column('ldust'      , Float),
    Column('t_w_bc'     , Float),
    Column('t_c_ism'    , Float),
    Column('xi_c_tot'   , Float),
    Column('xi_pah_tot' , Float),
    Column('xi_mir_tot' , Float),
    Column('x_w_tot'    , Float),
    Column('tvism'      , Float),
    Column('mdust'      , Float),
    Column('sfr'        , Float),
    Column('i_opt'      , Float),
    Column('dmstar'     , Float),
    Column('dfmu_aux'   , Float),
    Column('dz'         , Float)
)

REGISTER = Table('register',
    MAGPHYS_METADATA,
    Column('register_id'   , BigInteger, primary_key=True, nullable=False),
    Column('galaxy_name'   , String(128), nullable=False),
    Column('redshift'      , Numeric(7,5), nullable=False),
    Column('sigma'         , Numeric(3,2), nullable=False),
    Column('galaxy_type'   , String(10), nullable=False),
    Column('filename'      , String(1000), nullable=False),
    Column('sigma_filename', String(1000)),
    Column('priority'      , Integer, nullable=False),
    Column('register_time' , TIMESTAMP, nullable=False),
    Column('create_time'   , TIMESTAMP),
    Column('run_id'        , BigInteger, ForeignKey('run.run_id'), nullable=False)
)

RUN = Table('run',
    MAGPHYS_METADATA,
    Column('run_id'            , BigInteger, primary_key=True),
    Column('short_description' , String(250)),
    Column('long_description'  , String(1000)),
    Column('directory'         , String(1000)),
    Column('fpops_est'         , Float),
    Column('cobblestone_factor', Float),
)

RUN_FILE = Table('run_file',
    MAGPHYS_METADATA,
    Column('run_file_id', BigInteger, primary_key=True),
    Column('run_id'     , BigInteger, ForeignKey('run.run_id')),
    Column('redshift'   , Numeric(7,5)),
    Column('file_type'  , Integer),
    Column('file_name'  , String(1000)),
    Column('size'       , BigInteger),
    Column('md5_hash'   , String(100))
)

RUN_FILTER = Table('run_filter',
    MAGPHYS_METADATA,
    Column('run_filter_id', BigInteger, primary_key=True),
    Column('run_id'       , BigInteger, ForeignKey('run.run_id')),
    Column('filter_id'    , BigInteger, ForeignKey('filter.filter_id'))
)

DOCMOSIS_TASK = Table('docmosis_task',
    MAGPHYS_METADATA,
    Column('task_id'      , BigInteger, primary_key=True, autoincrement=True),
    Column('userid'      , Integer),
    Column('worker_token', String(15)),
    Column('create_time' , TIMESTAMP, nullable=False),
    Column('finish_time' , TIMESTAMP),
    Column('status'      , Integer)
)

DOCMOSIS_TASK_GALAXY = Table('docmosis_task_galaxy',
    MAGPHYS_METADATA,
    Column('task_id'    , BigInteger, ForeignKey('docmosis_task.task_id'), primary_key=True),
    Column('galaxy_id'  , BigInteger, primary_key=True)
)
