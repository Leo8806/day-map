from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# --------------------------------------------------
# Database Configuration
# --------------------------------------------------

DATABASE_URL = "sqlite:///./daymap.db"


# --------------------------------------------------
# Database Engine
# --------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# --------------------------------------------------
# Database Session
# --------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# --------------------------------------------------
# Base Class for Database Models
# --------------------------------------------------

class Base(DeclarativeBase):
    pass


# --------------------------------------------------
# Database Dependency
# --------------------------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
