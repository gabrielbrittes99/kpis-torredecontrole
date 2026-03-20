"""
Módulo de Manutenção — Visão Geral, Operacional e Diretoria

Fontes de dados:
  - FKM (db_fkm): dados agregados por veículo/mês — FILIAL correta, categorias limpas
    Campos: manutencao (03.03), rodas_pneus (03.05), lataria_pintura (03.02),
            total_geral_manutencao = soma das 3 categorias
  - SQL Server (db_sqlserver): detalhes por OS/item — fornecedores, grupos de despesa

Categorias de manutenção:
  "Manutenção"      → fkm.manutencao        (peças + mão de obra 03.03)
  "Pneus"           → fkm.rodas_pneus       (03.05)
  "Lataria/Pintura" → fkm.lataria_pintura   (03.02)
"""
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from db_fkm import get_fkm_df
from db_sqlserver import get_manutencao_df

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/manutencao", tags=["manutencao"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _r(v, n=2):
    try:
        f = float(v)
        return round(f, n) if f != 0 else 0
    except Exception:
        return None


def _fkm_man(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna apenas registros com custo de manutenção > 0."""
    return df[df["total_geral_manutencao"] > 0].copy()


def _apply_fkm_filters(
    df: pd.DataFrame,
    ano_mes: Optional[str] = None,
    filial: Optional[str] = None,
    grupo: Optional[str] = None,
) -> pd.DataFrame:
    df = df.copy()
    if ano_mes:
        df = df[df["ano_mes"] == ano_mes]
    if filial:
        df = df[df["filial"] == filial]
    if grupo:
        df = df[df["grupo_veiculo"] == grupo]
    return df


def _ultimo_mes(df: pd.DataFrame) -> str:
    meses = sorted(df["ano_mes"].dropna().unique().tolist())
    return meses[-1] if meses else ""


def _mes_anterior(df: pd.DataFrame, ano_mes: str) -> str:
    meses = sorted(df["ano_mes"].dropna().unique().tolist())
    idx = meses.index(ano_mes) if ano_mes in meses else -1
    return meses[idx - 1] if idx > 0 else ""


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: filtros disponíveis
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/filtros")
def get_filtros():
    df = get_fkm_df()
    if df.empty:
        return {"meses": [], "filiais": [], "grupos": []}

    df = _fkm_man(df)
    meses   = sorted(df["ano_mes"].dropna().unique().tolist(), reverse=True)
    filiais = sorted([f for f in df["filial"].dropna().unique() if f and f != "nan"])
    grupos  = sorted([g for g in df["grupo_veiculo"].dropna().unique() if g and g != "nan"])

    return {"meses": meses, "filiais": filiais, "grupos": grupos}


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO GERAL — KPIs
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis")
def get_kpis(
    ano_mes: Optional[str] = Query(default=None),
    filial:  Optional[str] = None,
    grupo:   Optional[str] = None,
):
    """KPIs gerais de manutenção do mês: totais, categorias, comparativo vs mês anterior."""
    df_all = _fkm_man(get_fkm_df())
    if df_all.empty:
        return {}

    if not ano_mes:
        ano_mes = _ultimo_mes(df_all)

    df = _apply_fkm_filters(df_all, ano_mes, filial, grupo)
    df_ant = _apply_fkm_filters(df_all, _mes_anterior(df_all, ano_mes), filial, grupo)

    def _totals(d):
        return {
            "total_manutencao":    float(d["manutencao"].sum()),
            "total_pneus":         float(d["rodas_pneus"].sum()),
            "total_lataria":       float(d["lataria_pintura"].sum()),
            "total_geral":         float(d["total_geral_manutencao"].sum()),
            "total_km":            float(d["total_km"].sum()),
            "qtd_veiculos":        int(d["placa"].nunique()),
        }

    cur = _totals(df)
    ant = _totals(df_ant) if not df_ant.empty else None

    tg = cur["total_geral"]
    tk = cur["total_km"]

    def _var(a, b):
        if b and b > 0:
            return _r((a - b) / b * 100, 1)
        return None

    return {
        "ano_mes": ano_mes,
        "total_manutencao":    _r(cur["total_manutencao"]),
        "total_pneus":         _r(cur["total_pneus"]),
        "total_lataria":       _r(cur["total_lataria"]),
        "total_geral":         _r(tg),
        "total_km":            _r(cur["total_km"], 0),
        "qtd_veiculos":        cur["qtd_veiculos"],
        "custo_km":            _r(tg / tk, 4) if tk > 0 else None,
        "custo_veiculo":       _r(tg / cur["qtd_veiculos"]) if cur["qtd_veiculos"] > 0 else None,
        "pct_manutencao":      _r(cur["total_manutencao"] / tg * 100, 1) if tg > 0 else None,
        "pct_pneus":           _r(cur["total_pneus"] / tg * 100, 1) if tg > 0 else None,
        "pct_lataria":         _r(cur["total_lataria"] / tg * 100, 1) if tg > 0 else None,
        # vs mês anterior
        "var_total_pct":       _var(tg, ant["total_geral"]) if ant else None,
        "total_geral_ant":     _r(ant["total_geral"]) if ant else None,
        "ano_mes_ant":         _mes_anterior(df_all, ano_mes),
    }


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO GERAL — Evolução mensal
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/evolucao-mensal")
def get_evolucao_mensal(
    filial: Optional[str] = None,
    grupo:  Optional[str] = None,
):
    """Evolução mensal de manutenção: total + categorias."""
    df = _fkm_man(get_fkm_df())
    df = _apply_fkm_filters(df, None, filial, grupo)
    if df.empty:
        return []

    resultado = []
    for am in sorted(df["ano_mes"].dropna().unique().tolist()):
        g = df[df["ano_mes"] == am]
        tg = float(g["total_geral_manutencao"].sum())
        resultado.append({
            "ano_mes":          am,
            "total_geral":      _r(tg),
            "total_manutencao": _r(float(g["manutencao"].sum())),
            "total_pneus":      _r(float(g["rodas_pneus"].sum())),
            "total_lataria":    _r(float(g["lataria_pintura"].sum())),
            "total_km":         _r(float(g["total_km"].sum()), 0),
            "qtd_veiculos":     int(g["placa"].nunique()),
            "custo_km":         _r(tg / float(g["total_km"].sum()), 4) if g["total_km"].sum() > 0 else None,
        })

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO GERAL — Top veículos (maior gasto de manutenção)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/top-veiculos")
def get_top_veiculos(
    ano_mes: Optional[str] = Query(default=None),
    filial:  Optional[str] = None,
    grupo:   Optional[str] = None,
    limit:   int = Query(default=20, le=100),
):
    df = _fkm_man(get_fkm_df())
    if not ano_mes:
        ano_mes = _ultimo_mes(df)
    df = _apply_fkm_filters(df, ano_mes, filial, grupo)
    if df.empty:
        return []

    resultado = []
    for placa, g in df.groupby("placa"):
        tg  = float(g["total_geral_manutencao"].sum())
        tk  = float(g["total_km"].sum())
        if tg == 0:
            continue
        resultado.append({
            "placa":       placa,
            "modelo":      g["modelo_simplificado"].mode().iloc[0] if not g["modelo_simplificado"].mode().empty else "",
            "grupo":       g["grupo_veiculo"].mode().iloc[0] if not g["grupo_veiculo"].mode().empty else "",
            "filial":      g["filial"].mode().iloc[0] if not g["filial"].mode().empty else "",
            "motorista":   g["motorista_principal"].mode().iloc[0] if not g["motorista_principal"].mode().empty else "",
            "total_geral":      _r(tg),
            "total_manutencao": _r(float(g["manutencao"].sum())),
            "total_pneus":      _r(float(g["rodas_pneus"].sum())),
            "total_lataria":    _r(float(g["lataria_pintura"].sum())),
            "total_km":         _r(tk, 0),
            "custo_km":         _r(tg / tk, 4) if tk > 0 else None,
        })

    resultado.sort(key=lambda x: x["total_geral"], reverse=True)
    return resultado[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO GERAL — Top fornecedores (SQL Server)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/top-fornecedores")
def get_top_fornecedores(
    limit: int = Query(default=15, le=50),
):
    """Top fornecedores por valor total (SQL Server — detalhado)."""
    try:
        df = get_manutencao_df()
        if df.empty:
            return []

        agrupado = (
            df.groupby("Fornecedor", as_index=False)
            .agg(total_valor=("ValorTotal", "sum"), qtd_os=("OrdemServico", "nunique"))
            .sort_values("total_valor", ascending=False)
            .head(limit)
        )

        return [
            {
                "fornecedor": row["Fornecedor"],
                "total_valor": _r(row["total_valor"]),
                "qtd_os": int(row["qtd_os"]),
            }
            for _, row in agrupado.iterrows()
        ]
    except Exception as e:
        logger.warning(f"Manutenção top-fornecedores: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO OPERACIONAL — Por filial
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-filial")
def get_por_filial(
    ano_mes: Optional[str] = Query(default=None),
    grupo:   Optional[str] = None,
):
    """Resumo de manutenção por filial: categorias + custo/km + % do total."""
    df = _fkm_man(get_fkm_df())
    if not ano_mes:
        ano_mes = _ultimo_mes(df)
    df = _apply_fkm_filters(df, ano_mes, None, grupo)
    if df.empty:
        return []

    total_geral_frota = float(df["total_geral_manutencao"].sum())

    resultado = []
    for filial, g in df.groupby("filial"):
        if not filial or filial == "nan":
            continue
        tg  = float(g["total_geral_manutencao"].sum())
        tk  = float(g["total_km"].sum())
        if tg == 0:
            continue
        resultado.append({
            "filial":           filial,
            "total_geral":      _r(tg),
            "total_manutencao": _r(float(g["manutencao"].sum())),
            "total_pneus":      _r(float(g["rodas_pneus"].sum())),
            "total_lataria":    _r(float(g["lataria_pintura"].sum())),
            "total_km":         _r(tk, 0),
            "custo_km":         _r(tg / tk, 4) if tk > 0 else None,
            "pct_total":        _r(tg / total_geral_frota * 100, 1) if total_geral_frota > 0 else 0,
            "qtd_veiculos":     int(g["placa"].nunique()),
        })

    resultado.sort(key=lambda x: x["total_geral"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO OPERACIONAL — Por grupo de veículo
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-grupo")
def get_por_grupo(
    ano_mes: Optional[str] = Query(default=None),
    filial:  Optional[str] = None,
):
    """Custo de manutenção por grupo de veículo (Leve, Médio, Pesado, Caminhão)."""
    df = _fkm_man(get_fkm_df())
    if not ano_mes:
        ano_mes = _ultimo_mes(df)
    df = _apply_fkm_filters(df, ano_mes, filial)
    if df.empty:
        return []

    total_geral = float(df["total_geral_manutencao"].sum())

    resultado = []
    for grupo, g in df.groupby("grupo_veiculo"):
        if not grupo or grupo == "nan":
            continue
        tg = float(g["total_geral_manutencao"].sum())
        tk = float(g["total_km"].sum())
        if tg == 0:
            continue
        resultado.append({
            "grupo":            grupo,
            "total_geral":      _r(tg),
            "total_manutencao": _r(float(g["manutencao"].sum())),
            "total_pneus":      _r(float(g["rodas_pneus"].sum())),
            "total_lataria":    _r(float(g["lataria_pintura"].sum())),
            "total_km":         _r(tk, 0),
            "custo_km":         _r(tg / tk, 4) if tk > 0 else None,
            "pct_total":        _r(tg / total_geral * 100, 1) if total_geral > 0 else 0,
            "qtd_veiculos":     int(g["placa"].nunique()),
        })

    resultado.sort(key=lambda x: x["total_geral"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO DIRETORIA — KPIs estratégicos (últimos N meses)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis-estrategicos")
def get_kpis_estrategicos(
    ano_mes: Optional[str] = Query(default=None),
    filial:  Optional[str] = None,
):
    """
    KPIs estratégicos de manutenção:
    - Total mês atual vs anterior vs média 6 meses
    - Custo manutenção como % do custo total da frota
    - Custo/km de manutenção
    """
    df_all = get_fkm_df()
    if df_all.empty:
        return {}

    df_man = _fkm_man(df_all.copy())
    if not ano_mes:
        ano_mes = _ultimo_mes(df_man)

    meses_disp = sorted(df_man["ano_mes"].dropna().unique().tolist())
    idx = meses_disp.index(ano_mes) if ano_mes in meses_disp else len(meses_disp) - 1

    # Meses para média de 6 meses (excluindo o mês atual)
    meses_6 = meses_disp[max(0, idx - 6):idx]
    mes_ant = meses_disp[idx - 1] if idx > 0 else None

    def _agg(d):
        if d.empty:
            return None
        d = _apply_fkm_filters(d, None, filial)
        return {
            "man":   float(d["total_geral_manutencao"].sum()),
            "comb":  float(d["valor_comb"].sum()),
            "total": float(d["total"].sum()),
            "km":    float(d["total_km"].sum()),
        }

    cur_data = _apply_fkm_filters(df_all[df_all["ano_mes"] == ano_mes], None, filial)
    ant_data = _apply_fkm_filters(df_all[df_all["ano_mes"] == mes_ant], None, filial) if mes_ant else pd.DataFrame()
    m6_data  = _apply_fkm_filters(df_all[df_all["ano_mes"].isin(meses_6)], None, filial)

    cur = _agg(cur_data)
    ant = _agg(ant_data) if not ant_data.empty else None
    m6  = _agg(m6_data)  if not m6_data.empty  else None

    if not cur:
        return {"ano_mes": ano_mes, "sem_dados": True}

    def _var(a, b):
        if b and b > 0:
            return _r((a - b) / b * 100, 1)
        return None

    media_6 = _r(m6["man"] / len(meses_6)) if m6 and meses_6 else None

    return {
        "ano_mes":            ano_mes,
        "total_manutencao":   _r(cur["man"]),
        "custo_km":           _r(cur["man"] / cur["km"], 4) if cur["km"] > 0 else None,
        "pct_custo_frota":    _r(cur["man"] / cur["total"] * 100, 1) if cur["total"] > 0 else None,
        "var_mes_ant_pct":    _var(cur["man"], ant["man"]) if ant else None,
        "total_mes_ant":      _r(ant["man"]) if ant else None,
        "ano_mes_ant":        mes_ant,
        "media_6m":           media_6,
        "var_media_6m_pct":   _var(cur["man"], media_6) if media_6 else None,
        "meses_disponiveis":  len(meses_disp),
    }


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO DIRETORIA — Tendência 12 meses (manutenção + % do total frota)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/tendencia")
def get_tendencia(filial: Optional[str] = None):
    """Histórico mensal com custo manutenção + % do custo total da frota."""
    df = _apply_fkm_filters(get_fkm_df(), None, filial)
    if df.empty:
        return []

    resultado = []
    for am in sorted(df["ano_mes"].dropna().unique().tolist()):
        g = df[df["ano_mes"] == am]
        man   = float(g["total_geral_manutencao"].sum())
        total = float(g["total"].sum())
        km    = float(g["total_km"].sum())
        resultado.append({
            "ano_mes":        am,
            "total_manutencao": _r(man),
            "total_frota":    _r(total),
            "pct_man_frota":  _r(man / total * 100, 1) if total > 0 else None,
            "custo_km_man":   _r(man / km, 4) if km > 0 else None,
            "qtd_veiculos":   int(g["placa"].nunique()),
        })

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# VISÃO DIRETORIA — Ranking filiais por custo manutenção/km (estratégico)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/ranking-filiais-estrategico")
def get_ranking_filiais_estrategico(
    ano_mes: Optional[str] = Query(default=None),
):
    """Ranking estratégico de filiais: custo/km de manutenção + flag vs média."""
    df = _fkm_man(get_fkm_df())
    if not ano_mes:
        ano_mes = _ultimo_mes(df)
    df = _apply_fkm_filters(df, ano_mes)
    if df.empty:
        return []

    resultado = []
    for filial, g in df.groupby("filial"):
        if not filial or filial == "nan":
            continue
        tg = float(g["total_geral_manutencao"].sum())
        tk = float(g["total_km"].sum())
        tf = float(g["total"].sum())
        if tg == 0:
            continue
        resultado.append({
            "filial":        filial,
            "total_geral":   _r(tg),
            "custo_km_man":  _r(tg / tk, 4) if tk > 0 else None,
            "pct_man_frota": _r(tg / tf * 100, 1) if tf > 0 else None,
            "qtd_veiculos":  int(g["placa"].nunique()),
            "total_km":      _r(tk, 0),
        })

    if not resultado:
        return []

    # Calcula média de custo/km para flagging
    ckms = [r["custo_km_man"] for r in resultado if r["custo_km_man"] is not None]
    media_ckm = sum(ckms) / len(ckms) if ckms else None

    for r in resultado:
        if media_ckm and r["custo_km_man"]:
            pct = (r["custo_km_man"] - media_ckm) / media_ckm * 100
            r["pct_vs_media"] = _r(pct, 1)
            r["flag"] = "ALTO" if pct > 15 else ("BAIXO" if pct < -15 else "NORMAL")
        else:
            r["pct_vs_media"] = None
            r["flag"] = "NORMAL"
        r["media_geral_custo_km"] = _r(media_ckm, 4) if media_ckm else None

    resultado.sort(key=lambda x: x["custo_km_man"] or 0, reverse=True)
    return resultado
