from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import db_login

pogsEngine = create_engine(db_login)
PogsSession = sessionmaker(bind=pogsEngine)