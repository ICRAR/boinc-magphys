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
The SQLAlchemy ORM tables

The database is partitioned to improve performance, this means there are no primary
keys, but the ORM mapping of sqlalchemy needs them - doesn't seem to hurt having
them even though they don't really exist
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Table
from sqlalchemy.types import Numeric

##########################################################################
##########################################################################

##########################################################################
#
# If you change this file change the database_support_core.py file to
# match the change
#
##########################################################################

##########################################################################
##########################################################################

Base = declarative_base()

# The many-to-many join table
run_filter_association_table = Table('run_filter',
    Base.metadata,
    Column('run_id', BigInteger, ForeignKey('run.run_id')),
    Column('filter_id', BigInteger, ForeignKey('filter.filter_id')))

class Galaxy(Base):
    __tablename__ = 'galaxy'

    galaxy_id        = Column(BigInteger, primary_key=True)
    run_id           = Column(BigInteger, ForeignKey('run.run_id'))
    name             = Column(String(128))
    dimension_x      = Column(Integer)
    dimension_y      = Column(Integer)
    dimension_z      = Column(Integer)
    redshift         = Column(Numeric(7,5))
    create_time      = Column(TIMESTAMP)
    image_time       = Column(TIMESTAMP)
    version_number   = Column(Integer)
    current          = Column(Boolean)
    galaxy_type      = Column(String(10))
    ra_cent          = Column(Float)
    dec_cent         = Column(Float)
    sigma            = Column(Numeric(3,2))
    pixel_count      = Column(Integer)
    pixels_processed = Column(Integer)

    def __repr__(self):
        return 'galaxy: {galaxy_id : {0}, name : {1}}'.format(self.galaxy_id, self.name)

class FitsHeader(Base):
    __tablename__ = 'fits_header'

    fitsheader_id = Column(BigInteger, primary_key=True)
    galaxy_id     = Column(BigInteger, ForeignKey('galaxy.galaxy_id'))
    keyword       = Column(String(128))
    value         = Column(String(128))

    galaxy = relationship("Galaxy", backref=backref('fits_headers', order_by=galaxy_id))

class Area(Base):
    __tablename__ = 'area'

    area_id      = Column(BigInteger, primary_key=True)
    galaxy_id    = Column(BigInteger, ForeignKey('galaxy.galaxy_id'))
    top_x        = Column(Integer)
    top_y        = Column(Integer)
    bottom_x     = Column(Integer)
    bottom_y     = Column(Integer)
    workunit_id  = Column(BigInteger)
    update_time  = Column(TIMESTAMP)

    galaxy = relationship("Galaxy", backref=backref('areas', order_by=area_id))

class AreaUser(Base):
    __tablename__ = 'area_user'

    areauser_id = Column(BigInteger, primary_key=True)
    area_id     = Column(BigInteger, ForeignKey('area.area_id'))
    userid      = Column(Integer)
    create_time = Column(TIMESTAMP)

    area = relationship("Area", backref=backref('users', order_by=areauser_id))

class PixelResult(Base):
    __tablename__ = 'pixel_result'

    pxresult_id = Column(BigInteger, primary_key=True)
    area_id     = Column(BigInteger, ForeignKey('area.area_id'))
    galaxy_id   = Column(BigInteger, ForeignKey('galaxy.galaxy_id'))
    x           = Column(Integer)
    y           = Column(Integer)
    workunit_id = Column(BigInteger)
    i_sfh       = Column(Float)
    i_ir        = Column(Float)
    chi2        = Column(Float)
    redshift    = Column(Float)
    fmu_sfh     = Column(Float)
    fmu_ir      = Column(Float)
    mu          = Column(Float)
    tauv        = Column(Float)
    s_sfr       = Column(Float)
    m           = Column(Float)
    ldust       = Column(Float)
    t_w_bc      = Column(Float)
    t_c_ism     = Column(Float)
    xi_c_tot    = Column(Float)
    xi_pah_tot  = Column(Float)
    xi_mir_tot  = Column(Float)
    x_w_tot     = Column(Float)
    tvism       = Column(Float)
    mdust       = Column(Float)
    sfr         = Column(Float)
    i_opt       = Column(Float)
    dmstar      = Column(Float)
    dfmu_aux    = Column(Float)
    dz          = Column(Float)

    galaxy = relationship("Galaxy", backref=backref('pixelResults', order_by=galaxy_id))
    area   = relationship("Area", backref=backref('pixelResults', order_by=pxresult_id))

