"""
ETL: Reconciliação FKM × TruckPag → torre.fkm_reconciliacao

Cruza o FKM (custo total real de combustível por veículo/mês, incluindo
abastecimentos faturados diretamente) com o TruckPag (só transações via cartão)
para calcular o volume faturado diretamente por placa/mês.

Gera flags de qualidade:
  gap_negativo   — FKM menor que TruckPag (erro de preenchimento)
  preco_suspeito — preço/L implícito fora da faixa R$ 4–18
  kml_divergente — km/L calculado diverge do informado pela filial > 20%
  sem_truckpag   — nenhuma transação TruckPag no mês (100% direto)

Execução:
  cd backend && python etl_fkm_reconcilia.py            # todos os meses do FKM
  cd backend && python etl_fkm_reconcilia.py 2026-03    # mês específico
"""
import logging
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


# ── DDL ───────────────────────────────────────────────────────────────────────

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS torre.fkm_reconciliacao (
    id              SERIAL PRIMARY KEY,
    placa           VARCHAR(20)    NOT NULL,
    ano_mes         VARCHAR(7)     NOT NULL,   -- 'YYYY-MM'
    filial          VARCHAR(100),
    contrato        VARCHAR(100),
    grupo_veiculo   VARCHAR(50),
    tp_combustivel  VARCHAR(50),
    total_km        NUMERIC(12,2),
    -- FKM original (informado pela filial — nunca alterado)
    litros_fkm      NUMERIC(12,2),
    valor_fkm       NUMERIC(14,2),
    media_kml_fkm   NUMERIC(8,3),
    -- TruckPag (apenas via cartão)
    litros_truckpag NUMERIC(12,2),
    valor_truckpag  NUMERIC(14,2),
    qtd_transacoes  INTEGER,
    -- Valores efetivos usados para cálculo
    -- (= TruckPag quando FKM < TruckPag, senão = FKM)
    litros_efetivo  NUMERIC(12,2),
    valor_efetivo   NUMERIC(14,2),
    -- Diferença (faturado diretamente)
    litros_direto   NUMERIC(12,2),
    valor_direto    NUMERIC(14,2),
    -- Métricas derivadas
    pct_truckpag          NUMERIC(6,2),
    preco_litro_implicito NUMERIC(8,3),
    -- Qualidade
    corrigido_por_truckpag BOOLEAN  DEFAULT FALSE,
    flags                  TEXT[],
    tem_alerta             BOOLEAN  DEFAULT FALSE,
    -- Controle
    etl_at          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (placa, ano_mes)
);

CREATE INDEX IF NOT EXISTS idx_fkm_recon_ano_mes  ON torre.fkm_reconciliacao (ano_mes DESC);
CREATE INDEX IF NOT EXISTS idx_fkm_recon_filial   ON torre.fkm_reconciliacao (filial);
CREATE INDEX IF NOT EXISTS idx_fkm_recon_alertas  ON torre.fkm_reconciliacao (tem_alerta) WHERE tem_alerta;

