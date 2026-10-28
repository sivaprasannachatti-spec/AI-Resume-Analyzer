import sys
import backend.models.schemas

from sqlmodel import Session, create_engine, SQLModel

from src.exception import CustomException
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        raise CustomException(e, sys)

def get_session():
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        raise CustomException(e, sys)

