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
    (["gasolina", "gasolina comum", "gasolina c"], "GASOLINA"),
    (["etanol", "álcool", "alcool"], "ETANOL"),
    (["gnv", "gás natural", "gas natural"], "GNV"),
]


def _match_produto(nome: Optional[str]) -> Optional[str]:
    if not nome or pd.isna(nome):
        return None
    n = str(nome).lower().strip()
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


@router.get("/interno")
def get_benchmark_interno(
    dias: int = Query(7, description="Janela de dias para média móvel interna")
):
    """
    Benchmark Interno: Preço médio pago pela própria frota nos últimos X dias.
    Serve como indicador de tempo real antes da atualização da ANP.
    """
    df = cache.get_df().copy()
    if df.empty:
        return []

    # Filtra últimos X dias
    limite_data = pd.Timestamp.now() - pd.Timedelta(days=dias)
    df_recente = df[df["data_transacao"] >= limite_data].copy()

    if df_recente.empty:
        return []

    agg = (
        df_recente.groupby(["uf_posto", "nome_combustivel"])
        .apply(lambda g: pd.Series({
            "preco_medio": (g["valor"].sum() / g["litragem"].sum()),
            "total_litros": g["litragem"].sum(),
            "qtd_abastecimentos": len(g)
        }))
        .reset_index()
    )
    
    # Arredondamentos
    agg["preco_medio"] = agg["preco_medio"].round(4)
    
    return agg.to_dict(orient="records")


@router.get("/comparativo-frota")
def get_comparativo_frota(
    uf: Optional[str] = Query(None, description="Filtrar por UF (ex: SP, PR)"),
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    match_temporal: bool = Query(True, description="Tentar correspondência por semana de coleta")
):
    """
    Compara o preço médio pago pela frota com a média ANP de mercado.
    Se match_temporal for True, tenta comparar abastecimentos com a média ANP 
    daquela semana específica de coleta.
    """
    df_frota = cache.get_df().copy()
    if not df_frota.empty:
        if ano:
            df_frota = df_frota[df_frota["data_transacao"].dt.year == ano]
        if mes:
            df_frota = df_frota[df_frota["data_transacao"].dt.month == mes]
    
    df_anp = get_anp_df()

    if df_frota.empty or df_anp.empty:
        return []

    if uf and hasattr(uf, 'upper'):
        df_frota = df_frota[df_frota["uf_posto"] == uf.upper()]

    # Mapeia combustível TruckPag → produto ANP
    df_frota["produto_anp"] = df_frota["nome_combustivel"].apply(_match_produto)
    df_frota = df_frota[df_frota["produto_anp"].notna()].copy()

    if match_temporal and "data_coleta" in df_anp.columns:
        # Lógica de match por semana:
        # Agrupa ANP por UF, Produto e Semana
        df_anp["semana"] = df_anp["data_coleta"].dt.to_period("W").astype(str)
        anp_semanal = (
            df_anp.groupby(["uf", "produto", "semana"])["preco"]
            .mean()
            .reset_index()
            .rename(columns={"uf": "uf_posto", "produto": "produto_anp", "semana": "semana_anp", "preco": "preco_anp"})
        )
        
        # Mapeia frota para semanas
        df_frota["semana_anp"] = df_frota["data_transacao"].dt.to_period("W").astype(str)
        
        # Merge
        merged = df_frota.merge(anp_semanal, on=["uf_posto", "produto_anp", "semana_anp"], how="left")
        
        # Fallback para média global da UF se não houver na semana
        anp_global_uf = df_anp.groupby(["uf", "produto"])["preco"].mean().reset_index().rename(columns={"uf": "uf_posto", "produto": "produto_anp", "preco": "preco_anp_fallback"})
        merged = merged.merge(anp_global_uf, on=["uf_posto", "produto_anp"], how="left")
        merged["preco_anp_final"] = merged["preco_anp"].fillna(merged["preco_anp_fallback"])
        
        # Agrega resultado final
        agg = (
            merged.groupby(["uf_posto", "produto_anp"])
            .apply(lambda g: pd.Series({
                "preco_frota": (g["valor"].sum() / g["litragem"].sum()),
                "preco_anp_mercado": (g["preco_anp_final"] * g["litragem"]).sum() / g["litragem"].sum(), # Média ponderada pela litragem da frota
                "total_litros": g["litragem"].sum(),
                "total_valor": g["valor"].sum(),
                "qtd_abastecimentos": len(g),
            }))
            .reset_index()
        )
    else:
        # Lógica antiga (simplificada)
        frota_agg = df_frota.groupby(["uf_posto", "produto_anp"]).apply(lambda g: pd.Series({
            "preco_frota": (g["valor"].sum() / g["litragem"].sum()),
            "total_litros": g["litragem"].sum(),
            "total_valor": g["valor"].sum(),
            "qtd_abastecimentos": len(g),
        })).reset_index()
        
        anp_agg = df_anp.groupby(["uf", "produto"])["preco"].mean().reset_index().rename(columns={"uf": "uf_posto", "produto": "produto_anp", "preco": "preco_anp_mercado"})
        agg = frota_agg.merge(anp_agg, on=["uf_posto", "produto_anp"], how="left")

    resultado = []
    for _, row in agg.iterrows():
        preco_frota = float(row["preco_frota"])
        preco_anp = float(row["preco_anp_mercado"]) if pd.notna(row["preco_anp_mercado"]) else None
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
    # Filtra para retornar apenas registros que possuem dados da ANP (evita dados distorcidos)
    resultado = [r for r in resultado if r["preco_anp_mercado"] is not None]
    return resultado