-- Garante colunas novas em tabelas já existentes
ALTER TABLE torre.fkm_reconciliacao ADD COLUMN IF NOT EXISTS litros_efetivo  NUMERIC(12,2);
ALTER TABLE torre.fkm_reconciliacao ADD COLUMN IF NOT EXISTS valor_efetivo   NUMERIC(14,2);
ALTER TABLE torre.fkm_reconciliacao ADD COLUMN IF NOT EXISTS corrigido_por_truckpag BOOLEAN DEFAULT FALSE;
"""


def _ensure_table():
    from db_dw import get_dw_engine
    engine = get_dw_engine()
    with engine.begin() as conn:
        conn.execute(text(_CREATE_TABLE_SQL))
    logger.info("Tabela torre.fkm_reconciliacao criada/verificada")


# ── Extração ──────────────────────────────────────────────────────────────────

def _load_fkm(ano_mes: str | None) -> pd.DataFrame:
    from db_fkm import get_fkm_df
    df = get_fkm_df()
    if df.empty:
        raise RuntimeError("FKM vazio — verifique o arquivo xlsb")
    if ano_mes:
        df = df[df["ano_mes"] == ano_mes]
        if df.empty:
            raise RuntimeError(f"Nenhuma linha FKM para {ano_mes}")
    logger.info(f"FKM: {len(df)} linhas | meses: {sorted(df['ano_mes'].dropna().unique())}")
    return df


def _load_truckpag(ano_mes: str | None) -> pd.DataFrame:
    """Agrega TruckPag (Railway) por placa_norm + ano_mes."""
    from db import get_engine
    engine = get_engine()

    where = ""
    if ano_mes:
        where = f"AND TO_CHAR(data_transacao, 'YYYY-MM') = '{ano_mes}'"

    sql = f"""
        SELECT
            UPPER(REPLACE(placa, '-', '')) AS placa_norm,
            TO_CHAR(data_transacao, 'YYYY-MM') AS ano_mes,
            SUM(valor)    AS valor_truckpag,
            SUM(litragem) AS litros_truckpag,
            COUNT(*)      AS qtd_transacoes
        FROM integration_truckpag_transacoes
        WHERE litragem > 0
          AND transacao_estornada = '0'
          {where}
        GROUP BY 1, 2
    """
    df = pd.read_sql(sql, engine)
    logger.info(f"TruckPag: {len(df)} registros placa+mês")
    return df


# ── Transformação ─────────────────────────────────────────────────────────────

def _flags(row) -> list[str]:
    # Chamado APÓS a correção de gap_negativo.
    # Usa valor_efetivo/litros_efetivo (já corrigidos) para validações de preço e km/L.
    f = []
    litros = row["litros_efetivo"]
    valor  = row["valor_efetivo"]
    if litros > 0:
        preco_impl = valor / litros
        if preco_impl < 4.0 or preco_impl > 18.0:
            f.append("preco_suspeito")
    if row["total_km"] > 0 and litros > 0 and row["media_kml"] > 0:
        kml_calc = row["total_km"] / litros
        if abs(kml_calc - row["media_kml"]) / row["media_kml"] > 0.20:
            f.append("kml_divergente")
    if row["qtd_transacoes"] == 0 and valor > 0:
        f.append("sem_truckpag")
    return f


def _transform(df_fkm: pd.DataFrame, df_tp: pd.DataFrame) -> pd.DataFrame:
    df = df_fkm.copy()
    df["placa_norm"] = df["placa"].str.upper().str.replace("-", "", regex=False).str.strip()

    merged = df.merge(df_tp, on=["placa_norm", "ano_mes"], how="left")
    merged["valor_truckpag"]  = merged["valor_truckpag"].fillna(0.0)
    merged["litros_truckpag"] = merged["litros_truckpag"].fillna(0.0)
    merged["qtd_transacoes"]  = merged["qtd_transacoes"].fillna(0).astype(int).infer_objects(copy=False)

    merged["valor_direto"]  = merged["valor_comb"] - merged["valor_truckpag"]
    merged["litros_direto"] = merged["litros_comb"] - merged["litros_truckpag"]

    # Caso 1: FKM < TruckPag (gap negativo — erro de preenchimento)
    # Confia no TruckPag e zera o direto.
    gap_neg = merged["valor_direto"] < -100

    # Caso 2: FKM = 0 mas TruckPag > 0 (filial não preencheu o FKM)
    # Mesma lógica: usa TruckPag como fonte e marca como corrigido.
    fkm_vazio_tp_ok = (merged["valor_comb"] == 0) & (merged["valor_truckpag"] > 0)

    corrigido = gap_neg | fkm_vazio_tp_ok
    merged["corrigido_por_truckpag"] = corrigido

    merged.loc[corrigido, "valor_direto"]  = 0.0
    merged.loc[corrigido, "litros_direto"] = 0.0

    # Valores efetivos: TruckPag quando corrigido, FKM quando não
    merged["valor_efetivo"]  = merged["valor_comb"].copy()
    merged["litros_efetivo"] = merged["litros_comb"].copy()
    merged.loc[corrigido, "valor_efetivo"]  = merged.loc[corrigido, "valor_truckpag"]
    merged.loc[corrigido, "litros_efetivo"] = merged.loc[corrigido, "litros_truckpag"]

    merged["pct_truckpag"] = (
        merged["valor_truckpag"] / merged["valor_efetivo"] * 100
    ).where(merged["valor_efetivo"] > 0, 0)

    merged["preco_litro_implicito"] = (
        merged["valor_efetivo"] / merged["litros_efetivo"]
    ).where(merged["litros_efetivo"] > 0, None)

    merged["flags"]      = merged.apply(_flags, axis=1)
    merged["tem_alerta"] = merged["flags"].apply(lambda x: len(x) > 0)

    n_gap_neg    = int(gap_neg.sum())
    n_fkm_vazio  = int(fkm_vazio_tp_ok.sum())
    n_direto     = int((merged["valor_direto"] > 100).sum())
    logger.info(
        f"Transformação: {len(merged)} linhas | "
        f"{n_gap_neg} gap negativo | {n_fkm_vazio} FKM vazio corrigido pelo TruckPag | "
        f"{n_direto} veículos com faturamento direto | "
        f"{merged['tem_alerta'].sum()} alertas restantes"
    )
    return merged


# ── Carga (upsert) ────────────────────────────────────────────────────────────

_UPSERT_SQL = """
INSERT INTO torre.fkm_reconciliacao (
    placa, ano_mes, filial, contrato, grupo_veiculo, tp_combustivel, total_km,
    litros_fkm, valor_fkm, media_kml_fkm,
    litros_truckpag, valor_truckpag, qtd_transacoes,
    litros_efetivo, valor_efetivo,
    litros_direto, valor_direto,
    pct_truckpag, preco_litro_implicito,
    corrigido_por_truckpag, flags, tem_alerta, etl_at
) VALUES (
    :placa, :ano_mes, :filial, :contrato, :grupo_veiculo, :tp_combustivel, :total_km,
    :litros_fkm, :valor_fkm, :media_kml_fkm,
    :litros_truckpag, :valor_truckpag, :qtd_transacoes,
    :litros_efetivo, :valor_efetivo,
    :litros_direto, :valor_direto,
    :pct_truckpag, :preco_litro_implicito,
    :corrigido_por_truckpag, :flags, :tem_alerta, :etl_at
)
ON CONFLICT (placa, ano_mes) DO UPDATE SET
    filial                  = EXCLUDED.filial,
    contrato                = EXCLUDED.contrato,
    grupo_veiculo           = EXCLUDED.grupo_veiculo,
    tp_combustivel          = EXCLUDED.tp_combustivel,
    total_km                = EXCLUDED.total_km,
    litros_fkm              = EXCLUDED.litros_fkm,
    valor_fkm               = EXCLUDED.valor_fkm,
    media_kml_fkm           = EXCLUDED.media_kml_fkm,
    litros_truckpag         = EXCLUDED.litros_truckpag,
    valor_truckpag          = EXCLUDED.valor_truckpag,
    qtd_transacoes          = EXCLUDED.qtd_transacoes,
    litros_efetivo          = EXCLUDED.litros_efetivo,
    valor_efetivo           = EXCLUDED.valor_efetivo,
    litros_direto           = EXCLUDED.litros_direto,
    valor_direto            = EXCLUDED.valor_direto,
    pct_truckpag            = EXCLUDED.pct_truckpag,
    preco_litro_implicito   = EXCLUDED.preco_litro_implicito,
    corrigido_por_truckpag  = EXCLUDED.corrigido_por_truckpag,
    flags                   = EXCLUDED.flags,
    tem_alerta              = EXCLUDED.tem_alerta,
    etl_at                  = EXCLUDED.etl_at
