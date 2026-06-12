from sqlalchemy import create_engine

DATABASE_URL = (
    "postgresql://postgres:15102001@localhost:5432/native_capital"
)

engine = create_engine(DATABASE_URL)