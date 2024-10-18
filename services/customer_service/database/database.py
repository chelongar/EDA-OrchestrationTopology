#!/usr/bin/python

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from .database_models import Base

from .customer_model import customer


class postgreSQL_database:
    def __init__(self, username, password, database_name):
        self.database_engine = create_engine(f"postgresql+psycopg://{username}:"
                                             f"{password}@postgreSQL_service:5432/"
                                             f"{database_name}", echo=True)
        self.metadata = MetaData()
        self.metadata.bind = self.database_engine

        self.current_session = scoped_session(sessionmaker(bind=self.database_engine))

    def get_session(self):
        return self.current_session()

    def drop_schema(self):
        Base.metadata.drop_all(self.database_engine, checkfirst=True)

    def create_schema(self):
        Base.metadata.create_all(self.database_engine, checkfirst=True)
