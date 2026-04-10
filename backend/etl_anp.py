"""
ETL para dados ANP - Baixa do site oficial e insere em torre.anp_precos no DW.
Executar via cron: python -m etl_anp
Executar também na primeira vez para criar a tabela automaticamente.
"""
import io
import logging
from datetime import datetime, timedelta
from decimal import Decimal

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_ANP_BASE = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsan"

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

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS torre.anp_precos (
    id SERIAL PRIMARY KEY,
    uf VARCHAR(2) NOT NULL,
    municipio VARCHAR(100),
    produto VARCHAR(50) NOT NULL,
    preco DECIMAL(8,4) NOT NULL,
    data_coleta DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anp_precos_uf_produto 
    ON torre.anp_precos (uf, produto, data_coleta);

CREATE INDEX IF NOT EXISTS idx_anp_precos_data_coleta 
    ON torre.anp_precos (data_coleta DESC);
"""


def _ensure_table():
    """Cria a tabela se não existir."""
    from db_dw import get_dw_engine
    from sqlalchemy import text
    
    engine = get_dw_engine()
    with engine.begin() as conn:
        conn.execute(text(_CREATE_TABLE_SQL))
    logger.info("ANP ETL: tabela torre.anp_precos criada/verificada")


def _csv_urls(ano: int, mes: int) -> list[str]:
    mm = f"{mes:02d}"
    base = f"{_ANP_BASE}/{ano}"
    return [
        f"{base}/{mm}-dados-abertos-precos-diesel-gnv.csv",
        f"{base}/{mm}-dados-abertos-precos-gasolina-etanol.csv",
    ]


def _download_csv(url: str) -> pd.DataFrame | None:
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
        df.dropna(subset=["preco", "data_coleta"], inplace=True)
        return df
    except Exception as e:
        logger.warning(f"ANP ETL: falha ao baixar {url}: {e}")
        return None


def _fetch_recent_data() -> pd.DataFrame:
    """Baixa dados dos últimos 2 meses."""
    hoje = datetime.now()
    resultados = []

    for delta in range(2):
        d = hoje - pd.DateOffset(months=delta)
        urls = _csv_urls(d.year, d.month)
        
        for url in urls:
            df = _download_csv(url)
            if df is not None and not df.empty:
                resultados.append(df)
                logger.info(f"ANP ETL: baixado {url} ({len(df)} registros)")

        if len(resultados) >= 2:
            break

    if not resultados:
        raise RuntimeError("ANP ETL: nenhum dado baixado")

    return pd.concat(resultados, ignore_index=True)


def run_etl():
    """Executa o ETL: baixa dados da ANP e insere no DW."""
    logger.info("ANP ETL: iniciando...")
    
    # Garante que a tabela existe
    _ensure_table()
    
    df = _fetch_recent_data()
    logger.info(f"ANP ETL: {len(df)} registros baixados")
    
    df["produto"] = df["produto"].map(PRODUTO_MAP).fillna(df["produto"])
    
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "uf": r["uf"],
            "municipio": r["municipio"],
            "produto": r["produto"],
            "preco": Decimal(str(r["preco"])),
            "data_coleta": r["data_coleta"].date(),
        })
    
    from db_dw import get_dw_engine
    from sqlalchemy import text
    
    engine = get_dw_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM torre.anp_precos"))
        conn.execute(text("""
            INSERT INTO torre.anp_precos (uf, municipio, produto, preco, data_coleta)
            VALUES (:uf, :municipio, :produto, :preco, :data_coleta)
        """), rows)
    
    logger.info(f"ANP ETL: {len(rows)} registros inseridos no DW")


if __name__ == "__main__":
    run_etl()