"""


def _safe(v):
    """Converte NaN/None para None (compatível com psycopg2)."""
    if v is None:
        return None
    try:
        import math
        if math.isnan(float(v)):
            return None
    except (TypeError, ValueError):
        pass
    return v


def _load_to_dw(df: pd.DataFrame):
    from db_dw import get_dw_engine
    engine = get_dw_engine()
    now = datetime.now()

    rows = []
    for _, row in df.iterrows():
        rows.append({
            "placa":                  str(row["placa"]),
            "ano_mes":                str(row["ano_mes"]),
            "filial":                 str(row.get("filial", "") or ""),
            "contrato":               str(row.get("contrato", "") or ""),
            "grupo_veiculo":          str(row.get("grupo_veiculo", "") or ""),
            "tp_combustivel":         str(row.get("tp_combustivel", "") or ""),
            "total_km":               _safe(row.get("total_km")),
            "litros_fkm":             _safe(row.get("litros_comb")),
            "valor_fkm":              _safe(row.get("valor_comb")),
            "media_kml_fkm":          _safe(row.get("media_kml")),
            "litros_truckpag":        _safe(row.get("litros_truckpag")),
            "valor_truckpag":         _safe(row.get("valor_truckpag")),
            "qtd_transacoes":         int(row.get("qtd_transacoes", 0)),
            "litros_efetivo":         _safe(row.get("litros_efetivo")),
            "valor_efetivo":          _safe(row.get("valor_efetivo")),
            "litros_direto":          _safe(row.get("litros_direto")),
            "valor_direto":           _safe(row.get("valor_direto")),
            "pct_truckpag":           _safe(row.get("pct_truckpag")),
            "preco_litro_implicito":  _safe(row.get("preco_litro_implicito")),
            "corrigido_por_truckpag": bool(row.get("corrigido_por_truckpag", False)),
            "flags":                  row.get("flags") or [],
            "tem_alerta":             bool(row.get("tem_alerta", False)),
            "etl_at":                 now,
        })

    with engine.begin() as conn:
        conn.execute(text(_UPSERT_SQL), rows)

    logger.info(f"DW: {len(rows)} linhas upsertadas em torre.fkm_reconciliacao")


# ── Entry point ───────────────────────────────────────────────────────────────

def run(ano_mes: str | None = None):
    logger.info(f"=== ETL fkm_reconciliacao | mês: {ano_mes or 'todos'} ===")
    _ensure_table()

    df_fkm = _load_fkm(ano_mes)
    # Agrega TruckPag para todos os meses presentes no FKM filtrado
    meses = sorted(df_fkm["ano_mes"].dropna().unique().tolist())
    df_tp_list = [_load_truckpag(m) for m in meses]
    df_tp = pd.concat(df_tp_list, ignore_index=True) if df_tp_list else pd.DataFrame()

    df_final = _transform(df_fkm, df_tp)
    _load_to_dw(df_final)

    # Resumo por flag para conferência
    todas_flags = [f for flags in df_final["flags"] for f in flags]
    from collections import Counter
    contagem = Counter(todas_flags)
    logger.info("Resumo de alertas: " + (str(dict(contagem)) if contagem else "nenhum"))
    logger.info("=== ETL concluído ===")


if __name__ == "__main__":
    mes_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if mes_arg and mes_arg.lower() == "todos":
        mes_arg = None
    run(mes_arg)
