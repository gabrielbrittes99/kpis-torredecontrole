"""
Conexão com o Data Warehouse interno (PostgreSQL).
Tabela principal: silver.truckpag_analitico_transacao

Host: DW_HOST (192.168.0.37)
Port: DW_PORT (5433)
DB:   DW_NAME (dw)
"""
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()

logger = logging.getLogger(__name__)

_dw_engine: Engine | None = None


def get_dw_engine() -> Engine:
    """Retorna engine SQLAlchemy para o Data Warehouse (PostgreSQL interno)."""
    global _dw_engine
    if _dw_engine is None:
        host = os.getenv("DW_HOST")
        port = os.getenv("DW_PORT", "5433")
        dbname = os.getenv("DW_NAME", "dw")
        user = os.getenv("DW_USER")
        password = os.getenv("DW_PASSWORD")

        if not all([host, user, password]):
            raise RuntimeError(
                "Credenciais DW não configuradas. "
                "Preencha DW_HOST, DW_USER e DW_PASSWORD no .env"
            )

        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        _dw_engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 30},
        )
        logger.info(f"DW Engine criada: {host}:{port}/{dbname}")
    return _dw_engine
