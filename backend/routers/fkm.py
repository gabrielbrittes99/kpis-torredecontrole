"""
Módulo FKM — Fechamento Mensal de Frota
Fonte: planilha 'Evolucao FKM 2026.xlsb', aba BANCO DE DADOS.

Combina combustível + manutenção + km rodado por veículo/filial/mês,
permitendo calcular o TCO (Total Cost of Ownership) real da frota.
"""
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from db_fkm import get_fkm_df, refresh_fkm_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fkm", tags=["fkm"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _apply_filters(
    df: pd.DataFrame,
    ano_mes: Optional[str] = None,
    filial: Optional[str] = None,
    grupo: Optional[str] = None,
    tp_combustivel: Optional[str] = None,
) -> pd.DataFrame:
    df = df.copy()
    if ano_mes:
        df = df[df["ano_mes"] == ano_mes]
    if filial:
        df = df[df["filial"] == filial]
    if grupo:
        df = df[df["grupo_veiculo"] == grupo]
    if tp_combustivel:
        df = df[df["tp_combustivel"].str.lower() == tp_combustivel.lower()]
    return df


def _safe_round(val, n=2):
    try:
        return round(float(val), n)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: filtros disponíveis
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/filtros")
def get_filtros():
    """Retorna listas de valores disponíveis para filtros."""
    df = get_fkm_df()
    if df.empty:
        return {"meses": [], "filiais": [], "grupos": [], "combustiveis": []}

    meses = sorted(df["ano_mes"].dropna().unique().tolist(), reverse=True)
    filiais = sorted(df["filial"].dropna().unique().tolist())
    filiais = [f for f in filiais if f and f != "nan"]
    grupos = sorted(df["grupo_veiculo"].dropna().unique().tolist())
    grupos = [g for g in grupos if g and g != "nan"]
    combustiveis = sorted(df["tp_combustivel"].dropna().unique().tolist())
    combustiveis = [c for c in combustiveis if c and c != "nan"]

    return {
        "meses": meses,
        "filiais": filiais,
        "grupos": grupos,
        "combustiveis": combustiveis,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 1: KPIs gerais
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis")
def get_kpis(
    ano_mes: Optional[str] = Query(default=None, description="Ex: 2026-01"),
    filial: Optional[str] = None,
    grupo: Optional[str] = None,
    tp_combustivel: Optional[str] = None,
):
    """
    KPIs consolidados do FKM:
    total km frota, custo total, custo/km, km/L médio,
    gastos por categoria (combustível, manutenção, pneus, lataria).
    """
    df = get_fkm_df()
    if df.empty:
        return {}

    # Se não passar mês, usa o mais recente
    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, filial, grupo, tp_combustivel)
    if df.empty:
        return {"ano_mes": ano_mes, "sem_dados": True}

    total_km = float(df["total_km"].sum())
    total_combustivel = float(df["valor_comb"].sum())
    total_arla = float(df["arla"].sum())
    total_manutencao = float(df["manutencao"].sum())
    total_pneus = float(df["rodas_pneus"].sum())
    total_lataria = float(df["lataria_pintura"].sum())
    total_geral_man = float(df["total_geral_manutencao"].sum())
    total_geral = float(df["total"].sum())
    total_litros = float(df["litros_comb"].sum())

    custo_km = _safe_round(total_geral / total_km, 4) if total_km > 0 else None
    custo_km_comb = _safe_round(total_combustivel / total_km, 4) if total_km > 0 else None
    custo_km_man = _safe_round(total_geral_man / total_km, 4) if total_km > 0 else None
    media_kml = _safe_round(total_km / total_litros, 2) if total_litros > 0 else None

    qtd_veiculos = int(df["placa"].nunique())
    qtd_filiais = int(df["filial"].nunique())

    pct_comb = _safe_round(total_combustivel / total_geral * 100, 1) if total_geral > 0 else None
    pct_man = _safe_round(total_geral_man / total_geral * 100, 1) if total_geral > 0 else None

    return {
        "ano_mes": ano_mes,
        "total_km": _safe_round(total_km, 0),
        "total_litros": _safe_round(total_litros, 0),
        "total_combustivel": _safe_round(total_combustivel, 2),
        "total_arla": _safe_round(total_arla, 2),
        "total_manutencao": _safe_round(total_manutencao, 2),
        "total_pneus": _safe_round(total_pneus, 2),
        "total_lataria": _safe_round(total_lataria, 2),
        "total_geral_manutencao": _safe_round(total_geral_man, 2),
        "total_geral": _safe_round(total_geral, 2),
        "custo_km_total": custo_km,
        "custo_km_combustivel": custo_km_comb,
        "custo_km_manutencao": custo_km_man,
        "media_kml": media_kml,
        "qtd_veiculos": qtd_veiculos,
        "qtd_filiais": qtd_filiais,
        "pct_combustivel": pct_comb,
        "pct_manutencao": pct_man,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 2: Resumo por filial
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/resumo-por-filial")
def get_resumo_por_filial(
    ano_mes: Optional[str] = Query(default=None),
    grupo: Optional[str] = None,
    tp_combustivel: Optional[str] = None,
):
    """Tabela: filial × km, combustível, manutenção, pneus, total, custo/km."""
    df = get_fkm_df()
    if df.empty:
        return []

    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, None, grupo, tp_combustivel)
    if df.empty:
        return []

    resultado = []
    for filial, g in df.groupby("filial"):
        if not filial or filial == "nan":
            continue

        total_km = float(g["total_km"].sum())
        total_comb = float(g["valor_comb"].sum())
        total_arla = float(g["arla"].sum())
        total_man = float(g["manutencao"].sum())
        total_pneus = float(g["rodas_pneus"].sum())
        total_lataria = float(g["lataria_pintura"].sum())
        total_geral_man = float(g["total_geral_manutencao"].sum())
        total_geral = float(g["total"].sum())
        total_litros = float(g["litros_comb"].sum())

        custo_km = _safe_round(total_geral / total_km, 4) if total_km > 0 else None
        media_kml = _safe_round(total_km / total_litros, 2) if total_litros > 0 else None

        resultado.append({
            "filial": filial,
            "total_km": _safe_round(total_km, 0),
            "total_litros": _safe_round(total_litros, 0),
            "total_combustivel": _safe_round(total_comb, 2),
            "total_arla": _safe_round(total_arla, 2),
            "total_manutencao": _safe_round(total_man, 2),
            "total_pneus": _safe_round(total_pneus, 2),
            "total_lataria": _safe_round(total_lataria, 2),
            "total_geral_manutencao": _safe_round(total_geral_man, 2),
            "total_geral": _safe_round(total_geral, 2),
            "custo_km": custo_km,
            "media_kml": media_kml,
            "qtd_veiculos": int(g["placa"].nunique()),
        })

    resultado.sort(key=lambda x: x["total_geral"] or 0, reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 3: Custo por veículo (TCO)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/custo-por-veiculo")
def get_custo_por_veiculo(
    ano_mes: Optional[str] = Query(default=None),
    filial: Optional[str] = None,
    grupo: Optional[str] = None,
    limit: int = Query(default=30, le=200),
):
    """Ranking de veículos por custo total (TCO = combustível + manutenção)."""
    df = get_fkm_df()
    if df.empty:
        return []

    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, filial, grupo)
    if df.empty:
        return []

    resultado = []
    for placa, g in df.groupby("placa"):
        total_km = float(g["total_km"].sum())
        total_comb = float(g["valor_comb"].sum())
        total_man = float(g["manutencao"].sum())
        total_pneus = float(g["rodas_pneus"].sum())
        total_lataria = float(g["lataria_pintura"].sum())
        total_geral = float(g["total"].sum())
        total_litros = float(g["litros_comb"].sum())

        custo_km = _safe_round(total_geral / total_km, 4) if total_km > 0 else None
        media_kml = _safe_round(total_km / total_litros, 2) if total_litros > 0 else None

        filial_v = g["filial"].mode().iloc[0] if not g["filial"].mode().empty else ""
        modelo = g["modelo_simplificado"].mode().iloc[0] if not g["modelo_simplificado"].mode().empty else ""
        grupo_v = g["grupo_veiculo"].mode().iloc[0] if not g["grupo_veiculo"].mode().empty else ""
        motorista = g["motorista_principal"].mode().iloc[0] if not g["motorista_principal"].mode().empty else ""
        tp_comb = g["tp_combustivel"].mode().iloc[0] if not g["tp_combustivel"].mode().empty else ""

        resultado.append({
            "placa": placa,
            "modelo": modelo,
            "grupo": grupo_v,
            "filial": filial_v,
            "motorista": motorista,
            "tp_combustivel": tp_comb,
            "total_km": _safe_round(total_km, 0),
            "total_litros": _safe_round(total_litros, 0),
            "total_combustivel": _safe_round(total_comb, 2),
            "total_manutencao": _safe_round(total_man, 2),
            "total_pneus": _safe_round(total_pneus, 2),
            "total_lataria": _safe_round(total_lataria, 2),
            "total_geral": _safe_round(total_geral, 2),
            "custo_km": custo_km,
            "media_kml": media_kml,
        })

    resultado.sort(key=lambda x: x["total_geral"] or 0, reverse=True)
    return resultado[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 4: Evolução mensal
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/evolucao-mensal")
def get_evolucao_mensal(
    filial: Optional[str] = None,
    grupo: Optional[str] = None,
    tp_combustivel: Optional[str] = None,
):
    """Histórico mensal: km, combustível, manutenção, custo/km por mês."""
    df = get_fkm_df()
    if df.empty:
        return []

    df = _apply_filters(df, None, filial, grupo, tp_combustivel)
    if df.empty:
        return []

    resultado = []
    for am in sorted(df["ano_mes"].dropna().unique().tolist()):
        g = df[df["ano_mes"] == am]

        total_km = float(g["total_km"].sum())
        total_comb = float(g["valor_comb"].sum())
        total_geral_man = float(g["total_geral_manutencao"].sum())
        total_geral = float(g["total"].sum())
        total_litros = float(g["litros_comb"].sum())

        custo_km = _safe_round(total_geral / total_km, 4) if total_km > 0 else None
        media_kml = _safe_round(total_km / total_litros, 2) if total_litros > 0 else None

        resultado.append({
            "ano_mes": am,
            "total_km": _safe_round(total_km, 0),
            "total_litros": _safe_round(total_litros, 0),
            "total_combustivel": _safe_round(total_comb, 2),
            "total_manutencao": _safe_round(total_geral_man, 2),
            "total_geral": _safe_round(total_geral, 2),
            "custo_km": custo_km,
            "media_kml": media_kml,
            "qtd_veiculos": int(g["placa"].nunique()),
        })

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 5: Distribuição por categoria
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/distribuicao-categorias")
def get_distribuicao_categorias(
    ano_mes: Optional[str] = Query(default=None),
    filial: Optional[str] = None,
    grupo: Optional[str] = None,
):
    """Distribuição percentual do gasto total por categoria."""
    df = get_fkm_df()
    if df.empty:
        return []

    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, filial, grupo)
    if df.empty:
        return []

    categorias = {
        "Combustível": float(df["valor_comb"].sum()),
        "Arla": float(df["arla"].sum()),
        "Manutenção": float(df["manutencao"].sum()),
        "Pneus": float(df["rodas_pneus"].sum()),
        "Lataria e Pintura": float(df["lataria_pintura"].sum()),
    }

    total = sum(categorias.values())
    resultado = []
    for nome, valor in categorias.items():
        if valor > 0:
            resultado.append({
                "categoria": nome,
                "valor": _safe_round(valor, 2),
                "pct": _safe_round(valor / total * 100, 1) if total > 0 else 0,
            })

    resultado.sort(key=lambda x: x["valor"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 6: Ranking km/L por grupo
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/ranking-km-litro")
def get_ranking_km_litro(
    ano_mes: Optional[str] = Query(default=None),
    filial: Optional[str] = None,
    limit: int = Query(default=30, le=100),
):
    """Ranking de km/L por veículo, agrupado por tipo (Leve, Médio, Pesado, Caminhão)."""
    df = get_fkm_df()
    if df.empty:
        return []

    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, filial)

    # Só considera veículos com km e litros válidos
    df = df[(df["total_km"] > 0) & (df["litros_comb"] > 0)].copy()
    if df.empty:
        return []

    resultado = []
    for placa, g in df.groupby("placa"):
        total_km = float(g["total_km"].sum())
        total_litros = float(g["litros_comb"].sum())
        if total_km <= 0 or total_litros <= 0:
            continue

        media_kml = _safe_round(total_km / total_litros, 2)
        grupo_v = g["grupo_veiculo"].mode().iloc[0] if not g["grupo_veiculo"].mode().empty else ""
        modelo = g["modelo_simplificado"].mode().iloc[0] if not g["modelo_simplificado"].mode().empty else ""
        filial_v = g["filial"].mode().iloc[0] if not g["filial"].mode().empty else ""
        motorista = g["motorista_principal"].mode().iloc[0] if not g["motorista_principal"].mode().empty else ""
        tp_comb = g["tp_combustivel"].mode().iloc[0] if not g["tp_combustivel"].mode().empty else ""

        resultado.append({
            "placa": placa,
            "modelo": modelo,
            "grupo": grupo_v,
            "filial": filial_v,
            "motorista": motorista,
            "tp_combustivel": tp_comb,
            "total_km": _safe_round(total_km, 0),
            "total_litros": _safe_round(total_litros, 0),
            "media_kml": media_kml,
        })

    # Calcula média por grupo para referência
    grupos_media = {}
    for item in resultado:
        grp = item["grupo"]
        if grp not in grupos_media:
            grupos_media[grp] = []
        grupos_media[grp].append(item["media_kml"])

    medias_grupo = {
        grp: round(sum(vals) / len(vals), 2)
        for grp, vals in grupos_media.items() if vals
    }

    for item in resultado:
        media_ref = medias_grupo.get(item["grupo"])
        item["media_grupo"] = media_ref
        item["pct_vs_grupo"] = (
            _safe_round((item["media_kml"] - media_ref) / media_ref * 100, 1)
            if media_ref else None
        )

    resultado.sort(key=lambda x: x["media_kml"] or 0, reverse=True)
    return resultado[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: refresh de cache
# ═══════════════════════════════════════════════════════════════════════════
@router.post("/cache/refresh")
def post_refresh_cache():
    """Força recarregamento do arquivo FKM."""
    return refresh_fkm_cache()
