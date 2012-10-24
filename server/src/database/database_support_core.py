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

GALAXY = Table('galaxy',
    MAGPHYS_METADATA,
    Column('galaxy_id'       , BigInteger, primary_key=True),
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
    Column('pixels_processed', Integer)
)

AREA = Table('area',
    MAGPHYS_METADATA,
    Column('area_id'    , BigInteger, primary_key=True),
    Column('galaxy_id'  , BigInteger, ForeignKey('galaxy.galaxy_id')),
    Column('top_x'      , Integer),
    Column('top_y'      , Integer),
    Column('bottom_x'   , Integer),
    Column('bottom_y'   , Integer),
    Column('workunit_id', BigInteger),
    Column('update_time', TIMESTAMP)
)

PIXEL_RESULT = Table('pixel_result',
    MAGPHYS_METADATA,
    Column('pxresult_id', BigInteger, primary_key=True),
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

FITS_HEADER = Table('fits_header',
    MAGPHYS_METADATA,
    Column('fitsheader_id', BigInteger, primary_key=True),
    Column('galaxy_id'    , BigInteger, ForeignKey('galaxy.galaxy_id')),
    Column('keyword'      , String(128)),
    Column('value'        , String(128))
)

PIXEL_PARAMETER = Table('pixel_parameter',
    MAGPHYS_METADATA,
    Column('pxparameter_id'   , BigInteger, primary_key=True),
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

PARAMETER_NAME = Table('parameter_name',
    MAGPHYS_METADATA,
    Column('parameter_name_id', Integer, primary_key=True),
    Column('name'             , String(100))
)

PIXEL_HISTOGRAM = Table('pixel_histogram',
    MAGPHYS_METADATA,
    Column('pxhistogram_id', BigInteger, primary_key=True),
    Column('pxparameter_id', BigInteger, ForeignKey('pixel_parameter.pxparameter_id')),
    Column('pxresult_id'   , BigInteger, ForeignKey('pixel_result.pxresult_id')),
    Column('x_axis'        , Float),
    Column('hist_value'    , Float)
)
