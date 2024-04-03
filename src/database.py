import os
import dotenv
import sqlalchemy
from sqlalchemy import create_engine

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)

def updateRow():
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE students SET first_name = 'Jane'"))

def selectRow():
    with engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM students"))
        for row in result:
            print(row)