"""
Seção 6 — Benchmark ANP
Compara preços pagos pela frota com a média de mercado (ANP) por UF e combustível.
"""
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from anp_client import get_benchmark_nacional, get_benchmark_por_uf, get_anp_df
from data_cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


# Mapeamento fuzzy: nome do combustível no TruckPag → produto ANP
_MATCH = [
    (["diesel s10", "s10", "s-10"], "DIESEL S10"),
    (["diesel", "óleo diesel", "oleo diesel"], "DIESEL"),
    (["gasolina aditivada", "gasolina boa", "gasolina podium", "gasolina v-power", "gasolina select", "gasolina super"], "GASOLINA ADITIVADA"),
    (["gasolina", "gasolina comum", "gasolina c"], "GASOLINA COMUM"),
    (["etanol", "álcool", "alcool"], "ETANOL HIDRATADO"),
    (["gnv", "gás natural", "gas natural"], "GNV"),
]


def _match_produto(nome: str) -> Optional[str]:
    n = nome.lower().strip()
    for keywords, anp_name in _MATCH:
        if any(k in n for k in keywords):
            return anp_name
    return None


@router.get("/nacional")
def get_benchmark_nacional_endpoint():
    """Preço médio ANP nacional por tipo de combustível (mês mais recente disponível)."""
    return get_benchmark_nacional()


@router.get("/por-uf")
def get_benchmark_uf_endpoint():
    """Preço médio ANP por UF e tipo de combustível."""
    return get_benchmark_por_uf()


@router.get("/comparativo-frota")
def get_comparativo_frota(
    uf: Optional[str] = Query(None, description="Filtrar por UF (ex: SP, PR)"),
):
    """
    Compara o preço médio pago pela frota com a média ANP de mercado,
    por UF e tipo de combustível. Mostra desvio em R$ e %.
    """
    df_frota = cache.get_df().copy()
    df_anp = get_anp_df()

    if df_frota.empty or df_anp.empty:
        return []

    if uf:
        df_frota = df_frota[df_frota["uf_posto"] == uf.upper()]

    if df_frota.empty:
        return []

    # Mapeia combustível TruckPag → produto ANP
    df_frota["produto_anp"] = df_frota["nome_combustivel"].apply(_match_produto)
    df_frota = df_frota[df_frota["produto_anp"].notna()].copy()

    # Preço médio da frota por UF + produto
    frota_agg = (
        df_frota.groupby(["uf_posto", "produto_anp"])
        .apply(lambda g: pd.Series({
            "preco_frota": (g["valor"].sum() / g["litragem"].sum()),
            "total_litros": g["litragem"].sum(),
            "total_valor": g["valor"].sum(),
            "qtd_abastecimentos": len(g),
        }))
        .reset_index()
    )

    # Preço médio ANP por UF + produto
    anp_agg = (
        df_anp.groupby(["uf", "produto"])["preco"]
        .mean()
        .reset_index()
        .rename(columns={"uf": "uf_posto", "produto": "produto_anp", "preco": "preco_anp"})
    )

    merged = frota_agg.merge(anp_agg, on=["uf_posto", "produto_anp"], how="left")

    resultado = []
    for _, row in merged.iterrows():
        preco_frota = float(row["preco_frota"])
        preco_anp = float(row["preco_anp"]) if pd.notna(row["preco_anp"]) else None
        desvio_abs = round(preco_frota - preco_anp, 4) if preco_anp else None
        desvio_pct = round((preco_frota - preco_anp) / preco_anp * 100, 2) if preco_anp else None
        economia_potencial = round(desvio_abs * float(row["total_litros"]), 2) if desvio_abs else None

        resultado.append({
            "uf": row["uf_posto"],
            "combustivel": row["produto_anp"],
            "preco_frota": round(preco_frota, 4),
            "preco_anp_mercado": round(preco_anp, 4) if preco_anp else None,
            "desvio_abs": desvio_abs,
            "desvio_pct": desvio_pct,
            "economia_potencial": economia_potencial,
            "total_litros": round(float(row["total_litros"]), 0),
            "total_valor": round(float(row["total_valor"]), 2),
            "qtd_abastecimentos": int(row["qtd_abastecimentos"]),
            "status": (
                "abaixo_mercado" if desvio_abs and desvio_abs < -0.05
                else "acima_mercado" if desvio_abs and desvio_abs > 0.05
                else "na_media"
            ),
        })

    resultado.sort(key=lambda x: (x["desvio_pct"] or 0), reverse=True)
    return resultado


@router.get("/resumo")
def get_resumo_benchmark():
    """
    Resumo executivo: quanto a frota está pagando acima/abaixo do mercado ANP no total.
    """
    comparativo = get_comparativo_frota()
    if not comparativo:
        return {}

    acima = [r for r in comparativo if r["status"] == "acima_mercado"]
    abaixo = [r for r in comparativo if r["status"] == "abaixo_mercado"]

    economia_total = sum(r["economia_potencial"] or 0 for r in acima)
    gasto_total = sum(r["total_valor"] for r in comparativo)

    return {
        "gasto_total_frota": round(gasto_total, 2),
        "economia_potencial_total": round(economia_total, 2),
        "economia_pct": round(economia_total / gasto_total * 100, 2) if gasto_total else 0,
        "ufs_acima_mercado": len(set(r["uf"] for r in acima)),
        "ufs_abaixo_mercado": len(set(r["uf"] for r in abaixo)),
        "combinacoes_analisadas": len(comparativo),
    }