class PixelFilter(Base):
    __tablename__ = 'pixel_filter'

    pxfilter_id               = Column(BigInteger, primary_key=True)
    pxresult_id               = Column(BigInteger, ForeignKey('pixel_result.pxresult_id'))
    filter_name               = Column(String(100))
    observed_flux             = Column(Float)
    observational_uncertainty = Column(Float)
    flux_bfm = Column(Float)

    result = relationship("PixelResult", backref=backref('filters', order_by=pxfilter_id))

class PixelParameter(Base):
    __tablename__ = 'pixel_parameter'

    pxparameter_id    = Column(BigInteger, primary_key=True)
    pxresult_id       = Column(BigInteger, ForeignKey('pixel_result.pxresult_id'))
    parameter_name_id = Column(Integer)
    percentile2_5     = Column(Float)
    percentile16      = Column(Float)
    percentile50      = Column(Float)
    percentile84      = Column(Float)
    percentile97_5    = Column(Float)
    high_prob_bin     = Column(Float)
    first_prob_bin    = Column(Float)
    last_prob_bin     = Column(Float)
    bin_step          = Column(Float)

    result = relationship("PixelResult", backref=backref('parameters', order_by=pxparameter_id))

class PixelHistogram(Base):
    __tablename__ = 'pixel_histogram'

    pxhistogram_id = Column(BigInteger, primary_key=True)
    pxparameter_id = Column(BigInteger, ForeignKey('pixel_parameter.pxparameter_id'))
    pxresult_id    = Column(BigInteger, ForeignKey('pixel_result.pxresult_id'))
    x_axis         = Column(Float)
    hist_value     = Column(Float)

    parameter = relationship("PixelParameter", backref=backref('histograms', order_by=pxhistogram_id))
    pxresult = relationship("PixelResult", backref=backref('histograms', order_by=pxhistogram_id))

class Register(Base):
    __tablename__ = 'register'

    register_id   = Column(BigInteger, primary_key=True)
    galaxy_name   = Column(String(128))
    redshift      = Column(Numeric(7,5))
    sigma         = Column(Numeric(3,2))
    galaxy_type   = Column(String(10))
    filename      = Column(String(1000))
    priority      = Column(Integer)
    register_time = Column(TIMESTAMP)
    create_time   = Column(TIMESTAMP)
    run_id        = Column(BigInteger, ForeignKey('run.run_id'))

class ParameterName(Base):
    __tablename__ = 'parameter_name'

    parameter_name_id = Column(Integer, primary_key=True)
    name              = Column(String(100))

class Filter(Base):
    __tablename__ = 'filter'

    filter_id     = Column(Integer, primary_key=True)
    name          = Column(String(30))
    eff_lambda    = Column(Numeric(10,4))
    filter_number = Column(Integer)
    ultraviolet   = Column(Integer)
    optical       = Column(Integer)
    infrared      = Column(Integer)

class ImageFiltersUsed(Base):
    __tablename__ = 'image_filters_used'

    image_filters_used_id = Column(BigInteger, primary_key=True)
    image_number          = Column(Integer)
    galaxy_id             = Column(BigInteger, ForeignKey('galaxy.galaxy_id'))
    filter_id_red         = Column(Integer, ForeignKey('filter.filter_id'))
    filter_id_green       = Column(Integer, ForeignKey('filter.filter_id'))
    filter_id_blue        = Column(Integer, ForeignKey('filter.filter_id'))

class Run(Base):
    __tablename__ = 'run'

    run_id            = Column(BigInteger, primary_key=True)
    short_description = Column(String(250))
    long_description  = Column(String(1000))
    directory         = Column(String(1000))

    registrations = relationship('Register', backref=backref('run'))
    run_files     = relationship('RunFile', backref=backref('run'))
    filters       = relationship('Filter', secondary=run_filter_association_table, backref='runs')

class RunFile(Base):
    __tablename__ = 'run_file'

    run_file_id = Column(BigInteger, primary_key=True)
    run_id      = Column(BigInteger, ForeignKey('run.run_id'))
    redshift    = Column(Numeric(7,5))
    file_type   = Column(Integer)
    file_name   = Column(String(1000))
    size        = Column(BigInteger)
    md5_hash    = Column(String(100))
