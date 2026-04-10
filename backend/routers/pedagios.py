import logging
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Query

from data_cache import cache
from utils import safe_round, apply_time_filters, apply_attribute_filters

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pedagios", tags=["pedagios"])


def get_pedagios_df():
    return cache.get_df("pedagios")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Filtros Disponíveis
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/filtros")
def get_filtros():
    df = get_pedagios_df()
    if df.empty:
        return {"filiais": [], "grupos": [], "placas": []}
    return {
        "filiais": sorted([f for f in df["filial_nome"].dropna().unique() if f]),
        "grupos":  sorted([g for g in df["grupo_veiculo"].dropna().unique() if g]),
        "placas":  sorted([p for p in df["placa"].dropna().unique() if p]),
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: KPIs de Pedágio
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/visao-geral")
def get_visao_geral(
    modo_tempo:  str = Query(default="mes"),
    ano:         Optional[int] = None,
    mes:         Optional[int] = None,
    bimestre:    Optional[int] = None,
    semestre:    Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim:    Optional[str] = None,
    filial:      Optional[str] = None,
    grupo:       Optional[str] = None,
    estado:      Optional[str] = None,
    regiao:      Optional[str] = None,
    placa:       Optional[str] = None,
):
    df = get_pedagios_df()
    df = apply_time_filters(df, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim)
    df = apply_attribute_filters(df, grupo=grupo, filial=filial, estado=estado, regiao=regiao)

    if placa:
        df = df[df["placa"] == placa]

    if df.empty:
        return {"total_gasto": 0, "qtd_passagens": 0, "ticket_medio": 0, "max_passagem": 0}

    total_gasto   = float(df["valor"].sum())
    qtd_passagens = len(df)
    ticket_medio  = safe_round(total_gasto / qtd_passagens, 2) if qtd_passagens > 0 else 0

    return {
        "total_gasto":   safe_round(total_gasto, 2),
        "qtd_passagens": qtd_passagens,
        "ticket_medio":  ticket_medio,
        "max_passagem":  safe_round(float(df["valor"].max()), 2),
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Gasto por Filial
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-filial")
def get_por_filial(
    modo_tempo:  str = Query(default="mes"),
    ano:         Optional[int] = None,
    mes:         Optional[int] = None,
    bimestre:    Optional[int] = None,
    semestre:    Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim:    Optional[str] = None,
    grupo:       Optional[str] = None,
    estado:      Optional[str] = None,
    regiao:      Optional[str] = None,
):
    df = get_pedagios_df()
    df = apply_time_filters(df, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim)
    df = apply_attribute_filters(df, grupo=grupo, estado=estado, regiao=regiao)

    if df.empty:
        return []

    resumo = df.groupby("filial_nome").agg(
        total_gasto=("valor", "sum"),
        qtd_passagens=("valor", "count"),
    ).reset_index().rename(columns={"filial_nome": "filial"})

    resumo["ticket_medio"] = (resumo["total_gasto"] / resumo["qtd_passagens"]).round(2)
    resumo = resumo.sort_values("total_gasto", ascending=False)
    return resumo.to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Gasto por Grupo de Veículo
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-grupo")
def get_por_grupo(
    modo_tempo:  str = Query(default="mes"),
    ano:         Optional[int] = None,
    mes:         Optional[int] = None,
    bimestre:    Optional[int] = None,
    semestre:    Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim:    Optional[str] = None,
    filial:      Optional[str] = None,
    estado:      Optional[str] = None,
    regiao:      Optional[str] = None,
):
    df = get_pedagios_df()
    df = apply_time_filters(df, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim)
    df = apply_attribute_filters(df, filial=filial, estado=estado, regiao=regiao)

    if df.empty:
        return []

    resumo = df.groupby("grupo_veiculo").agg(
        total_gasto=("valor", "sum"),
        qtd_passagens=("valor", "count"),
        qtd_veiculos=("placa", "nunique"),
    ).reset_index().rename(columns={"grupo_veiculo": "grupo"})

    resumo["ticket_medio"] = (resumo["total_gasto"] / resumo["qtd_passagens"]).round(2)
    resumo = resumo.sort_values("total_gasto", ascending=False)
    return resumo.to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Ranking de Veículos
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/ranking-veiculos")
def get_ranking_veiculos(
    modo_tempo:  str = Query(default="mes"),
    ano:         Optional[int] = None,
    mes:         Optional[int] = None,
    bimestre:    Optional[int] = None,
    semestre:    Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim:    Optional[str] = None,
    filial:      Optional[str] = None,
    grupo:       Optional[str] = None,
    estado:      Optional[str] = None,
    regiao:      Optional[str] = None,
    limit:       int = Query(default=10),
):
    df = get_pedagios_df()
    df = apply_time_filters(df, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim)
    df = apply_attribute_filters(df, grupo=grupo, filial=filial, estado=estado, regiao=regiao)

    if df.empty:
        return []

    resumo = df.groupby("placa").agg(
        total_gasto=("valor", "sum"),
        qtd_passagens=("valor", "count"),
    ).reset_index()

    resumo["ticket_medio"] = (resumo["total_gasto"] / resumo["qtd_passagens"]).round(2)
    resumo = resumo.sort_values("total_gasto", ascending=False).head(limit)
    return resumo.to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Evolução Mensal
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/historico-mensal")
def get_historico_mensal(
    filial:  Optional[str] = None,
    grupo:   Optional[str] = None,
    estado:  Optional[str] = None,
    regiao:  Optional[str] = None,
):
    df = get_pedagios_df()
    df = apply_attribute_filters(df, grupo=grupo, filial=filial, estado=estado, regiao=regiao)

    if df.empty:
        return []

    df = df.copy()
    df["ano_mes"] = df["data_transacao"].dt.strftime("%Y-%m")
    evolucao = df.groupby("ano_mes").agg(
        total_gasto=("valor", "sum"),
        qtd_passagens=("valor", "count"),
    ).reset_index().sort_values("ano_mes")

    return evolucao.to_dict(orient="records")
