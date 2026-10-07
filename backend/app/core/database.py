from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

db_url = settings.get_database_url()

# Provide SQLite fallback for local developer testing if Postgres is not yet provisioned
if db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,  # Check live connection before borrowing from pool
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base class for all ORM models
Base = declarative_base()


def ensure_user_avatar_column():
    if not inspect(engine).has_table("users"):
        return
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "avatar_url" not in user_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)"))


def get_db():
    """
    FastAPI dependency function to provide a clean database session per request.
    Closes session automatically after request completes or raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
