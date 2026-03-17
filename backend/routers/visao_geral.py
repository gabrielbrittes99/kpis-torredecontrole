"""
Visão Geral — Combustível
Dashboard consolidado com KPIs agrupados por grupo de veículo.
"""
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from config import get_kml_referencia
from data_cache import cache

router = APIRouter(prefix="/api/visao-geral", tags=["visao-geral"])


def _apply_filters(
    df: pd.DataFrame,
    modo_tempo: str = "mes",
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    grupo: Optional[str] = None,
    combustivel: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
    filial: Optional[str] = None,
) -> pd.DataFrame:
    df = df.copy()
    
    # 1. Filtros Temporais
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
    elif ano:
        df = df[df["data_transacao"].dt.year == ano]

    # 2. Filtros de Atributo
    if grupo:
        df = df[df["grupo_veiculo"] == grupo]
    if combustivel:
        df = df[df["grupo_combustivel"] == combustivel]
    if estado:
        df = df[df["filial_estado"] == estado]
    if regiao:
        df = df[df["filial_regiao"] == regiao]
    if filial:
        df = df[df["filial_nome"] == filial]
                
    return df


# ---------------------------------------------------------------------------
@router.get("/dashboard")
def get_dashboard(
    modo_tempo: str = Query(default="mes"),
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    grupo: Optional[str] = None,
    combustivel: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
    filial: Optional[str] = None,
):
    now = datetime.now()
    mes = mes or now.month
    ano = ano or now.year
    
    df_all = cache.get_df()
    
    # Identifica se é o mês atual p/ MTD comparison (apenas no modo 'mes')
    is_current_month = (modo_tempo == "mes" and mes == now.month and ano == now.year)
    trend_label = "mesmo período" if is_current_month else "período anterior"
    
    # Filtros para o período atual
    df_periodo = _apply_filters(df_all, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim, 
                                grupo, combustivel, estado, regiao, filial)

    # Gasto Total sem filtros de atributo (para mix e por_grupo)
    df_periodo_unfiltered = _apply_filters(df_all, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim)
    gasto_total_periodo_sem_filtro = float(df_periodo_unfiltered["valor"].sum()) or 1

    # ── Hero KPIs ────────────────────────────────────────────────────────────
    gasto_mes    = float(df_periodo["valor"].sum())
    litros_mes   = float(df_periodo["litragem"].sum())
    total_abs    = int(len(df_periodo))
    total_veic   = int(df_periodo["placa"].nunique())
    preco_medio  = round(gasto_mes / litros_mes, 4) if litros_mes > 0 else None

    # Variação vs período anterior
    # Simplificação: Para meses, usa M-1. Para outros modos, compara com o mesmo período do ano anterior (ou apenas o ano anterior completo)
    # Aqui vamos manter a lógica de mês para compatibilidade se modo_tempo for 'mes'
    gasto_ant = None
    if modo_tempo == "mes":
        m_ant = mes - 1 if mes > 1 else 12
        a_ant = ano if mes > 1 else ano - 1
        df_ant = _apply_filters(df_all, "mes", a_ant, m_ant, None, None, None, None, grupo, combustivel, estado, regiao, filial)
        if is_current_month:
            df_ant = df_ant[df_ant["data_transacao"].dt.day <= now.day]
        gasto_ant = float(df_ant["valor"].sum())
    elif modo_tempo == "ano":
        df_ant = _apply_filters(df_all, "ano", ano - 1, None, None, None, None, None, grupo, combustivel, estado, regiao, filial)
        gasto_ant = float(df_ant["valor"].sum())

    var_pct = round((gasto_mes - gasto_ant) / gasto_ant * 100, 1) if gasto_ant and gasto_ant > 0 else None

    # km/l e custo/km — calculado sobre o período filtrado com hodômetro
    kml_df = cache.get_kml_df()
    kml_periodo = _apply_filters(kml_df, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim, 
                                 grupo, combustivel, estado, regiao, filial)

    km_val    = float(kml_periodo["km_percorrido"].sum()) if not kml_periodo.empty else 0
    lit_kml   = float(kml_periodo["litragem"].sum()) if not kml_periodo.empty else 0
    val_kml   = float(kml_periodo["valor"].sum()) if not kml_periodo.empty else 0
    kml_medio = round(km_val / lit_kml, 2)   if lit_kml > 0 else None
    custo_km  = round(val_kml / km_val, 4)   if km_val  > 0 else None

    hero = {
        "gasto_mes":         round(gasto_mes, 2),
        "gasto_mes_var_pct": var_pct,
        "trend_label":       trend_label,
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
    for grupo, g in df_periodo.groupby("grupo_veiculo"):
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
        df_g = df_periodo[df_periodo["grupo_veiculo"] == hp_grupo]
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
    # Ordenar por nome (alfabética) em vez de gasto
    for v in sorted(grupos_data.values(), key=lambda x: str(x["grupo"]).lower()):
        # A porcentagem é sempre em relação ao total GERAL do mês (sem filtro) 
        # para que o gráfico não preencha 100% à toa quando filtrado por si mesmo
        v["pct_gasto"] = round(v["gasto"] / gasto_total_periodo_sem_filtro * 100, 1)
        por_grupo.append(v)

    # ── Mix de combustível (mês) ─────────────────────────────────────────────
    mix = []
    for grp, g in df_periodo.groupby("grupo_combustivel"):
        mix.append({
            "grupo":  grp,
            "valor":  round(float(g["valor"].sum()), 2),
            "litros": round(float(g["litragem"].sum()), 1),
            "pct":    round(float(g["valor"].sum()) / gasto_total_periodo_sem_filtro * 100, 1),
        })
    # Ordenar por nome (alfabética)
    mix.sort(key=lambda x: str(x["grupo"]).lower())

    # ── Filiais (mês) ────────────────────────────────────────────────────────
    filiais = []
    for filial, g in df_periodo.groupby("filial_nome"):
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
    # Ordenar por nome (alfabética)
    filiais.sort(key=lambda x: str(x["filial"]).lower())

    sem_filial = df_periodo[df_periodo["filial_nome"] == ""]
    if not sem_filial.empty:
        filiais.append({
            "filial":   "Sem filial identificada",
            "estado":   "",
            "regiao":   "",
            "gasto":    round(float(sem_filial["valor"].sum()), 2),
            "litros":   round(float(sem_filial["litragem"].sum()), 1),
            "veiculos": int(sem_filial["placa"].nunique()),
            "placas_pendentes": sem_filial["placa"].unique().tolist(),
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
    df_all = cache.get_df()
        
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
