"""
ETL Veículos — SQL Server → torre.veiculo_classificacao

Lê o cadastro de veículos do SQL Server (BlueFleet), aplica a classificação
de grupo (VEICULO_RULES do config.py) e persiste o resultado no DW schema torre.

Executar manualmente:  python -m etl_veiculos
Ou via endpoint:       POST /api/sistema/veiculos/refresh
"""
import logging
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS torre.veiculo_classificacao (
    placa              VARCHAR(10)   PRIMARY KEY,
    modelo             VARCHAR(200),
    montadora          VARCHAR(100),
    grupo_veiculo      VARCHAR(50),
    tanque_litros      NUMERIC(8,2),
    ano_modelo         INTEGER,
    filial_operacional VARCHAR(200),
    atualizado_em      TIMESTAMP     DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_vc_grupo   ON torre.veiculo_classificacao (grupo_veiculo);
CREATE INDEX IF NOT EXISTS idx_vc_filial  ON torre.veiculo_classificacao (filial_operacional);
"""


def _ensure_table():
    from db_dw import get_dw_engine
    from sqlalchemy import text
    with get_dw_engine().begin() as conn:
        conn.execute(text(_CREATE_TABLE_SQL))
    logger.info("ETL Veículos: tabela torre.veiculo_classificacao criada/verificada")


def run_etl() -> int:
    """
    Executa a carga completa:
    1. Lê veículos do SQL Server
    2. Classifica grupo via VEICULO_RULES
    3. Upsert em torre.veiculo_classificacao

    Retorna o número de registros sincronizados.
    """
    from config import get_veiculo_group
    from db_sqlserver import get_veiculos_df
    from db_dw import get_dw_engine
    from sqlalchemy import text

    logger.info("ETL Veículos: iniciando...")

    _ensure_table()

    df = get_veiculos_df()
    if df.empty:
        logger.warning("ETL Veículos: SQL Server retornou 0 veículos")
        return 0

    # Deduplica por placa (SQL Server pode ter múltiplos registros por placa)
    df = df.drop_duplicates(subset=["Placa"], keep="last")

    rows = []
    for _, row in df.iterrows():
        placa     = str(row.get("Placa", "") or "").strip()
        modelo    = str(row.get("Modelo", "") or "").strip()
        montadora = str(row.get("Montadora", "") or "").strip()

        # Ignora placas inválidas
        if not placa or placa.upper() in ("NAN", "NONE", "NULL", ""):
            continue

        grupo = get_veiculo_group(modelo, montadora, placa)

        rows.append({
            "placa":              placa,
            "modelo":             modelo,
            "montadora":          montadora,
            "grupo_veiculo":      grupo,
            "tanque_litros":      row.get("TanqueLitros"),
            "ano_modelo":         row.get("AnoModelo"),
            "filial_operacional": str(row.get("FilialOperacional", "") or "").strip(),
            "atualizado_em":      datetime.now(),
        })

    if not rows:
        logger.warning("ETL Veículos: nenhum registro válido para inserir")
        return 0

    engine = get_dw_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM torre.veiculo_classificacao"))
        conn.execute(text("""
            INSERT INTO torre.veiculo_classificacao
                (placa, modelo, montadora, grupo_veiculo, tanque_litros,
                 ano_modelo, filial_operacional, atualizado_em)
            VALUES
                (:placa, :modelo, :montadora, :grupo_veiculo, :tanque_litros,
                 :ano_modelo, :filial_operacional, :atualizado_em)
        """), rows)

    logger.info(f"ETL Veículos: {len(rows)} registros sincronizados em torre.veiculo_classificacao")
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_etl()
