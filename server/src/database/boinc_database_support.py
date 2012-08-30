"""
Connect to the BOINC database
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import Column
from sqlalchemy.types import BigInteger

Base = declarative_base()
class Result(Base):
    __tablename__ = 'result'
    id = Column(BigInteger, primary_key=True)
    server_state = Column(BigInteger)
    workunitid = Column(BigInteger)
    appid = Column(BigInteger)
