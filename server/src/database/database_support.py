from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.orm import relationship, backref

# The database is partitioned to improve performance, this means there are no primary
# keys, but the ORM mapping of sqlalchemy needs them - doesn't seem to hurt having
# them even though they don't really exist

Base = declarative_base()
class Galaxy(Base):
    __tablename__ = 'galaxy'

    galaxy_id = Column(BigInteger, primary_key=True)
    name = Column(String(128))
    dimension_x = Column(Integer)
    dimension_y = Column(Integer)
    dimension_z = Column(Integer)
    redshift = Column(Float)
    create_time = Column(TIMESTAMP)
    image_time  = Column(TIMESTAMP)
    version_number = Column(Integer)

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

    galaxy = relationship("Galaxy", backref=backref('areas', order_by=galaxy_id))

class AreaUser(Base):
    __tablename__ = 'area_user'

    areauser_id = Column(BigInteger, primary_key=True)
    area_id = Column(BigInteger, ForeignKey('area.area_id'))
    userid = Column(Integer)
    create_time = Column(TIMESTAMP)

    area = relationship("Area", backref=backref('users', order_by=areauser_id))

class PixelResult(Base):
    __tablename__ = 'pixel_result'

    pxresult_id = Column(BigInteger, primary_key=True)
    area_id = Column(BigInteger, ForeignKey('area.area_id'))
    galaxy_id = Column(BigInteger, ForeignKey('galaxy.galaxy_id'))
    x = Column(Integer)
    y = Column(Integer)
    workunit_id = Column(BigInteger)
    i_sfh = Column(Float)
    i_ir = Column(Float)
    chi2 = Column(Float)
    redshift = Column(Float)
    fmu_sfh = Column(Float)
    fmu_ir = Column(Float)
    mu = Column(Float)
    tauv = Column(Float)
    s_sfr = Column(Float)
    m = Column(Float)
    ldust = Column(Float)
    t_w_bc = Column(Float)
    t_c_ism = Column(Float)
    xi_c_tot = Column(Float)
    xi_pah_tot = Column(Float)
    xi_mir_tot = Column(Float)
    x_w_tot = Column(Float)
    tvism = Column(Float)
    mdust = Column(Float)
    sfr = Column(Float)
    i_opt = Column(Float)
    dmstar = Column(Float)
    dfmu_aux = Column(Float)
    dz = Column(Float)

    galaxy = relationship("Galaxy", backref=backref('pixelResults', order_by=galaxy_id))
    area = relationship("Area", backref=backref('pixelResults', order_by=area_id))

class PixelFilter(Base):
    __tablename__ = 'pixel_filter'

    pxfilter_id = Column(BigInteger, primary_key=True)
    pxresult_id = Column(BigInteger, ForeignKey('pixel_result.pxresult_id'))
    filter_name = Column(String(100))
    observed_flux = Column(Float)
    observational_uncertainty = Column(Float)
    flux_bfm = Column(Float)

    result = relationship("PixelResult", backref=backref('filters', order_by=pxfilter_id))

class PixelParameter(Base):
    __tablename__ = 'pixel_parameter'

    pxparameter_id = Column(BigInteger, primary_key=True)
    pxresult_id = Column(BigInteger, ForeignKey('pixel_result.pxresult_id'))
    parameter_name = Column(String(100))
    percentile2_5 = Column(Float)
    percentile16 = Column(Float)
    percentile50 = Column(Float)
    percentile84 = Column(Float)
    percentile97_5 = Column(Float)

    result = relationship("PixelResult", backref=backref('parameters', order_by=pxparameter_id))

class PixelHistogram(Base):
    __tablename__ = 'pixel_histogram'

    pxhistogram_id = Column(BigInteger, primary_key=True)
    pxparameter_id = Column(BigInteger, ForeignKey('pixel_parameter.pxparameter_id'))
    pxresult_id = Column(BigInteger, ForeignKey('pixel_result.pxresult_id'))
    x_axis = Column(Float)
    hist_value = Column(Float)

    parameter = relationship("PixelParameter", backref=backref('histograms', order_by=pxhistogram_id))


