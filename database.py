import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not found."
                    " Please set it to connect to the database.")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

print("✅ Database Connected")
