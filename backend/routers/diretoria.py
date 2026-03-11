"""
Seção 4 — Visão da Diretoria
KPIs estratégicos, projeção anual, potencial de economia e benchmarks ANP.
"""
import calendar
from datetime import datetime
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Query

from data_cache import cache

router = APIRouter(prefix="/api/diretoria", tags=["diretoria"])


# ---------------------------------------------------------------------------
# KPIs estratégicos
# ---------------------------------------------------------------------------

@router.get("/kpis-estrategicos")
def get_kpis_estrategicos():
    """
    KPIs de alto nível para a diretoria:
    - Gasto acumulado no ano
    - Projeção anual
    - Mês com maior gasto
    - Diesel vs outros combustíveis
    - Top 5 veículos mais caros
    """
    df = cache.get_df()
    if df.empty:
        return {}

    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month

    df_ano = df[df["data_transacao"].dt.year == ano_atual].copy()

    # Gasto acumulado no ano
    gasto_ano = round(float(df_ano["valor"].sum()), 2)
    litros_ano = round(float(df_ano["litragem"].sum()), 0)

    # Projeção anual (baseada na média mensal dos meses completos)
    meses_completos = mes_atual - 1  # Meses já fechados
    if meses_completos > 0:
        df_meses_completos = df_ano[df_ano["data_transacao"].dt.month < mes_atual]
        media_mensal = float(df_meses_completos["valor"].sum()) / meses_completos
    else:
        media_mensal = gasto_ano  # Só o mês atual

    projecao_anual = round(media_mensal * 12, 2)

    # Mês com maior gasto no ano
    if not df_ano.empty:
        mensal = df_ano.groupby(df_ano["data_transacao"].dt.month)["valor"].sum()
        mes_pico = int(mensal.idxmax())
        valor_pico = round(float(mensal.max()), 2)
    else:
        mes_pico = 0
        valor_pico = 0

    # Diesel vs outros
    DIESEL_KEYWORDS = ["diesel", "s10", "s-10"]
    df_ano_copy = df_ano.copy()
    df_ano_copy["eh_diesel"] = df_ano_copy["nome_combustivel"].str.lower().apply(
        lambda n: any(k in n for k in DIESEL_KEYWORDS)
    )
    gasto_diesel = round(float(df_ano_copy[df_ano_copy["eh_diesel"]]["valor"].sum()), 2)
    gasto_outros = round(float(df_ano_copy[~df_ano_copy["eh_diesel"]]["valor"].sum()), 2)
    pct_diesel = round(gasto_diesel / gasto_ano * 100, 1) if gasto_ano > 0 else 0

    # Top 5 veículos mais caros (todos os dados, não só ano atual)
    df_todos = df.copy()
    top_veiculos = (
        df_todos.groupby("placa")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
            modelo=("modelo_veiculo", lambda x: x.mode().iloc[0] if not x.mode().empty else ""),
        )
        .reset_index()
        .sort_values("total_valor", ascending=False)
        .head(5)
    )
    top5 = [
        {
            "placa": row["placa"],
            "modelo": row["modelo"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 0),
            "qtd_abastecimentos": int(row["qtd"]),
        }
        for _, row in top_veiculos.iterrows()
    ]

    # Veículos ativos no mês atual
    veiculos_mes_atual = int(df_ano[df_ano["data_transacao"].dt.month == mes_atual]["placa"].nunique())

    return {
        "ano_atual": ano_atual,
        "gasto_ano": gasto_ano,
        "litros_ano": litros_ano,
        "media_mensal": round(media_mensal, 2),
        "projecao_anual": projecao_anual,
        "mes_pico": mes_pico,
        "valor_pico": valor_pico,
        "gasto_diesel": gasto_diesel,
        "gasto_outros": gasto_outros,
        "pct_diesel": pct_diesel,
        "top5_veiculos": top5,
        "veiculos_ativos_mes": veiculos_mes_atual,
        "meses_completos": meses_completos,
    }


# ---------------------------------------------------------------------------
# Tendência mensal (12 meses)
# ---------------------------------------------------------------------------

@router.get("/tendencia-12-meses")
def get_tendencia_12_meses():
    """Últimos 12 meses de custo total, litros e preço médio."""
    df = cache.get_df()
    if df.empty:
        return []

    df = df.copy()
    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    agg = (
        df.groupby("ano_mes")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd_veiculos=("placa", "nunique"),
            qtd_abastecimentos=("valor", "count"),
        )
        .reset_index()
        .sort_values("ano_mes")
        .tail(12)
    )
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)

    # Variação mês a mês
    agg["variacao_valor"] = agg["total_valor"].diff().round(2)
    agg["variacao_pct"] = (agg["total_valor"].pct_change() * 100).round(2)

    return [
        {
            "ano_mes": row["ano_mes"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 0),
            "preco_medio": float(row["preco_medio"]),
            "qtd_veiculos": int(row["qtd_veiculos"]),
            "qtd_abastecimentos": int(row["qtd_abastecimentos"]),
            "variacao_valor": float(row["variacao_valor"]) if pd.notna(row["variacao_valor"]) else None,
            "variacao_pct": float(row["variacao_pct"]) if pd.notna(row["variacao_pct"]) else None,
        }
        for _, row in agg.iterrows()
    ]


