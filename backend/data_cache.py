import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pandas as pd
from db import get_engine
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# TTLs fixos
TTL_TRANSACOES = timedelta(minutes=int(os.getenv("CACHE_TTL_MINUTES", "10")))
TTL_ANP = timedelta(hours=24)
TTL_VEICULOS = timedelta(hours=4)

# SQL principal
_QUERY_TRANSACOES = """
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
        self._cache: Dict[str, Dict[str, Any]] = {
            "transacoes": {"df": None, "ts": None, "ttl": TTL_TRANSACOES},
            "anp": {"df": None, "ts": None, "ttl": TTL_ANP},
            "veiculos": {"df": None, "ts": None, "ttl": TTL_VEICULOS},
        }

    def _is_stale(self, key: str) -> bool:
        entry = self._cache.get(key)
        if not entry or entry["df"] is None or entry["ts"] is None:
            return True
        return datetime.now() - entry["ts"] > entry["ttl"]

    def _fetch_transacoes(self) -> pd.DataFrame:
        logger.info("Cache: Carregando transações do PostgreSQL...")
        with get_engine().connect() as conn:
            df = pd.read_sql_query(_QUERY_TRANSACOES, conn)

        # Garante tipos corretos
        df["data_transacao"] = pd.to_datetime(df["data_transacao"], utc=True).dt.tz_localize(None)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        df["litragem"] = pd.to_numeric(df["litragem"], errors="coerce").fillna(0)
        df["hodometro"] = pd.to_numeric(df["hodometro"], errors="coerce")

        # Normaliza texto
        text_cols = [
            "nome_combustivel", "tipo_abastecimento", "placa",
            "razao_social_posto", "cidade_posto", "uf_posto", "motorista"
        ]
        for col in text_cols:
            df[col] = df[col].fillna("").astype(str).str.strip()

        logger.info(f"Cache: {len(df)} transações carregadas.")
        return df

    def get_df(self, key: str = "transacoes") -> pd.DataFrame:
        """Retorna o DataFrame do cache, atualizando-o se necessário."""
        if self._is_stale(key):
            try:
                if key == "transacoes":
                    df = self._fetch_transacoes()
                elif key == "anp":
                    # Integrado via anp_client, mas mantido aqui para centralizar
                    from anp_client import get_anp_df
                    df = get_anp_df()
                else:
                    return pd.DataFrame()

                self._cache[key]["df"] = df
                self._cache[key]["ts"] = datetime.now()
            except Exception as e:
                logger.error(f"Falha ao atualizar cache '{key}': {e}")
                if self._cache[key]["df"] is None:
                    raise
        return self._cache[key]["df"]

    def force_refresh(self, key: str = "transacoes") -> None:
        """Força a limpeza do timestamp para obrigar atualização na próxima chamada."""
        if key in self._cache:
            self._cache[key]["ts"] = None
            self.get_df(key)

    @property
    def last_updated(self) -> Optional[datetime]:
        return self._cache["transacoes"]["ts"]


cache = DataCache()