@router.get("/resumo")
def get_resumo_benchmark(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None)
):
    """
    Resumo executivo: quanto a frota está pagando acima/abaixo do mercado ANP no total.
    """
    comparativo = get_comparativo_frota(mes=mes, ano=ano)
    if not comparativo:
        return {}

    acima = [r for r in comparativo if r["status"] == "acima_mercado"]
    abaixo = [r for r in comparativo if r["status"] == "abaixo_mercado"]

    economia_total = sum(r["economia_potencial"] or 0 for r in acima)
    gasto_total = sum(r["total_valor"] for r in comparativo)
    
    # Média ponderada da variação %
    total_litros_global = sum(r["total_litros"] for r in comparativo)
    variacao_media_pct = sum((r["desvio_pct"] or 0) * r["total_litros"] for r in comparativo) / total_litros_global if total_litros_global > 0 else 0

    return {
        "gasto_total_frota": round(gasto_total, 2),
        "economia_potencial_total": round(economia_total, 2),
        "economia_pct": round(economia_total / gasto_total * 100, 2) if gasto_total else 0,
        "variacao_media_pct": round(variacao_media_pct, 2),
        "saving_total_mes": round(sum(abs(r["economia_potencial"]) for r in abaixo if r["economia_potencial"] is not None), 2),
        "ufs_acima_mercado": len(set(r["uf"] for r in acima)),
        "ufs_abaixo_mercado": len(set(r["uf"] for r in abaixo)),
        "combinacoes_analisadas": len(comparativo),
    }


@router.get("/comparativo-municipal")
def get_comparativo_municipal(
    uf: Optional[str] = Query(None),
    municipio: Optional[str] = Query(None),
):
    """
    Benchmark detalhado por município.
    """
    df_frota = cache.get_df().copy()
    df_anp = get_anp_df()

    if df_frota.empty or df_anp.empty:
        return []

    # Normaliza município para comparação
    df_frota["cidade_posto_norm"] = df_frota["cidade_posto"].str.upper().str.strip()
    
    if uf and hasattr(uf, 'upper'):
        df_frota = df_frota[df_frota["uf_posto"] == uf.upper()]
    if municipio and hasattr(municipio, 'upper'):
        df_frota = df_frota[df_frota["cidade_posto_norm"] == municipio.upper()]

    if df_frota.empty:
        return []

    df_frota["produto_anp"] = df_frota["nome_combustivel"].apply(_match_produto)
    df_frota = df_frota[df_frota["produto_anp"].notna()].copy()

    # Agrupa frota por UF + Município + Produto
    frota_agg = (
        df_frota.groupby(["uf_posto", "cidade_posto_norm", "produto_anp"])
        .apply(lambda g: pd.Series({
            "preco_frota": (g["valor"].sum() / g["litragem"].sum()),
            "total_litros": g["litragem"].sum(),
        }))
        .reset_index()
    )

    # Agrupa ANP por UF + Município + Produto
    anp_agg = (
        df_anp.groupby(["uf", "municipio", "produto"])["preco"]
        .mean()
        .reset_index()
        .rename(columns={"uf": "uf_posto", "municipio": "cidade_posto_norm", "produto": "produto_anp", "preco": "preco_anp"})
    )

    merged = frota_agg.merge(anp_agg, on=["uf_posto", "cidade_posto_norm", "produto_anp"], how="left")
    
    # Fallback para média estadual se não houver municipal
    anp_uf = df_anp.groupby(["uf", "produto"])["preco"].mean().reset_index().rename(columns={"uf": "uf_posto", "produto": "produto_anp", "preco": "preco_anp_uf"})
    merged = merged.merge(anp_uf, on=["uf_posto", "produto_anp"], how="left")
    
    anp_fallback_name = "preco_anp_fallback" if "preco_anp_fallback" in merged.columns else "preco_anp_uf"
    merged["preco_anp_final"] = merged["preco_anp"].fillna(merged[anp_fallback_name])

    resultado = []
    for _, row in merged.iterrows():
        preco_frota = float(row["preco_frota"])
        preco_anp = float(row["preco_anp_final"]) if pd.notna(row["preco_anp_final"]) else None
        
        resultado.append({
            "uf": row["uf_posto"],
            "municipio": row["cidade_posto_norm"],
            "combustivel": row["produto_anp"],
            "preco_frota": round(preco_frota, 4),
            "preco_anp": round(preco_anp, 4) if preco_anp else None,
            "desvio": round(preco_frota - preco_anp, 4) if preco_anp else 0,
            "tem_dados_municipais": pd.notna(row["preco_anp"])
        })

    return resultado
