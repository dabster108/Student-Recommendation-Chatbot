from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL  # Make sure to define DATABASE_URL in .env file

# Create the database engine (this will use the DATABASE_URL from the config file)
engine = create_engine(DATABASE_URL)

# SessionLocal is the session that will be used to interact with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for the database models (User model, etc.)
Base = declarative_base()

# Dependency that will allow us to use the database session in the API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
