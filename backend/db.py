import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Railway fornece DATABASE_URL com prefixo "postgresql://"
            # SQLAlchemy precisa de "postgresql+psycopg2://"
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            url = database_url
        else:
            # Fallback: variáveis individuais (.env local)
            host = os.getenv("DB_HOST")
            port = os.getenv("DB_PORT", "5432")
            dbname = os.getenv("DB_NAME")
            user = os.getenv("DB_USER")
            password = os.getenv("DB_PASSWORD")
            url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        _engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 15})
    return _engine
