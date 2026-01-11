from sqlalchemy import create_engine, inspect
import os

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/optimization_db"
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
print(inspector.get_table_names())
