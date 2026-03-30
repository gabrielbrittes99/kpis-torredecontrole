import logging
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Query

from data_cache import cache
from utils import safe_round, apply_time_filters, apply_attribute_filters

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/estornos", tags=["estornos"])


def _get_df() -> pd.DataFrame:
    return cache.get_df("estornos")


def _apply_filters(
    df: pd.DataFrame,
    modo_tempo: str = "mes",
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    filial: Optional[str] = None,
    placa: Optional[str] = None,
) -> pd.DataFrame:
    df = apply_time_filters(df, modo_tempo=modo_tempo, ano=ano, mes=mes)
    if placa:
        df = df[df["placa"] == placa.upper().replace("-", "").strip()]
    if filial:
        df = apply_attribute_filters(df, filial=filial)
    return df


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: KPIs de Estornos
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis")
def get_kpis(
    mes:  Optional[int] = Query(default=None),
    ano:  Optional[int] = Query(default=None),
):
    """KPIs gerais: total estornado, quantidade, % sobre total de transações."""
    df = _get_df()
    df = apply_time_filters(df, modo_tempo="mes" if (mes and ano) else "ano" if ano else "mes", ano=ano, mes=mes)

    df_total = cache.get_df("transacoes")
    df_total = apply_time_filters(df_total, modo_tempo="mes" if (mes and ano) else "ano" if ano else "mes", ano=ano, mes=mes)

    total_estornado = float(df["valor"].sum())
    qtd_estornos    = len(df)
    total_tx        = len(df_total) + qtd_estornos  # denominador inclui estornos

    return {
        "total_estornado":    safe_round(total_estornado, 2),
        "quantidade_estornos": qtd_estornos,
        "total_transacoes":   total_tx,
        "pct_estornos":       safe_round(qtd_estornos / total_tx * 100, 2) if total_tx > 0 else 0,
        "ticket_medio":       safe_round(total_estornado / qtd_estornos, 2) if qtd_estornos > 0 else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Auditoria Analítica
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/analitico")
def get_analitico(
    mes:    Optional[int] = Query(default=None),
    ano:    Optional[int] = Query(default=None),
    filial: Optional[str] = Query(default=None),
    placa:  Optional[str] = Query(default=None),
    limit:  int           = Query(default=100, le=500),
):
    """Lista detalhada de transações estornadas para auditoria."""
    df = _get_df()
    modo = "mes" if (mes and ano) else "ano" if ano else "mes"
    df = _apply_filters(df, modo_tempo=modo, ano=ano, mes=mes, filial=filial, placa=placa)

    if df.empty:
        return []

    df = df.copy()
    df["data_transacao"] = df["data_transacao"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df.sort_values("data_transacao", ascending=False).head(limit).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Resumo por Tipo
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/resumo")
def get_resumo(
    mes: Optional[int] = Query(default=None),
    ano: Optional[int] = Query(default=None),
):
    """Total estornado agrupado por tipo de transação (Combustível, Pedágio)."""
    df = _get_df()
    modo = "mes" if (mes and ano) else "ano" if ano else "mes"
    df = apply_time_filters(df, modo_tempo=modo, ano=ano, mes=mes)

    if df.empty:
        return {"total_estornado": 0, "por_tipo": []}

    total_estornado = float(df["valor"].sum())

    por_tipo = []
    for tipo, g in df.groupby("tipo_abastecimento"):
        por_tipo.append({
            "tipo":       tipo,
            "valor":      safe_round(float(g["valor"].sum()), 2),
            "quantidade": len(g),
        })

    return {
        "total_estornado":  safe_round(total_estornado, 2),
        "quantidade_total": len(df),
        "por_tipo":         sorted(por_tipo, key=lambda x: x["valor"], reverse=True),
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Ranking por Placa
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-placa")
def get_por_placa(
    mes:   Optional[int] = Query(default=None),
    ano:   Optional[int] = Query(default=None),
    limit: int           = Query(default=20, le=100),
):
    """Veículos com maior volume de estornos."""
    df = _get_df()
    modo = "mes" if (mes and ano) else "ano" if ano else "mes"
    df = apply_time_filters(df, modo_tempo=modo, ano=ano, mes=mes)

    if df.empty:
        return []

    resumo = (
        df.groupby("placa")
        .agg(total_valor=("valor", "sum"), qtd=("valor", "count"))
        .reset_index()
        .sort_values("total_valor", ascending=False)
        .head(limit)
    )
    resumo["total_valor"] = resumo["total_valor"].apply(lambda v: safe_round(v, 2))
    return resumo.to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Ranking por Filial
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/ranking-filiais")
def get_ranking_filiais(
    mes: Optional[int] = Query(default=None),
    ano: Optional[int] = Query(default=None),
):
    """Filiais com maior volume de estornos."""
    df = _get_df()
    modo = "mes" if (mes and ano) else "ano" if ano else "mes"
    df = apply_time_filters(df, modo_tempo=modo, ano=ano, mes=mes)

    if df.empty:
        return []

    col_filial = "filial_nome" if "filial_nome" in df.columns else "filial"
    if col_filial not in df.columns:
        return []

    resumo = (
        df.groupby(col_filial)
        .agg(total_valor=("valor", "sum"), qtd=("valor", "count"))
        .reset_index()
        .rename(columns={col_filial: "filial"})
        .sort_values("total_valor", ascending=False)
    )
    resumo["total_valor"] = resumo["total_valor"].apply(lambda v: safe_round(v, 2))
    return resumo.to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Evolução Mensal
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/evolucao-mensal")
def get_evolucao_mensal(
    filial: Optional[str] = Query(default=None),
    placa:  Optional[str] = Query(default=None),
):
    """Série mensal de estornos (valor e quantidade)."""
    df = _get_df()
    if filial:
        df = apply_attribute_filters(df, filial=filial)
    if placa:
        df = df[df["placa"] == placa.upper().replace("-", "").strip()]

    if df.empty:
        return []

    df = df.copy()
    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    evolucao = (
        df.groupby("ano_mes")
        .agg(total_valor=("valor", "sum"), quantidade=("valor", "count"))
        .reset_index()
        .sort_values("ano_mes")
    )
    evolucao["total_valor"] = evolucao["total_valor"].apply(lambda v: safe_round(v, 2))
    return evolucao.to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Rastreio de Auditoria
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/rastreio/{transacao_id}")
def get_rastreio(transacao_id: str):
    """
    Trilha de auditoria para uma transação.
    Dado um ID, retorna: a transação original (se houver), o estorno, e a substituta.
    """
    df_estornos  = _get_df()
    df_transacoes = cache.get_df("transacoes")

    resultado = {"transacao_id": transacao_id, "cadeia": []}

    # Caso 1: o ID informado É uma transação estornada (está em df_estornos)
    estorno = df_estornos[df_estornos["transacao"] == transacao_id]
    if not estorno.empty:
        row = estorno.iloc[0]
        resultado["cadeia"].append({
            "papel": "estorno",
            "transacao":          str(row.get("transacao", "")),
            "transacao_original": str(row.get("transacao_estornada", "")),
            "data":   row["data_transacao"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(row["data_transacao"]) else None,
            "valor":  safe_round(float(row["valor"]), 2),
            "placa":  row.get("placa", ""),
        })
        # Busca a transação original no cache principal
        id_original = str(row.get("transacao_estornada", ""))
        if id_original:
            original = df_transacoes[df_transacoes["transacao"] == id_original]
            if not original.empty:
                r = original.iloc[0]
                resultado["cadeia"].insert(0, {
                    "papel":     "original",
                    "transacao": str(r.get("transacao", "")),
                    "data":      r["data_transacao"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(r["data_transacao"]) else None,
                    "valor":     safe_round(float(r["valor"]), 2),
                    "placa":     r.get("placa", ""),
                })

    # Caso 2: o ID informado É uma transação original (encontrada no cache principal)
    original_tx = df_transacoes[df_transacoes["transacao"] == transacao_id]
    if not original_tx.empty and estorno.empty:
        row = original_tx.iloc[0]
        resultado["cadeia"].append({
            "papel":     "original",
            "transacao": str(row.get("transacao", "")),
            "data":      row["data_transacao"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(row["data_transacao"]) else None,
            "valor":     safe_round(float(row["valor"]), 2),
            "placa":     row.get("placa", ""),
        })
        # Verifica se existe estorno apontando para este ID
        estorno_ref = df_estornos[df_estornos["transacao_estornada"] == transacao_id]
        if not estorno_ref.empty:
            r = estorno_ref.iloc[0]
            resultado["cadeia"].append({
                "papel":     "estorno",
                "transacao": str(r.get("transacao", "")),
                "data":      r["data_transacao"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(r["data_transacao"]) else None,
                "valor":     safe_round(float(r["valor"]), 2),
                "placa":     r.get("placa", ""),
            })

    if not resultado["cadeia"]:
        resultado["mensagem"] = "Transação não encontrada em nenhum cache."

    return resultado
