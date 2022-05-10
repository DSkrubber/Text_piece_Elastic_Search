from typing import Iterator

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .constants import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

load_dotenv(find_dotenv("../.env"))

SQLALCHEMY_POSTGRESQL_URL = "postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}".format(
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
)
engine = create_engine(SQLALCHEMY_POSTGRESQL_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Iterator[sessionmaker]:
    """Yields SessionLocal instance for resources via FastAPI Depends function.

    Finally, closes connection to database.
    :return: Iterator that yields SessionLocal instance.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
