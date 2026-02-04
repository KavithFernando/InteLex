"""
SQLAlchemy engine and session for ORM (e.g. User model).
Uses same DB config as db.connection; for auth/user only.
"""
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DB_CONFIG

# Build URL; escape password for special characters
user = DB_CONFIG["user"] or ""
password = DB_CONFIG["password"] or ""
host = DB_CONFIG["host"] or "localhost"
port = int(DB_CONFIG["port"]) if DB_CONFIG["port"] is not None else 3306
database = DB_CONFIG["database"] or ""
url = (
    f"mysql+mysqlconnector://{quote_plus(user)}:{quote_plus(password)}"
    f"@{host}:{port}/{quote_plus(database)}"
)

engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db_session():
    """Yield a DB session; caller should close or use as context."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
