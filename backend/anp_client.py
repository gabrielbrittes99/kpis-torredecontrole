"""
Cliente ANP — Série Histórica de Preços de Combustíveis
Fonte: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis

Baixa os CSVs mensais públicos da ANP e retorna preço médio por UF e produto.
Cache local de 24h para evitar downloads repetidos.
"""
import io
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

# URLs dos CSVs mensais da ANP (padrão: MM-dados-abertos-precos-PRODUTO.csv)
_ANP_BASE = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsan"

# Mapeamento de nome ANP → nome interno do sistema
PRODUTO_MAP = {
    "GASOLINA COMUM": "gasolina",
    "GASOLINA": "gasolina",
    "GASOLINA ADITIVADA": "gasolina aditivada",
    "ETANOL HIDRATADO": "etanol",
    "ETANOL": "etanol",
    "DIESEL": "diesel",
    "DIESEL S10": "diesel s10",
    "GNV": "gnv",
}

_cache_df: Optional[pd.DataFrame] = None
_cache_ts: Optional[datetime] = None
_CACHE_TTL = timedelta(hours=24)


def _csv_urls(ano: int, mes: int) -> list[str]:
    mm = f"{mes:02d}"
    base = f"{_ANP_BASE}/{ano}"
    return [
        f"{base}/{mm}-dados-abertos-precos-diesel-gnv.csv",
        f"{base}/{mm}-dados-abertos-precos-gasolina-etanol.csv",
    ]


def _download_csv(url: str) -> Optional[pd.DataFrame]:
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
        df = pd.read_csv(
            io.StringIO(r.text),
            sep=";",
            decimal=",",
            usecols=["Estado - Sigla", "Municipio", "Produto", "Valor de Venda", "Data da Coleta"],
            dtype={"Estado - Sigla": str, "Municipio": str, "Produto": str},
        )
        df.rename(columns={
            "Estado - Sigla": "uf",
            "Municipio": "municipio",
            "Produto": "produto",
            "Valor de Venda": "preco",
            "Data da Coleta": "data_coleta"
        }, inplace=True)
        df["data_coleta"] = pd.to_datetime(df["data_coleta"], format="%d/%m/%Y", errors="coerce")
        df["preco"] = pd.to_numeric(df["preco"], errors="coerce")
        df["municipio"] = df["municipio"].fillna("").str.strip().str.upper()
        df.dropna(subset=["preco"], inplace=True)
        return df
    except Exception as e:
        logger.warning(f"ANP: falha ao baixar {url}: {e}")
        return None


def _build_cache() -> pd.DataFrame:
    hoje = datetime.now()
    frames = []
    
    # Categorias de arquivos que precisamos (categorias de URL)
    # 0 = diesel/gnv, 1 = gasolina/etanol
    categorias_baixadas = [False, False]

    # Tenta até os últimos 4 meses para garantir cobertura total
    for delta in range(4):
        if all(categorias_baixadas):
            break
            
        d = hoje - pd.DateOffset(months=delta)
        urls = _csv_urls(d.year, d.month)
        
        for idx, url in enumerate(urls):
            if categorias_baixadas[idx]:
                continue # Já temos os dados mais recentes dessa categoria
                
            df = _download_csv(url)
            if df is not None and not df.empty:
                frames.append(df)
                categorias_baixadas[idx] = True
                logger.info(f"ANP: Dados de {url} carregados com sucesso.")

    if not frames:
        logger.error("ANP: nenhum CSV disponível nos últimos 4 meses")
        return pd.DataFrame(columns=["uf", "municipio", "produto", "preco", "data_coleta"])

    return pd.concat(frames, ignore_index=True)


def get_anp_df() -> pd.DataFrame:
    global _cache_df, _cache_ts
    agora = datetime.now()
    if _cache_df is None or _cache_ts is None or (agora - _cache_ts) > _CACHE_TTL:
        logger.info("ANP: atualizando cache de preços...")
        _cache_df = _build_cache()
        _cache_ts = agora
        logger.info(f"ANP: {len(_cache_df)} registros carregados")
    return _cache_df


def get_benchmark_por_uf() -> list[dict]:
    """
    Retorna preço médio ANP por UF e produto (combustível).
    Usado para comparar com o preço pago pela frota.
    """
    df = get_anp_df()
    if df.empty:
        return []

    agg = (
        df.groupby(["uf", "produto"])["preco"]
        .agg(preco_medio="mean", qtd_postos="count")
        .reset_index()
    )
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
    """
    Retorna preço médio ANP nacional por produto.
    """
    df = get_anp_df()
    if df.empty:
        return []

    agg = (
        df.groupby("produto")["preco"]
        .agg(preco_medio="mean", qtd_postos="count")
        .reset_index()
    )
    agg["preco_medio"] = agg["preco_medio"].round(4)

    return [
        {
            "produto_anp": row["produto"],
            "preco_medio_anp": float(row["preco_medio"]),
            "qtd_postos_pesquisados": int(row["qtd_postos"]),
        }
        for _, row in agg.sort_values("produto").iterrows()
    ]
