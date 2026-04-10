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

from data_cache import cache
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
    contrato: Optional[str] = None,
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
    if contrato:
        df = df[df["contrato"] == contrato]
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
        return {"meses": [], "filiais": [], "grupos": [], "combustiveis": [], "contratos": []}

    meses = sorted(df["ano_mes"].dropna().unique().tolist(), reverse=True)
    filiais = sorted(df["filial"].dropna().unique().tolist())
    filiais = [f for f in filiais if f and f != "nan"]
    grupos = sorted(df["grupo_veiculo"].dropna().unique().tolist())
    grupos = [g for g in grupos if g and g != "nan"]
    combustiveis = sorted(df["tp_combustivel"].dropna().unique().tolist())
    combustiveis = [c for c in combustiveis if c and c != "nan"]
    contratos = sorted(df["contrato"].dropna().unique().tolist())
    contratos = [c for c in contratos if c and c != "nan"]

    return {
        "meses": meses,
        "filiais": filiais,
        "grupos": grupos,
        "combustiveis": combustiveis,
        "contratos": contratos,
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
    contrato: Optional[str] = None,
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

    df = _apply_filters(df, ano_mes, filial, grupo, tp_combustivel, contrato)
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

    custo_km = _safe_round(total_geral / total_km, 2) if total_km > 0 else None
    custo_km_comb = _safe_round(total_combustivel / total_km, 2) if total_km > 0 else None
    custo_km_man = _safe_round(total_geral_man / total_km, 2) if total_km > 0 else None
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
    contrato: Optional[str] = None,
):
    """Tabela: filial × km, combustível, manutenção, pneus, total, custo/km."""
    df = get_fkm_df()
    if df.empty:
        return []

    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, None, grupo, tp_combustivel, contrato)
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

        custo_km = _safe_round(total_geral / total_km, 2) if total_km > 0 else None
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
    contrato: Optional[str] = None,
    limit: int = Query(default=30, le=200),
):
    """Ranking de veículos por custo total (TCO = combustível + manutenção)."""
    df = get_fkm_df()
    if df.empty:
        return []

    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, filial, grupo, contrato=contrato)
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

        custo_km = _safe_round(total_geral / total_km, 2) if total_km > 0 else None
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
    contrato: Optional[str] = None,
):
    """Histórico mensal: km, combustível, manutenção, custo/km por mês."""
    df = get_fkm_df()
    if df.empty:
        return []

    df = _apply_filters(df, None, filial, grupo, tp_combustivel, contrato)
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

        custo_km = _safe_round(total_geral / total_km, 2) if total_km > 0 else None
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
    contrato: Optional[str] = None,
):
    """Distribuição percentual do gasto total por categoria."""
    df = get_fkm_df()
    if df.empty:
        return []

    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, filial, grupo, contrato=contrato)
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
    contrato: Optional[str] = None,
    limit: int = Query(default=30, le=100),
):
    """Ranking de km/L por veículo, agrupado por tipo (Leve, Médio, Pesado, Caminhão)."""
    df = get_fkm_df()
    if df.empty:
        return []

    if not ano_mes:
        meses = sorted(df["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df = _apply_filters(df, ano_mes, filial, contrato=contrato)

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
# ENDPOINT: Reconciliação FKM × TruckPag
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/reconciliacao")
def get_reconciliacao(
    ano_mes: Optional[str] = Query(default=None, description="Ex: 2026-02. Padrão: mês mais recente do FKM"),
    filial: Optional[str] = None,
    contrato: Optional[str] = None,
):
    """
    Cruza o FKM (total real de combustível) com o TruckPag (só cartão)
    para calcular o volume faturado diretamente (fora do cartão) por veículo.

    Retorna por placa:
    - valor_fkm / litros_fkm: total real (FKM)
    - valor_truckpag / litros_truckpag: só via cartão
    - valor_direto / litros_direto: gap (faturado direto)
    - pct_truckpag: % do custo coberto pelo cartão
    - flags: validações de qualidade (gap_negativo, preco_suspeito, kml_divergente)
    """
    df_fkm = get_fkm_df()
    if df_fkm.empty:
        return {"ano_mes": ano_mes, "veiculos": [], "resumo_filiais": []}

    if not ano_mes:
        meses = sorted(df_fkm["ano_mes"].dropna().unique().tolist())
        ano_mes = meses[-1] if meses else None

    df_fkm = _apply_filters(df_fkm, ano_mes=ano_mes, filial=filial, contrato=contrato)
    if df_fkm.empty:
        return {"ano_mes": ano_mes, "veiculos": [], "resumo_filiais": []}

    # ── Agrega TruckPag por placa + ano_mes ──────────────────────────────────
    df_tp = cache.get_df().copy()
    df_tp = df_tp[df_tp["litragem"] > 0]  # só abastecimentos, não pedágios
    df_tp["ano_mes"] = df_tp["data_transacao"].dt.to_period("M").astype(str)
    df_tp["placa_norm"] = df_tp["placa"].str.upper().str.replace("-", "", regex=False).str.strip()

    tp_agg = (
        df_tp[df_tp["ano_mes"] == ano_mes]
        .groupby("placa_norm")
        .agg(
            valor_truckpag=("valor", "sum"),
            litros_truckpag=("litragem", "sum"),
            qtd_transacoes=("valor", "count"),
        )
        .reset_index()
    )

    # ── Junta FKM + TruckPag ─────────────────────────────────────────────────
    df_fkm = df_fkm.copy()
    df_fkm["placa_norm"] = df_fkm["placa"].str.upper().str.replace("-", "", regex=False).str.strip()

    merged = df_fkm.merge(tp_agg, on="placa_norm", how="left")
    merged["valor_truckpag"]  = merged["valor_truckpag"].fillna(0.0)
    merged["litros_truckpag"] = merged["litros_truckpag"].fillna(0.0)
    merged["qtd_transacoes"]  = merged["qtd_transacoes"].fillna(0).astype(int)

    merged["valor_direto"]  = merged["valor_comb"] - merged["valor_truckpag"]
    merged["litros_direto"] = merged["litros_comb"] - merged["litros_truckpag"]
    merged["pct_truckpag"]  = (
        (merged["valor_truckpag"] / merged["valor_comb"] * 100)
        .where(merged["valor_comb"] > 0, 0)
    )

    # ── Flags de qualidade ───────────────────────────────────────────────────
    def _flags(row) -> list[str]:
        f = []
        # Gap negativo: FKM registra menos que o TruckPag (erro de preenchimento)
        if row["valor_direto"] < -100:
            f.append("gap_negativo")
        # Preço/L implícito fora da faixa esperada (R$ 4–18)
        if row["litros_comb"] > 0:
            preco_impl = row["valor_comb"] / row["litros_comb"]
            if preco_impl < 4.0 or preco_impl > 18.0:
                f.append("preco_suspeito")
        # km/L calculado diverge do informado pela filial (> 20%)
        if row["total_km"] > 0 and row["litros_comb"] > 0 and row["media_kml"] > 0:
            kml_calc = row["total_km"] / row["litros_comb"]
            desvio = abs(kml_calc - row["media_kml"]) / row["media_kml"]
            if desvio > 0.20:
                f.append("kml_divergente")
        # Sem nenhuma transação TruckPag no mês (100% direto)
        if row["qtd_transacoes"] == 0 and row["valor_comb"] > 0:
            f.append("sem_truckpag")
        return f

    merged["flags"] = merged.apply(_flags, axis=1)
    merged["tem_alerta"] = merged["flags"].apply(lambda x: len(x) > 0)

    # ── Monta resultado por veículo ──────────────────────────────────────────
    veiculos = []
    for _, row in merged.iterrows():
        veiculos.append({
            "placa": row["placa"],
            "filial": row["filial"],
            "contrato": row.get("contrato", ""),
            "grupo_veiculo": row["grupo_veiculo"],
            "modelo": row.get("modelo_simplificado", ""),
            "motorista": row.get("motorista_principal", ""),
            "tp_combustivel": row["tp_combustivel"],
            "total_km": _safe_round(row["total_km"], 0),
            # FKM (total real)
            "valor_fkm": _safe_round(row["valor_comb"], 2),
            "litros_fkm": _safe_round(row["litros_comb"], 1),
            "media_kml_fkm": _safe_round(row["media_kml"], 2),
            # TruckPag
            "valor_truckpag": _safe_round(row["valor_truckpag"], 2),
            "litros_truckpag": _safe_round(row["litros_truckpag"], 1),
            "qtd_transacoes_tp": int(row["qtd_transacoes"]),
            # Direto (gap)
            "valor_direto": _safe_round(row["valor_direto"], 2),
            "litros_direto": _safe_round(row["litros_direto"], 1),
            # Métricas
            "pct_truckpag": _safe_round(row["pct_truckpag"], 1),
            "preco_litro_implicito": _safe_round(
                row["valor_comb"] / row["litros_comb"], 2
            ) if row["litros_comb"] > 0 else None,
            # Qualidade
            "flags": row["flags"],
            "tem_alerta": bool(row["tem_alerta"]),
        })

    veiculos.sort(key=lambda x: x["valor_direto"] or 0, reverse=True)

    # ── Resumo por filial ────────────────────────────────────────────────────
    df_res = merged.groupby("filial").agg(
        total_valor_fkm=("valor_comb", "sum"),
        total_valor_tp=("valor_truckpag", "sum"),
        total_valor_direto=("valor_direto", "sum"),
        qtd_veiculos=("placa", "count"),
        qtd_com_direto=("valor_direto", lambda x: (x > 100).sum()),
        qtd_alertas=("tem_alerta", "sum"),
    ).reset_index()

    df_res["pct_truckpag"] = (df_res["total_valor_tp"] / df_res["total_valor_fkm"] * 100).where(
        df_res["total_valor_fkm"] > 0, 0
    )

    resumo_filiais = [
        {
            "filial": row["filial"],
            "total_valor_fkm": _safe_round(row["total_valor_fkm"], 2),
            "total_valor_truckpag": _safe_round(row["total_valor_tp"], 2),
            "total_valor_direto": _safe_round(row["total_valor_direto"], 2),
            "pct_truckpag": _safe_round(row["pct_truckpag"], 1),
            "qtd_veiculos": int(row["qtd_veiculos"]),
            "qtd_com_direto": int(row["qtd_com_direto"]),
            "qtd_alertas": int(row["qtd_alertas"]),
        }
        for _, row in df_res.sort_values("total_valor_direto", ascending=False).iterrows()
        if row["filial"] and row["filial"] != "nan"
    ]

    # ── Totais gerais ────────────────────────────────────────────────────────
    total_fkm    = float(merged["valor_comb"].sum())
    total_tp     = float(merged["valor_truckpag"].sum())
    total_direto = float(merged["valor_direto"].sum())

    return {
        "ano_mes": ano_mes,
        "totais": {
            "valor_fkm": _safe_round(total_fkm, 2),
            "valor_truckpag": _safe_round(total_tp, 2),
            "valor_direto": _safe_round(total_direto, 2),
            "pct_truckpag": _safe_round(total_tp / total_fkm * 100, 1) if total_fkm > 0 else 0,
            "qtd_veiculos": len(veiculos),
            "qtd_com_direto": sum(1 for v in veiculos if (v["valor_direto"] or 0) > 100),
            "qtd_alertas": sum(1 for v in veiculos if v["tem_alerta"]),
        },
        "resumo_filiais": resumo_filiais,
        "veiculos": veiculos,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: refresh de cache
# ═══════════════════════════════════════════════════════════════════════════
@router.post("/cache/refresh")
def post_refresh_cache():
    """Força recarregamento do arquivo FKM."""
    return refresh_fkm_cache()
