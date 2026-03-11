import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from db import get_engine
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CACHE_TTL_MINUTES = int(os.getenv("CACHE_TTL_MINUTES", "30"))

# SQL principal — apenas abastecimentos válidos (litragem > 0, não estornados)
_QUERY = """
    SELECT
        data_transacao,
        valor,
        litragem,
        nome_combustivel,
        tipo_abastecimento,
        placa,
        hodometro,
        modelo_veiculo,
        marca_veiculo,
        motorista,
        razao_social_posto,
        nome_fantasia_posto,
        cidade_posto,
        uf_posto,
        transacao_estornada,
        cnpj_cliente
    FROM integration_truckpag_transacoes
    WHERE litragem > 0
      AND transacao_estornada = '0'
    ORDER BY data_transacao
"""


class DataCache:
    def __init__(self):
        self._df: pd.DataFrame | None = None
        self._last_updated: datetime | None = None

    def _is_stale(self) -> bool:
        if self._df is None or self._last_updated is None:
            return True
        return datetime.now() - self._last_updated > timedelta(
            minutes=CACHE_TTL_MINUTES
        )

    def _fetch_and_build(self) -> pd.DataFrame:
        logger.info("Carregando dados do PostgreSQL...")

        with get_engine().connect() as conn:
            df = pd.read_sql_query(_QUERY, conn)

        # Garante tipos corretos
        df["data_transacao"] = pd.to_datetime(
            df["data_transacao"], utc=True
        ).dt.tz_localize(None)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        df["litragem"] = pd.to_numeric(df["litragem"], errors="coerce").fillna(0)
        df["hodometro"] = pd.to_numeric(df["hodometro"], errors="coerce")

        # Normaliza texto
        for col in [
            "nome_combustivel",
            "tipo_abastecimento",
            "placa",
            "razao_social_posto",
            "cidade_posto",
            "uf_posto",
            "motorista",
        ]:
            df[col] = df[col].fillna("").astype(str).str.strip()

        logger.info(f"Cache atualizado: {len(df)} abastecimentos válidos")
        return df

    def get_df(self) -> pd.DataFrame:
        if self._is_stale():
            try:
                self._df = self._fetch_and_build()
                self._last_updated = datetime.now()
            except Exception as e:
                logger.error(f"Falha ao atualizar cache: {e}")
                if self._df is None:
                    raise
        return self._df

    def force_refresh(self) -> None:
        self._last_updated = None
        self.get_df()

    @property
    def last_updated(self) -> datetime | None:
        return self._last_updated


cache = DataCache()
