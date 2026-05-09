from sqlalchemy import create_engine # pyright: ignore[reportMissingImports]
from sqlalchemy.ext.declarative import declarative_base # pyright: ignore[reportMissingImports]
import sqlalchemy.orm # pyright: ignore[reportMissingImports]

DATABASE_URL = "sqlite:///./quiz.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sqlalchemy.orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()