# ---------------------------------------------------------------------------
# Potencial de economia
# ---------------------------------------------------------------------------

@router.get("/potencial-economia")
def get_potencial_economia():
    """
    Calcula o potencial de economia se todos os abastecimentos
    fossem feitos no posto mais barato de cada UF por tipo de combustível.
    """
    df = cache.get_df().copy()
    if df.empty:
        return {"economia_potencial": 0, "economia_pct": 0, "por_uf": []}

    df = df[df["uf_posto"] != ""].copy()
    df["preco_litro"] = df["valor"] / df["litragem"]

    # Preço mínimo por UF e tipo de combustível
    minimos = (
        df.groupby(["uf_posto", "nome_combustivel"])["preco_litro"]
        .min()
        .reset_index()
        .rename(columns={"preco_litro": "preco_minimo"})
    )

    df_join = df.merge(minimos, on=["uf_posto", "nome_combustivel"])
    df_join["valor_minimo"] = df_join["litragem"] * df_join["preco_minimo"]
    df_join["economia"] = df_join["valor"] - df_join["valor_minimo"]

    total_gasto = float(df_join["valor"].sum())
    economia_total = round(float(df_join["economia"].sum()), 2)
    economia_pct = round(economia_total / total_gasto * 100, 1) if total_gasto > 0 else 0

    por_uf = (
        df_join.groupby("uf_posto")
        .agg(
            economia=("economia", "sum"),
            total_gasto=("valor", "sum"),
        )
        .reset_index()
        .sort_values("economia", ascending=False)
    )
    por_uf["economia_pct"] = (por_uf["economia"] / por_uf["total_gasto"] * 100).round(1)

    return {
        "economia_potencial": economia_total,
        "economia_pct": economia_pct,
        "total_gasto": round(total_gasto, 2),
        "por_uf": [
            {
                "uf": row["uf_posto"],
                "economia": round(float(row["economia"]), 2),
                "total_gasto": round(float(row["total_gasto"]), 2),
                "economia_pct": float(row["economia_pct"]),
            }
            for _, row in por_uf.iterrows()
        ],
    }


# ---------------------------------------------------------------------------
# Distribuição por tipo de combustível (todos os dados)
# ---------------------------------------------------------------------------

@router.get("/mix-combustiveis")
def get_mix_combustiveis():
    """Distribuição de gasto por tipo de combustível (histórico completo)."""
    df = cache.get_df()
    if df.empty:
        return []

    total_valor = float(df["valor"].sum())

    agg = (
        df.groupby("nome_combustivel")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
        )
        .reset_index()
        .sort_values("total_valor", ascending=False)
    )

    return [
        {
            "combustivel": row["nome_combustivel"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 0),
            "qtd_abastecimentos": int(row["qtd"]),
            "pct_valor": round(float(row["total_valor"]) / total_valor * 100, 1) if total_valor > 0 else 0,
        }
        for _, row in agg.iterrows()
    ]


# ---------------------------------------------------------------------------
# Resumo comparativo mês atual vs mês anterior
# ---------------------------------------------------------------------------

@router.get("/comparativo-meses")
def get_comparativo_meses():
    """Comparação detalhada entre mês atual e mês anterior."""
    df = cache.get_df()
    if df.empty:
        return {}

    ultima_data = df["data_transacao"].max()
    mes_atual = int(ultima_data.month)
    ano_atual = int(ultima_data.year)
    data_ant = ultima_data - relativedelta(months=1)

    def resumo_mes(m, a):
        sub = df[(df["data_transacao"].dt.month == m) & (df["data_transacao"].dt.year == a)]
        if sub.empty:
            return None
        litros = float(sub["litragem"].sum())
        valor = float(sub["valor"].sum())
        return {
            "mes": m,
            "ano": a,
            "total_valor": round(valor, 2),
            "total_litros": round(litros, 0),
            "preco_medio": round(valor / litros, 4) if litros > 0 else 0,
            "qtd_abastecimentos": int(len(sub)),
            "qtd_veiculos": int(sub["placa"].nunique()),
            "dias_com_dados": int(sub["data_transacao"].dt.date.nunique()),
        }

    atual = resumo_mes(mes_atual, ano_atual)
    anterior = resumo_mes(data_ant.month, data_ant.year)

    variacao = {}
    if atual and anterior and anterior["total_valor"] > 0:
        variacao = {
            "valor_abs": round(atual["total_valor"] - anterior["total_valor"], 2),
            "valor_pct": round((atual["total_valor"] - anterior["total_valor"]) / anterior["total_valor"] * 100, 1),
            "litros_abs": round(atual["total_litros"] - anterior["total_litros"], 0),
            "preco_abs": round(atual["preco_medio"] - anterior["preco_medio"], 4),
        }

    return {
        "mes_atual": atual,
        "mes_anterior": anterior,
        "variacao": variacao,
    }
