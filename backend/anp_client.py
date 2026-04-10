"""
Cliente ANP — Preços de Combustíveis
DADOS VÊM EXCLUSIVAMENTE DO DW (torre.anp_precos)
Sem downloads, sem chamadas HTTP externas na API.
Execute o ETL separadamente para atualizar os dados no DW.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_cache_df: Optional[pd.DataFrame] = None
_cache_ts: Optional[datetime] = None
_CACHE_TTL = timedelta(hours=24)


def _has_dw_config() -> bool:
    """Verifica se as credenciais do DW estão configuradas."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return bool(
        os.getenv("DW_HOST")
        and os.getenv("DW_USER")
        and os.getenv("DW_PASSWORD")
        and os.getenv("DW_PASSWORD") != "COLOQUE_SUA_SENHA_AQUI"
    )


def _read_from_dw() -> pd.DataFrame | None:
    """Lê dados do DW (torre.anp_precos)."""
    if not _has_dw_config():
        logger.warning("ANP: DW não configurado")
        return None
    
    try:
        from db_dw import get_dw_engine
        from sqlalchemy import text
        
        engine = get_dw_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT uf, municipio, produto, preco, data_coleta
                FROM torre.anp_precos
                ORDER BY data_coleta DESC
            """))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        if df.empty:
            logger.warning("ANP: tabela vazia no DW")
            return None
        
        logger.info(f"ANP: {len(df)} registros carregados do DW")
        return df
    except Exception as e:
        logger.warning(f"ANP: falha ao ler do DW: {e}")
        return None


def get_anp_df() -> pd.DataFrame:
    """Retorna dados ANP do DW. Retorna vazio se não houver dados."""
    global _cache_df, _cache_ts
    agora = datetime.now()
    
    if _cache_df is not None and _cache_ts is not None and (agora - _cache_ts) <= _CACHE_TTL:
        return _cache_df
    
    df = _read_from_dw()
    
    _cache_df = df if df is not None else pd.DataFrame(columns=["uf", "municipio", "produto", "preco", "data_coleta"])
    _cache_ts = agora
    
    return _cache_df


def get_benchmark_por_uf() -> list[dict]:
    """Preço médio ANP por UF e produto."""
    df = get_anp_df()
    if df.empty:
        return []

    agg = df.groupby(["uf", "produto"])["preco"].agg(preco_medio="mean", qtd_postos="count").reset_index()
    agg["preco_medio"] = agg["preco_medio"].round(4)

    return [
        {
            "uf": row["uf"],
            "produto_anp": row["produto"],
            "preco_medio_anp": float(row["preco_medio"]),
            "qtd_postos_pesquisados": int(row["qtd_postos"]),
        }
        for _, row in agg.sort_values(["uf", "produto"]).iterrows()
    ]


def get_benchmark_nacional() -> list[dict]:
    """Preço médio ANP nacional por produto."""
    df = get_anp_df()
    if df.empty:
        return []

    agg = df.groupby("produto")["preco"].agg(preco_medio="mean", qtd_postos="count").reset_index()
    agg["preco_medio"] = agg["preco_medio"].round(4)

    return [
        {
            "produto_anp": row["produto"],
            "preco_medio_anp": float(row["preco_medio"]),
            "qtd_postos_pesquisados": int(row["qtd_postos"]),
        }
        for _, row in agg.sort_values("produto").iterrows()
    ]