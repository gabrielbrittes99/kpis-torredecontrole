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
) -> pd.DataFrame:
    if combustivel:
        df = df[df["nome_combustivel"] == combustivel]
    if placa:
        df = df[df["placa"] == placa.upper()]
    return df


# ---------------------------------------------------------------------------
# Evolução mensal de preço por tipo de combustível
# ---------------------------------------------------------------------------

@router.get("/evolucao-por-tipo")
def get_evolucao_por_tipo(
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """
    Retorna preço médio por litro por mês, separado por tipo de combustível.
    Ideal para gráfico multi-linha.
    """
    df = _apply_filters(cache.get_df(), combustivel, placa)
    if df.empty:
        return []

    df = df.copy()
    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    agg = (
        df.groupby(["ano_mes", "nome_combustivel"])
        .agg(total_valor=("valor", "sum"), total_litros=("litragem", "sum"))
        .reset_index()
    )
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)

    # Estrutura: lista de meses com preço por tipo
    meses = sorted(agg["ano_mes"].unique())
    tipos = sorted(agg["nome_combustivel"].unique())

    series = []
    for tipo in tipos:
        sub = agg[agg["nome_combustivel"] == tipo].set_index("ano_mes")
        pontos = []
        for mes in meses:
            if mes in sub.index:
                r = sub.loc[mes]
                pontos.append({
                    "ano_mes": mes,
                    "preco_medio": float(r["preco_medio"]),
                    "total_litros": float(r["total_litros"]),
                    "total_valor": float(r["total_valor"]),
                })
            else:
                pontos.append({"ano_mes": mes, "preco_medio": None, "total_litros": 0, "total_valor": 0})
        series.append({"combustivel": tipo, "dados": pontos})

    return {"meses": meses, "series": series}


# ---------------------------------------------------------------------------
# Preço médio por UF
# ---------------------------------------------------------------------------

@router.get("/preco-por-uf")
def get_preco_por_uf(
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """Preço médio por litro agrupado por estado (UF)."""
    df = _apply_filters(cache.get_df(), combustivel, placa)
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
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)
    agg = agg.sort_values("preco_medio")

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
):
    """Postos mais baratos ou mais caros por preço médio/L (mínimo 3 abastecimentos)."""
    df = _apply_filters(cache.get_df(), combustivel, placa)
    if df.empty:
        return []

    agg = (
        df.groupby(["razao_social_posto", "cidade_posto", "uf_posto"])
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
        )
        .reset_index()
    )
    # Só postos com pelo menos 3 abastecimentos (mais representativos)
    agg = agg[agg["qtd"] >= 3].copy()
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)

    ascending = ordem == "mais_barato"
    agg = agg.sort_values("preco_medio", ascending=ascending).head(limit)

    return [
        {
            "razao_social_posto": row["razao_social_posto"],
            "cidade_posto": row["cidade_posto"],
            "uf_posto": row["uf_posto"],
            "preco_medio": float(row["preco_medio"]),
            "total_litros": round(float(row["total_litros"]), 0),
            "total_valor": round(float(row["total_valor"]), 2),
            "qtd_abastecimentos": int(row["qtd"]),
        }
        for _, row in agg.iterrows()
    ]


# ---------------------------------------------------------------------------
# Análise de aditivos / combustíveis premium
# ---------------------------------------------------------------------------

@router.get("/analise-premium")
def get_analise_premium(
    placa: Optional[str] = Query(None),
):
    """
    Separa combustíveis comuns vs premium/aditivados.
    Mostra gasto extra estimado em relação ao tipo mais barato equivalente.
    """
    df = cache.get_df().copy()
    if placa:
        df = df[df["placa"] == placa.upper()]

    if df.empty:
        return {"grupos": [], "gasto_premium_total": 0}

    # Classificar por tipo
    PREMIUM_KEYWORDS = ["aditivad", "premium", "v-power", "podium", "select", "boa", "super"]

    def classificar(nome: str) -> str:
        n = nome.lower()
        if any(k in n for k in PREMIUM_KEYWORDS):
            return "premium"
        return "comum"

    df["categoria"] = df["nome_combustivel"].apply(classificar)

    agg = (
        df.groupby(["nome_combustivel", "categoria"])
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
        )
        .reset_index()
    )
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)

    grupos = [
        {
            "nome": row["nome_combustivel"],
            "categoria": row["categoria"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 0),
            "preco_medio": float(row["preco_medio"]),
            "qtd": int(row["qtd"]),
        }
        for _, row in agg.sort_values("preco_medio").iterrows()
    ]

    # Gasto extra: diferença entre premium e o mais barato de cada família
    total_premium = float(agg[agg["categoria"] == "premium"]["total_valor"].sum())

    return {
        "grupos": grupos,
        "gasto_premium_total": round(total_premium, 2),
    }


# ---------------------------------------------------------------------------
# Variação de preço mês a mês (para alertas)
# ---------------------------------------------------------------------------

@router.get("/variacao-mensal")
def get_variacao_mensal(
    combustivel: Optional[str] = Query(None),
):
    """Variação % do preço médio entre meses consecutivos por tipo."""
    df = cache.get_df().copy()
    if combustivel:
        df = df[df["nome_combustivel"] == combustivel]

    if df.empty:
        return []

    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    agg = (
        df.groupby(["ano_mes", "nome_combustivel"])
        .agg(total_valor=("valor", "sum"), total_litros=("litragem", "sum"))
        .reset_index()
        .sort_values(["nome_combustivel", "ano_mes"])
    )
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)
    agg["variacao_pct"] = agg.groupby("nome_combustivel")["preco_medio"].pct_change() * 100
    agg["variacao_pct"] = agg["variacao_pct"].round(2)

    return [
        {
            "ano_mes": row["ano_mes"],
            "combustivel": row["nome_combustivel"],
            "preco_medio": float(row["preco_medio"]),
            "variacao_pct": float(row["variacao_pct"]) if pd.notna(row["variacao_pct"]) else None,
        }
        for _, row in agg.iterrows()
    ]
