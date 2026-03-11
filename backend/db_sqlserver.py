"""
Conexão com SQL Server (dados de veículos, filiais, garagens).
Usa pymssql — sem dependência de driver ODBC do sistema operacional.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import pymssql
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_veiculos_cache: Optional[pd.DataFrame] = None
_veiculos_cache_ts: Optional[datetime] = None
_VEICULOS_TTL = timedelta(hours=6)


def get_veiculos_df() -> pd.DataFrame:
    """
    Retorna DataFrame com Placa e TanqueLitros do SQL Server.
    Cache de 6h — evita query a cada requisição.
    """
    global _veiculos_cache, _veiculos_cache_ts
    agora = datetime.now()
    if (
        _veiculos_cache is None
        or _veiculos_cache_ts is None
        or (agora - _veiculos_cache_ts) > _VEICULOS_TTL
    ):
        try:
            conn = get_sqlserver_conn()
            cursor = conn.cursor(as_dict=True)
            cursor.execute("SELECT Placa, TanqueLitros, FilialOperacional FROM veiculos")
            rows = cursor.fetchall()
            conn.close()
            df = pd.DataFrame(rows)
            df["Placa"] = df["Placa"].str.upper().str.replace("-", "").str.strip()
            df["TanqueLitros"] = pd.to_numeric(df["TanqueLitros"], errors="coerce")
            _veiculos_cache = df
            _veiculos_cache_ts = agora
            logger.info(f"SQL Server: {len(df)} veículos carregados no cache")
        except Exception as e:
            logger.warning(f"SQL Server: falha ao carregar veículos: {e}")
            if _veiculos_cache is not None:
                return _veiculos_cache  # Retorna cache antigo em caso de falha
            return pd.DataFrame(columns=["Placa", "TanqueLitros", "FilialOperacional"])
    return _veiculos_cache


def get_sqlserver_conn() -> pymssql.Connection:
    host = os.getenv("SQLSERVER_HOST")
    port = int(os.getenv("SQLSERVER_PORT", "1433"))
    database = os.getenv("SQLSERVER_DB")
    user = os.getenv("SQLSERVER_USER")
    password = os.getenv("SQLSERVER_PASSWORD")

    if not all([host, database, user, password]):
        raise RuntimeError(
            "Credenciais SQL Server não configuradas. "
            "Preencha SQLSERVER_HOST, SQLSERVER_DB, SQLSERVER_USER e SQLSERVER_PASSWORD no .env"
        )

    return pymssql.connect(
        server=host,
        port=port,
        database=database,
        user=user,
        password=password,
        timeout=15,
        login_timeout=10,
    )
