"""
ETL Combustível — DW silver → torre.combustivel_classificacao

Lê os nomes distintos de combustível que existem no DW, aplica o mapeamento
do config.py (FUEL_GROUP_MAP) e persiste o resultado em torre.combustivel_classificacao.

Novos nomes que chegarem do DW sem mapeamento ficam como 'Outros' e podem
ser corrigidos diretamente na tabela — sem precisar alterar código.

Executar manualmente:  python -m etl_combustivel
Ou via endpoint:       POST /api/sistema/combustivel/refresh
"""
import logging
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS torre.combustivel_classificacao (
    combustivel_nome  VARCHAR(200) PRIMARY KEY,
    grupo_combustivel VARCHAR(50)  NOT NULL DEFAULT 'Outros',
    atualizado_em     TIMESTAMP    DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cc_grupo ON torre.combustivel_classificacao (grupo_combustivel);
"""


def _ensure_table():
    from db_dw import get_dw_engine
    from sqlalchemy import text
    with get_dw_engine().begin() as conn:
        conn.execute(text(_CREATE_TABLE_SQL))
    logger.info("ETL Combustível: tabela torre.combustivel_classificacao criada/verificada")


def run_etl() -> int:
    """
    Executa a carga:
    1. Lê nomes distintos de combustível do DW
    2. Classifica via FUEL_GROUP_MAP do config.py
    3. Upsert em torre.combustivel_classificacao (preserva mapeamentos manuais)

    Retorna o número de registros processados.
    """
    from config import FUEL_GROUP_MAP
    from db_dw import get_dw_engine
    from sqlalchemy import text
    import pandas as pd

    logger.info("ETL Combustível: iniciando...")

    _ensure_table()

    engine = get_dw_engine()

    # Busca nomes distintos do DW
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT combustivel_nome
            FROM silver.truckpag_analitico_transacao
            WHERE combustivel_nome IS NOT NULL AND combustivel_nome <> ''
        """))
        nomes_dw = [row[0] for row in result.fetchall()]

    logger.info(f"ETL Combustível: {len(nomes_dw)} nomes distintos encontrados no DW")

    # Busca mapeamentos manuais já existentes na tabela (para preservar edições manuais)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT combustivel_nome, grupo_combustivel
            FROM torre.combustivel_classificacao
        """))
        existentes = {row[0]: row[1] for row in result.fetchall()}

    agora = datetime.now()
    rows = []
    for nome in nomes_dw:
        nome_str = str(nome).strip()
        if not nome_str:
            continue

        # Classifica via FUEL_GROUP_MAP (fonte primária)
        grupo_auto = FUEL_GROUP_MAP.get(nome_str.lower(), "Outros")

        # Preserva edição manual APENAS se o valor no banco é diferente de "Outros"
        # e diferente do que o FUEL_GROUP_MAP produziria automaticamente —
        # isso indica que alguém editou manualmente para corrigir uma classificação.
        grupo_existente = existentes.get(nome_str)
        if grupo_existente and grupo_existente != "Outros" and grupo_existente != grupo_auto:
            grupo = grupo_existente
        else:
            grupo = grupo_auto

        rows.append({
            "combustivel_nome":  nome_str,
            "grupo_combustivel": grupo,
            "atualizado_em":     agora,
        })

    if not rows:
        logger.warning("ETL Combustível: nenhum registro para inserir")
        return 0

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM torre.combustivel_classificacao"))
        conn.execute(text("""
            INSERT INTO torre.combustivel_classificacao
                (combustivel_nome, grupo_combustivel, atualizado_em)
            VALUES
                (:combustivel_nome, :grupo_combustivel, :atualizado_em)
        """), rows)

    # Log dos que ficaram como "Outros" para facilitar diagnóstico
    outros = [r["combustivel_nome"] for r in rows if r["grupo_combustivel"] == "Outros"]
    if outros:
        logger.warning(f"ETL Combustível: {len(outros)} nomes sem mapeamento (Outros): {outros}")

    logger.info(f"ETL Combustível: {len(rows)} registros em torre.combustivel_classificacao")
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_etl()
