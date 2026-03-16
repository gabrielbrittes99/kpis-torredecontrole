"""
Visão Geral — Combustível
Dashboard consolidado com KPIs agrupados por grupo de veículo.
"""
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from config import get_veiculo_group, get_kml_referencia
from data_cache import cache

router = APIRouter(prefix="/api/visao-geral", tags=["visao-geral"])


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _df_periodo(df: pd.DataFrame, mes: int, ano: int) -> pd.DataFrame:
    return df[(df["data_transacao"].dt.month == mes) & (df["data_transacao"].dt.year == ano)]


def _add_grupo(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna grupo_veiculo ao DataFrame (in-place safe, retorna cópia)."""
    df = df.copy()
    df["grupo_veiculo"] = [
        get_veiculo_group(str(m or ""), str(b or ""))
        for m, b in zip(df["modelo_veiculo"], df["marca_veiculo"])
    ]
    return df


def _kml_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada linha com hodômetro válido, calcula km percorrido (diff por placa).
    Retorna df com colunas extras: km_percorrido.
    Usa o df completo para ter a leitura anterior correta, mesmo que o abastecimento
    anterior seja de outro mês.
    """
    hodo = df[df["hodometro"].notna() & (df["hodometro"] > 0)].copy()
    if hodo.empty:
        return hodo

    hodo = hodo.sort_values(["placa", "data_transacao"])
    hodo["km_percorrido"] = hodo.groupby("placa")["hodometro"].diff()
    # filtra km inválidos
    hodo = hodo[(hodo["km_percorrido"] > 0) & (hodo["km_percorrido"] <= 2000)]
    return hodo


# ---------------------------------------------------------------------------
# Endpoint principal
# ---------------------------------------------------------------------------

@router.get("/dashboard")
def get_dashboard(
    mes: Optional[int] = Query(default=None),
    ano: Optional[int] = Query(default=None),
    grupo: Optional[str] = Query(default=None),
    combustivel: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    regiao: Optional[str] = Query(default=None),
    filial: Optional[str] = Query(default=None),
):
    now = datetime.now()
    mes = mes or now.month
    ano = ano or now.year
    
    df_all = _add_grupo(cache.get_df())
    
    # Calcula totais do mês SEM filtro para ancorar as porcentagens
    df_mes_unfiltered = _df_periodo(df_all, mes, ano)
    gasto_total_mes_sem_filtro = float(df_mes_unfiltered["valor"].sum()) or 1
    
    # ── Aplicar filtros dinâmicos ─────────────────────
    if grupo:
        df_all = df_all[df_all["grupo_veiculo"] == grupo]
    if combustivel:
        df_all = df_all[df_all["grupo_combustivel"] == combustivel]
    if estado:
        df_all = df_all[df_all["filial_estado"] == estado]
    if regiao:
        df_all = df_all[df_all["filial_regiao"] == regiao]
    if filial:
        df_all = df_all[df_all["filial_nome"] == filial]

    df_mes = _df_periodo(df_all, mes, ano)

    # ── Hero KPIs ────────────────────────────────────────────────────────────
    gasto_mes    = float(df_mes["valor"].sum())
    litros_mes   = float(df_mes["litragem"].sum())
    total_abs    = int(len(df_mes))
    total_veic   = int(df_mes["placa"].nunique())
    preco_medio  = round(gasto_mes / litros_mes, 4) if litros_mes > 0 else None

    # Variação vs mês anterior
    m_ant = mes - 1 if mes > 1 else 12
    a_ant = ano if mes > 1 else ano - 1
    gasto_ant = float(_df_periodo(df_all, m_ant, a_ant)["valor"].sum())
    var_pct = round((gasto_mes - gasto_ant) / gasto_ant * 100, 1) if gasto_ant > 0 else None

    # km/l e custo/km — calculado sobre o ano corrente com hodômetro
    df_ano = df_all[df_all["data_transacao"].dt.year == ano]
    kml_df  = _kml_table(df_all)            # diffs sobre o df completo
    kml_ano = kml_df[kml_df["data_transacao"].dt.year == ano]

    km_ano    = float(kml_ano["km_percorrido"].sum()) if not kml_ano.empty else 0
    lit_kml   = float(kml_ano["litragem"].sum()) if not kml_ano.empty else 0
    val_kml   = float(kml_ano["valor"].sum()) if not kml_ano.empty else 0
    kml_medio = round(km_ano / lit_kml, 2)   if lit_kml > 0 else None
    custo_km  = round(val_kml / km_ano, 4)   if km_ano  > 0 else None

    hero = {
        "gasto_mes":         round(gasto_mes, 2),
        "gasto_mes_var_pct": var_pct,
        "litros_mes":        round(litros_mes, 1),
        "total_abastecimentos": total_abs,
        "total_veiculos":    total_veic,
        "preco_medio":       preco_medio,
        "kml_medio":         kml_medio,
        "custo_km":          custo_km,
    }

    # ── Gráfico mensal (últimos 12 meses) ────────────────────────────────────
    df_all["ym"] = df_all["data_transacao"].dt.to_period("M")
    ultimos_12 = sorted(df_all["ym"].unique())[-12:]
    grafico_mensal = []
    for p in ultimos_12:
        d = df_all[df_all["ym"] == p]
        grafico_mensal.append({
            "label": p.strftime("%b/%y"),
            "valor": round(float(d["valor"].sum()), 2),
            "litros": round(float(d["litragem"].sum()), 1),
        })

    # ── Gráfico semanal (últimas 8 semanas) ─────────────────────────────────
    df_all["yw"] = df_all["data_transacao"].dt.to_period("W")
    ultimas_8w = sorted(df_all["yw"].unique())[-8:]
    grafico_semanal = []
    for p in ultimas_8w:
        d = df_all[df_all["yw"] == p]
        label = "Sem " + p.start_time.strftime("%d/%m")
        grafico_semanal.append({
            "label": label,
            "valor": round(float(d["valor"].sum()), 2),
            "litros": round(float(d["litragem"].sum()), 1),
        })

    # ── Gráfico diário (últimos 30 dias) ─────────────────────────────────────
    df_all["dia"] = df_all["data_transacao"].dt.date
    ultimos_dias = sorted(df_all["dia"].unique())[-30:]
    grafico_diario = []
    for dia in ultimos_dias:
        d = df_all[df_all["dia"] == dia]
        grafico_diario.append({
            "label": dia.strftime("%d/%m"),
            "valor": round(float(d["valor"].sum()), 2),
            "litros": round(float(d["litragem"].sum()), 1),
        })

    # ── KPIs por grupo de veículo (mês selecionado) ──────────────────────────
    kml_mes_df = kml_df[
        (kml_df["data_transacao"].dt.month == mes) &
        (kml_df["data_transacao"].dt.year  == ano)
    ]

    grupos_data = {}
    for grupo, g in df_mes.groupby("grupo_veiculo"):
        grupos_data[grupo] = {
            "grupo":    grupo,
            "gasto":    round(float(g["valor"].sum()), 2),
            "litros":   round(float(g["litragem"].sum()), 1),
            "veiculos": int(g["placa"].nunique()),
            "abs_count": int(len(g)),
            "kml":      None,
            "custo_km": None,
        }

    # Enriquece com km/l e custo/km do mês onde disponível
    for hp_grupo, gk in kml_mes_df.groupby("grupo_veiculo"):
        km_g  = float(gk["km_percorrido"].sum())
        lit_g = float(gk["litragem"].sum())
        val_g = float(gk["valor"].sum())
        if hp_grupo in grupos_data:
            grupos_data[hp_grupo]["kml"]      = round(km_g / lit_g, 2) if lit_g > 0 else None
            grupos_data[hp_grupo]["custo_km"] = round(val_g / km_g, 4) if km_g  > 0 else None

    # Benchmark de referência: kml esperado pelo combustível predominante do grupo
    for hp_grupo, gd in grupos_data.items():
        df_g = df_mes[df_mes["grupo_veiculo"] == hp_grupo]
        if df_g.empty:
            gd["kml_ref"] = None
            gd["kml_status"] = None
            continue
        # combustível predominante em valor
        comb_pred = df_g.groupby("grupo_combustivel")["valor"].sum().idxmax()
        kml_ref = get_kml_referencia(hp_grupo, comb_pred)
        gd["kml_ref"]          = kml_ref
        gd["combustivel_pred"] = comb_pred
        # status: "ok" ≥ 95% do ref, "alerta" 80-95%, "critico" < 80%, None se sem ref/kml
        if kml_ref and gd["kml"]:
            ratio = gd["kml"] / kml_ref
            gd["kml_status"] = "ok" if ratio >= 0.95 else ("alerta" if ratio >= 0.80 else "critico")
            gd["kml_variacao_pct"] = round((ratio - 1) * 100, 1)
        else:
            gd["kml_status"] = None
            gd["kml_variacao_pct"] = None

    por_grupo = []
    for v in sorted(grupos_data.values(), key=lambda x: -x["gasto"]):
        # A porcentagem é sempre em relação ao total GERAL do mês (sem filtro) 
        # para que o gráfico não preencha 100% à toa quando filtrado por si mesmo
        v["pct_gasto"] = round(v["gasto"] / gasto_total_mes_sem_filtro * 100, 1)
        por_grupo.append(v)

    # ── Mix de combustível (mês) ─────────────────────────────────────────────
    mix = []
    for grp, g in df_mes.groupby("grupo_combustivel"):
        mix.append({
            "grupo":  grp,
            "valor":  round(float(g["valor"].sum()), 2),
            "litros": round(float(g["litragem"].sum()), 1),
            "pct":    round(float(g["valor"].sum()) / gasto_total_mes_sem_filtro * 100, 1),
        })
    mix.sort(key=lambda x: -x["valor"])

    # ── Filiais (mês) ────────────────────────────────────────────────────────
    filiais = []
    for filial, g in df_mes.groupby("filial_nome"):
        if not filial:
            continue
        filiais.append({
            "filial":   filial,
            "estado":   g["filial_estado"].iloc[0] if len(g) else "",
            "regiao":   g["filial_regiao"].iloc[0] if len(g) else "",
            "gasto":    round(float(g["valor"].sum()), 2),
            "litros":   round(float(g["litragem"].sum()), 1),
            "veiculos": int(g["placa"].nunique()),
        })
    filiais.sort(key=lambda x: -x["gasto"])

    sem_filial = df_mes[df_mes["filial_nome"] == ""]
    if not sem_filial.empty:
        filiais.append({
            "filial":   "Sem filial identificada",
            "estado":   "",
            "regiao":   "",
            "gasto":    round(float(sem_filial["valor"].sum()), 2),
            "litros":   round(float(sem_filial["litragem"].sum()), 1),
            "veiculos": int(sem_filial["placa"].nunique()),
        })

    return {
        "mes":           mes,
        "ano":           ano,
        "hero":          hero,
        "grafico_mensal":  grafico_mensal,
        "grafico_semanal": grafico_semanal,
        "grafico_diario":  grafico_diario,
        "por_grupo_veiculo": por_grupo,
        "mix_combustivel":   mix,
        "filiais":           filiais,
    }


# ---------------------------------------------------------------------------
# Filtros Globais Dinâmicos
# ---------------------------------------------------------------------------

@router.get("/filtros-disponiveis")
def get_filtros_disponiveis():
    """Retorna listas únicas para os dropdowns de filtro no frontend."""
    df_all = _add_grupo(cache.get_df())
        
    def get_unique(col):
        if col not in df_all.columns: return []
        items = df_all[col].dropna().unique().tolist()
        return sorted([str(i) for i in items if str(i).strip()])

    return {
        "status": "success",
        "estados": get_unique("filial_estado"),
        "regioes": get_unique("filial_regiao"),
        "filiais": get_unique("filial_nome"),
        "grupos_veiculo": get_unique("grupo_veiculo"),
        "combustiveis": get_unique("grupo_combustivel")
    }
