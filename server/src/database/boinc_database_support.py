"""
Connect to the BOINC database
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Column
from sqlalchemy.types import BigInteger, String

Base = declarative_base()
class Result(Base):
    __tablename__ = 'result'
    id = Column(BigInteger, primary_key=True)
    server_state = Column(BigInteger)
    workunitid = Column(BigInteger)
    appid = Column(BigInteger)

class Workunit(Base):
    __tablename__ = 'workunit'
    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    assimilate_state = Column(BigInteger)
