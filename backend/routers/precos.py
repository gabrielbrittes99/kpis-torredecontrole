"""
Seção 2 — Inteligência de Preços
Análise de preços por tipo de combustível, UF e postos.
"""
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from data_cache import cache

router = APIRouter(prefix="/api/precos", tags=["precos"])


def _apply_filters(
    df: pd.DataFrame,
    combustivel: Optional[str],
    placa: Optional[str],
    modo_tempo: str = "historico",
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
) -> pd.DataFrame:
    if combustivel:
        df = df[df["grupo_combustivel"] == combustivel]
    if placa:
        df = df[df["placa"] == placa.upper()]
    # Filtro temporal (quando não for "historico")
    if modo_tempo == "mes" and mes and ano:
        df = df[(df["data_transacao"].dt.month == mes) & (df["data_transacao"].dt.year == ano)]
    elif modo_tempo == "bimestre" and bimestre and ano:
        months = [bimestre * 2 - 1, bimestre * 2]
        df = df[(df["data_transacao"].dt.month.isin(months)) & (df["data_transacao"].dt.year == ano)]
    elif modo_tempo == "semestre" and semestre and ano:
        months = list(range(1, 7)) if semestre == 1 else list(range(7, 13))
        df = df[(df["data_transacao"].dt.month.isin(months)) & (df["data_transacao"].dt.year == ano)]
    elif modo_tempo == "ano" and ano:
        df = df[df["data_transacao"].dt.year == ano]
    elif modo_tempo == "personalizado" and data_inicio and data_fim:
        df = df[(df["data_transacao"] >= data_inicio) & (df["data_transacao"] <= data_fim)]
    return df


# ---------------------------------------------------------------------------
# Preço médio por UF
# ---------------------------------------------------------------------------

@router.get("/preco-por-uf")
def get_preco_por_uf(
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
    modo_tempo: str = Query("historico"),
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    bimestre: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
):
    """Preço médio por litro agrupado por estado (UF)."""
    df = _apply_filters(
        cache.get_df(), combustivel, placa,
        modo_tempo, mes, ano, bimestre, semestre, data_inicio, data_fim
    )
    if df.empty:
        return []

    df = df[df["uf_posto"] != ""].copy()

    agg = (
        df.groupby("uf_posto")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
        )
        .reset_index()
    )
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(2)
    agg = agg.sort_values("uf_posto")

    return [
        {
            "uf": row["uf_posto"],
            "preco_medio": float(row["preco_medio"]),
            "total_litros": round(float(row["total_litros"]), 0),
            "total_valor": round(float(row["total_valor"]), 2),
            "qtd_abastecimentos": int(row["qtd"]),
        }
        for _, row in agg.iterrows()
    ]


# ---------------------------------------------------------------------------
# Ranking de postos por preço médio
# ---------------------------------------------------------------------------

@router.get("/ranking-postos-preco")
def get_ranking_postos_preco(
    limit: int = Query(default=10, le=50),
    ordem: str = Query(default="mais_barato"),  # mais_barato | mais_caro
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
    modo_tempo: str = Query("historico"),
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    bimestre: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
):
    """Postos ordenados por preço médio/L, maior volume ou maior custo total (mínimo 3 abastecimentos)."""
    df = _apply_filters(
        cache.get_df(), combustivel, placa,
        modo_tempo, mes, ano, bimestre, semestre, data_inicio, data_fim
    )
    if df.empty:
        return []

    # Nome de exibição: usa nome_fantasia_posto se disponível, senão razao_social_posto
    df = df.copy()
    df["nome_exibicao"] = df["nome_fantasia_posto"].where(
        df["nome_fantasia_posto"].str.len() > 0, df["razao_social_posto"]
    )

    agg = (
        df.groupby(["nome_exibicao", "razao_social_posto", "cidade_posto", "uf_posto"])
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
        )
        .reset_index()
    )
    # Só postos com pelo menos 3 abastecimentos (mais representativos)
    agg = agg[agg["qtd"] >= 3].copy()
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(2)

    if ordem == "mais_barato":
        agg = agg.sort_values("preco_medio", ascending=True).head(limit)
    elif ordem == "mais_caro":
        agg = agg.sort_values("preco_medio", ascending=False).head(limit)
    elif ordem == "maior_volume":
        agg = agg.sort_values("total_litros", ascending=False).head(limit)
    elif ordem == "maior_custo":
        agg = agg.sort_values("total_valor", ascending=False).head(limit)
    else:
        agg = agg.sort_values("preco_medio", ascending=True).head(limit)

    return [
        {
            "razao_social_posto": row["nome_exibicao"],   # exibe nome fantasia se disponível
            "razao_social_juridica": row["razao_social_posto"],
            "cidade_posto": row["cidade_posto"],
            "uf_posto": row["uf_posto"],
            "preco_medio": float(row["preco_medio"]),
            "total_litros": round(float(row["total_litros"]), 0),
            "total_valor": round(float(row["total_valor"]), 2),
            "qtd_abastecimentos": int(row["qtd"]),
        }
        for _, row in agg.iterrows()
    ]
