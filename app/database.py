import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Add it to your environment file."
    )


class Base(DeclarativeBase):
    pass


engine_options = {
    "pool_pre_ping": True,
}


if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {
        "check_same_thread": False,
    }


engine = create_engine(
    DATABASE_URL,
    **engine_options,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)