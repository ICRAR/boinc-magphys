from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database_support import login

pogsEngine = create_engine(login)
PogsSession = sessionmaker(bind=pogsEngine)