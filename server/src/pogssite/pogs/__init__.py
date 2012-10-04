from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_LOGIN

pogsEngine = create_engine(DB_LOGIN)
PogsSession = sessionmaker(bind=pogsEngine)
