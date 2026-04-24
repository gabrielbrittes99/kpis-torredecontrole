"""
Visão Geral — Combustível
Dashboard consolidado com KPIs agrupados por grupo de veículo.
"""
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from config import get_kml_referencia
from data_cache import cache
from db_dw import get_dw_engine

router = APIRouter(prefix="/api/visao-geral", tags=["visao-geral"])


# ── KM/L e Custo/km do FKM Reconciliado ─────────────────────────────────────

def _kml_from_fkm(ano_mes: str, grupo: Optional[str] = None, filial: Optional[str] = None):
    """
    Busca km/L e custo/km consolidados da tabela torre.fkm_reconciliacao.
    Usa litros_efetivo (corrigido pelo TruckPag quando FKM estava abaixo).
    Retorna None quando o mês ainda não foi processado pelo ETL.
    """
    try:
        engine = get_dw_engine()
        where_parts = ["ano_mes = :ano_mes", "litros_efetivo > 0", "total_km > 0"]
        params = {"ano_mes": ano_mes}
        if grupo:
            where_parts.append("grupo_veiculo = :grupo")
            params["grupo"] = grupo
        if filial:
            where_parts.append("filial = :filial")
            params["filial"] = filial

        where = " AND ".join(where_parts)
        sql = f"""
            SELECT
                SUM(total_km)        AS total_km,
                SUM(litros_efetivo)  AS total_litros,
                SUM(valor_efetivo)   AS total_valor
            FROM torre.fkm_reconciliacao
            WHERE {where}
        """
        from sqlalchemy import text
        with engine.connect() as conn:
            row = conn.execute(text(sql), params).fetchone()

        if row and row.total_km and row.total_litros:
            km   = float(row.total_km)
            lit  = float(row.total_litros)
            val  = float(row.total_valor or 0)
            return {
                "kml_medio": round(km / lit, 2),
                "custo_km":  round(val / km, 2) if km > 0 else None,
                "fonte":     "fkm_reconciliado",
            }
    except Exception:
        pass
    return None


# ── Feriados Nacionais Brasileiros ───────────────────────────────────────────
def _easter(year: int) -> date:
    """Algoritmo de Butcher para Páscoa."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(114 + h + l - 7 * m, 31)
    return date(year, month, day + 1)


def _feriados_ano(year: int) -> set:
    easter = _easter(year)
    moveis = {
        easter - timedelta(days=48),  # Carnaval (segunda)
        easter - timedelta(days=47),  # Carnaval (terça)
        easter - timedelta(days=2),   # Sexta-feira Santa
        easter,                        # Páscoa
        easter + timedelta(days=60),  # Corpus Christi
    }
    fixos = {
        date(year, 1, 1),   # Ano Novo
        date(year, 4, 21),  # Tiradentes
        date(year, 5, 1),   # Dia do Trabalho
        date(year, 9, 7),   # Independência
        date(year, 10, 12), # Nossa Senhora Aparecida
        date(year, 11, 2),  # Finados
        date(year, 11, 15), # Proclamação da República
        date(year, 11, 20), # Consciência Negra
        date(year, 12, 25), # Natal
    }
    return moveis | fixos


_FERIADOS_CACHE: dict = {}


def _is_feriado(d: date) -> bool:
    if d.year not in _FERIADOS_CACHE:
        _FERIADOS_CACHE[d.year] = _feriados_ano(d.year)
    return d in _FERIADOS_CACHE[d.year]


def _tipo_dia(d: date) -> str:
    """Classifica o dia: 'feriado', 'fds' ou 'util'."""
    if _is_feriado(d):
        return "feriado"
    if d.weekday() >= 5:  # 5=Sáb, 6=Dom
        return "fds"
    return "util"


def _contar_dias_uteis(ano: int, mes: int) -> int:
    """Retorna a quantidade de dias úteis (exclui FDS e feriados) no mês/ano dado."""
    from calendar import monthrange
    _, ultimo = monthrange(ano, mes)
    return sum(1 for d in range(1, ultimo + 1) if _tipo_dia(date(ano, mes, d)) == "util")


_MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _mes_label(ano: int, mes: int) -> str:
    return f"{_MESES_PT[mes - 1]}/{ano}"


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
    mes_ref: Optional[int] = None,
    ano_ref: Optional[int] = None,
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
    preco_medio  = round(gasto_mes / litros_mes, 2) if litros_mes > 0 else None

    # Variação vs período anterior — suporta todos os modos de tempo
    df_ant = None
    mes_ref_usado: Optional[int] = None
    ano_ref_usado: Optional[int] = None
    if modo_tempo == "mes":
        # Default: mês imediatamente anterior
        m_ant = mes - 1 if mes > 1 else 12
        a_ant = ano if mes > 1 else ano - 1
        # Override via mes_ref/ano_ref — apenas se for estritamente anterior ao período atual
        if mes_ref and ano_ref and (ano_ref, mes_ref) < (ano, mes):
            m_ant, a_ant = mes_ref, ano_ref
        mes_ref_usado, ano_ref_usado = m_ant, a_ant
        df_ant = _apply_filters(df_all, "mes", a_ant, m_ant, None, None, None, None, grupo, combustivel, estado, regiao, filial)
        if is_current_month and (mes_ref_usado == (mes - 1 if mes > 1 else 12)):
            # só aplica recorte MTD quando comparando com o mês anterior imediato
            df_ant = df_ant[df_ant["data_transacao"].dt.day <= now.day]
    elif modo_tempo == "bimestre":
        b_ant = bimestre - 1 if bimestre and bimestre > 1 else 6
        a_ant = ano if (bimestre and bimestre > 1) else ano - 1
        df_ant = _apply_filters(df_all, "bimestre", a_ant, None, b_ant, None, None, None, grupo, combustivel, estado, regiao, filial)
    elif modo_tempo == "semestre":
        s_ant = semestre - 1 if semestre and semestre > 1 else 2
        a_ant = ano if (semestre and semestre > 1) else ano - 1
        df_ant = _apply_filters(df_all, "semestre", a_ant, None, None, s_ant, None, None, grupo, combustivel, estado, regiao, filial)
    elif modo_tempo == "ano":
        df_ant = _apply_filters(df_all, "ano", ano - 1, None, None, None, None, None, grupo, combustivel, estado, regiao, filial)

    gasto_ant   = float(df_ant["valor"].sum())   if df_ant is not None else None
    litros_ant  = float(df_ant["litragem"].sum()) if df_ant is not None else None
    abs_ant     = int(len(df_ant))               if df_ant is not None else None
    preco_ant   = round(gasto_ant / litros_ant, 2) if (litros_ant and litros_ant > 0 and gasto_ant is not None) else None

    def _var(atual, anterior):
        if atual is None or not anterior or anterior <= 0:
            return None
        return round((atual - anterior) / anterior * 100, 1)

    var_pct          = _var(gasto_mes, gasto_ant)
    litros_var_pct   = _var(litros_mes, litros_ant)
    abs_var_pct      = _var(float(total_abs), float(abs_ant) if abs_ant is not None else None)
    preco_medio_var_pct = _var(preco_medio, preco_ant)

    # km/L e custo/km — prioriza FKM reconciliado (mês fechado), cai no TruckPag se não tiver
    kml_df = cache.get_kml_df()
    kml_periodo = _apply_filters(kml_df, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim,
                                 grupo, combustivel, estado, regiao, filial)

    km_val    = float(kml_periodo["km_percorrido"].sum()) if not kml_periodo.empty else 0
    lit_kml   = float(kml_periodo["litragem"].sum()) if not kml_periodo.empty else 0
    val_kml   = float(kml_periodo["valor"].sum()) if not kml_periodo.empty else 0
    kml_medio_tp = round(km_val / lit_kml, 2) if lit_kml > 0 else None
    custo_km_tp  = round(val_kml / km_val, 2) if km_val  > 0 else None

    kml_medio  = kml_medio_tp
    custo_km   = custo_km_tp
    kml_fonte  = "truckpag"

    # Usa FKM reconciliado somente para modo mês sem filtros de combustível/estado/região
    # (FKM é agregado mensal — não tem granularidade para outros recortes temporais)
    if modo_tempo == "mes" and not combustivel and not estado and not regiao:
        ano_mes_str = f"{ano:04d}-{mes:02d}"
        fkm_kml = _kml_from_fkm(ano_mes_str, grupo=grupo, filial=filial)
        if fkm_kml:
            kml_medio = fkm_kml["kml_medio"]
            custo_km  = fkm_kml["custo_km"]
            kml_fonte = fkm_kml["fonte"]

    # ── Deltas absolutos + rótulos de período ───────────────────────────────
    gasto_delta_abs  = round(gasto_mes - gasto_ant, 2) if gasto_ant is not None else None
    litros_delta_abs = round(litros_mes - litros_ant, 1) if litros_ant is not None else None
    preco_delta_abs  = round(preco_medio - preco_ant, 3) if (preco_medio is not None and preco_ant is not None) else None

    dias_uteis_periodo = _contar_dias_uteis(ano, mes) if modo_tempo == "mes" else None
    dias_uteis_ref = _contar_dias_uteis(ano_ref_usado, mes_ref_usado) \
        if (modo_tempo == "mes" and mes_ref_usado and ano_ref_usado) else None

    periodo_label = _mes_label(ano, mes) if modo_tempo == "mes" else None
    mes_ref_label = _mes_label(ano_ref_usado, mes_ref_usado) \
        if (modo_tempo == "mes" and mes_ref_usado and ano_ref_usado) else None

    # ── Breakdown por combustível no hero (atual + referência) ──────────────
    def _agg_por_combustivel(df_base: Optional[pd.DataFrame]) -> dict:
        if df_base is None or df_base.empty:
            return {}
        out: dict = {}
        for comb, g in df_base.groupby("grupo_combustivel"):
            lit = float(g["litragem"].sum())
            val = float(g["valor"].sum())
            out[str(comb)] = {
                "litros": round(lit, 1),
                "valor":  round(val, 2),
                "preco_medio": round(val / lit, 3) if lit > 0 else None,
            }
        return out

    atual_por_comb = _agg_por_combustivel(df_periodo)
    ref_por_comb   = _agg_por_combustivel(df_ant)
    combs_ordenados = sorted(atual_por_comb.keys(), key=lambda c: atual_por_comb[c]["valor"], reverse=True)
    por_combustivel = []
    for comb in combs_ordenados:
        a = atual_por_comb[comb]
        r = ref_por_comb.get(comb, {})
        por_combustivel.append({
            "grupo":            comb,
            "litros":           a["litros"],
            "valor":            a["valor"],
            "preco_medio":      a["preco_medio"],
            "litros_ref":       r.get("litros"),
            "valor_ref":        r.get("valor"),
            "preco_medio_ref":  r.get("preco_medio"),
        })

    hero = {
        "gasto_mes":              round(gasto_mes, 2),
        "gasto_mes_var_pct":      var_pct,
        "gasto_mes_delta_abs":    gasto_delta_abs,
        "gasto_ant":              round(gasto_ant, 2) if gasto_ant is not None else None,
        "litros_mes":             round(litros_mes, 1),
        "litros_mes_var_pct":     litros_var_pct,
        "litros_mes_delta_abs":   litros_delta_abs,
        "litros_ant":             round(litros_ant, 1) if litros_ant is not None else None,
        "total_abastecimentos":   total_abs,
        "abastecimentos_var_pct": abs_var_pct,
        "total_veiculos":         total_veic,
        "preco_medio":            preco_medio,
        "preco_medio_var_pct":    preco_medio_var_pct,
        "preco_medio_delta_abs":  preco_delta_abs,
        "preco_ant":              preco_ant,
        "trend_label":            trend_label,
        "periodo_label":          periodo_label,
        "mes_ref_label":          mes_ref_label,
        "mes_ref":                mes_ref_usado,
        "ano_ref":                ano_ref_usado,
        "dias_uteis_periodo":     dias_uteis_periodo,
        "dias_uteis_ref":         dias_uteis_ref,
        "por_combustivel":        por_combustivel,
        "kml_medio":              kml_medio,
        "custo_km":               custo_km,
        "kml_fonte":              kml_fonte,  # "fkm_reconciliado" ou "truckpag"
    }

    # ── Gráfico mensal (últimos 12 meses) — aplica filtros de atributo ──────
    # Aplica apenas filtros de atributo (sem recorte temporal) para os gráficos históricos
    df_graf = df_all.copy()
    if grupo:
        df_graf = df_graf[df_graf["grupo_veiculo"] == grupo]
    if combustivel:
        df_graf = df_graf[df_graf["grupo_combustivel"] == combustivel]
    if estado:
        df_graf = df_graf[df_graf["filial_estado"] == estado]
    if regiao:
        df_graf = df_graf[df_graf["filial_regiao"] == regiao]
    if filial:
        df_graf = df_graf[df_graf["filial_nome"] == filial]

    df_graf = df_graf.copy()
    df_graf["ym"] = df_graf["data_transacao"].dt.to_period("M")
    ultimos_12 = sorted(df_all["data_transacao"].dt.to_period("M").unique())[-12:]
    grafico_mensal = []
    for p in ultimos_12:
        d = df_graf[df_graf["ym"] == p]
        grafico_mensal.append({
            "label": p.strftime("%b/%y"),
            "valor": round(float(d["valor"].sum()), 2),
            "litros": round(float(d["litragem"].sum()), 1),
        })

    # ── Gráfico semanal (últimas 8 semanas) ─────────────────────────────────
    df_graf["yw"] = df_graf["data_transacao"].dt.to_period("W")
    ultimas_8w = sorted(df_all["data_transacao"].dt.to_period("W").unique())[-8:]
    grafico_semanal = []
    for p in ultimas_8w:
        d = df_graf[df_graf["yw"] == p]
        label = "Sem " + p.start_time.strftime("%d/%m")
        grafico_semanal.append({
            "label": label,
            "valor": round(float(d["valor"].sum()), 2),
            "litros": round(float(d["litragem"].sum()), 1),
        })

    # ── Gráfico diário (últimos 30 dias corridos) ────────────────────────────
    df_graf["dia"] = df_graf["data_transacao"].dt.date
    if df_all.empty:
        ultimos_dias = []
    else:
        max_date = df_all["data_transacao"].dt.date.max()
        ultimos_dias = [max_date - timedelta(days=i) for i in range(29, -1, -1)]

    grafico_diario = []
    for dia in ultimos_dias:
        d = df_graf[df_graf["dia"] == dia]
        grafico_diario.append({
            "label":    dia.strftime("%d/%m"),
            "iso_date": dia.isoformat(),
            "tipo_dia": _tipo_dia(dia),
            "valor":    round(float(d["valor"].sum()), 2),
            "litros":   round(float(d["litragem"].sum()), 1),
        })

    # ── KPIs por grupo de veículo (mês selecionado) ──────────────────────────
    kml_mes_df = kml_df[
        (kml_df["data_transacao"].dt.month == mes) &
        (kml_df["data_transacao"].dt.year  == ano)
    ]

    grupos_data = {}
    for grp_nome, g in df_periodo.groupby("grupo_veiculo"):
        grupos_data[grp_nome] = {
            "grupo":    grp_nome,
            "gasto":    round(float(g["valor"].sum()), 2),
            "litros":   round(float(g["litragem"].sum()), 1),
            "veiculos": int(g["placa"].nunique()),
            "abs_count": int(len(g)),
            "km_rodado": 0.0,
            "kml":      None,
            "custo_km": None,
        }

    # Enriquece com km/l e custo/km do mês onde disponível
    for hp_grupo, gk in kml_mes_df.groupby("grupo_veiculo"):
        km_g  = float(gk["km_percorrido"].sum())
        lit_g = float(gk["litragem"].sum())
        val_g = float(gk["valor"].sum())
        if hp_grupo in grupos_data:
            grupos_data[hp_grupo]["km_rodado"] = round(km_g, 1)
            grupos_data[hp_grupo]["kml"]      = round(km_g / lit_g, 2) if lit_g > 0 else None
            grupos_data[hp_grupo]["custo_km"] = round(val_g / km_g, 2) if km_g  > 0 else None

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
    # Ordenar por nome (alfabética) em vez de gasto; exclui grupos sem classificação
    for v in sorted(grupos_data.values(), key=lambda x: str(x["grupo"]).lower()):
        if v["grupo"] in ("Outros", ""):
            continue
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
    mix.sort(key=lambda x: str(x["grupo"]).lower())

    # ── Por região ────────────────────────────────────────────────────────────
    por_regiao = []
    for reg, g in df_periodo.groupby("filial_regiao"):
        if not reg or reg in ("", "?"):
            continue
        por_regiao.append({
            "regiao":   reg,
            "valor":    round(float(g["valor"].sum()), 2),
            "litros":   round(float(g["litragem"].sum()), 1),
            "veiculos": int(g["placa"].nunique()),
            "filiais":  int(g["filial_nome"].nunique()),
            "pct":      round(float(g["valor"].sum()) / gasto_total_periodo_sem_filtro * 100, 1),
        })
    por_regiao.sort(key=lambda x: x["valor"], reverse=True)

    # ── Filiais (mês) ────────────────────────────────────────────────────────
    filiais = []
    for filial_nome, g in df_periodo.groupby("filial_nome"):
        if not filial_nome:
            continue
        comb_vals = g.groupby("grupo_combustivel")["valor"].sum()
        comb_pred = comb_vals.idxmax() if not comb_vals.empty else None
        filiais.append({
            "filial":           filial_nome,
            "estado":           g["filial_estado"].iloc[0] if len(g) else "",
            "regiao":           g["filial_regiao"].iloc[0] if len(g) else "",
            "gasto":            round(float(g["valor"].sum()), 2),
            "litros":           round(float(g["litragem"].sum()), 1),
            "veiculos":         int(g["placa"].nunique()),
            "combustivel_pred": comb_pred,
        })
    # Ordenar por gasto decrescente
    filiais.sort(key=lambda x: x["gasto"], reverse=True)

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
        "por_regiao":        por_regiao,
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


# ---------------------------------------------------------------------------
# Agressores por grupo de veículo
# ---------------------------------------------------------------------------

@router.get("/agressores")
def get_agressores(
    grupo: str = Query(...),
    modo_tempo: str = Query(default="mes"),
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
):
    """Retorna veículos abaixo da média do grupo, ordenados por desperdício."""
    now = datetime.now()
    mes = mes or now.month
    ano = ano or now.year

    kml_df = cache.get_kml_df()
    df_periodo = _apply_filters(kml_df, modo_tempo, ano, mes, bimestre, semestre, data_inicio, data_fim)
    df_grupo = df_periodo[df_periodo["grupo_veiculo"] == grupo]

    if df_grupo.empty:
        return {"grupo": grupo, "agressores": [], "destaques": [], "total_desperdicio": 0, "total_economia": 0, "total_agressores": 0, "total_destaques": 0, "kml_meta": None, "kml_grupo_avg": None, "veiculos_examinados": 0}

    # Combustivel predominante do grupo para buscar a meta
    comb_pred = df_grupo.groupby("grupo_combustivel")["valor"].sum().idxmax()
    kml_meta = get_kml_referencia(grupo, comb_pred)

    # Média real do grupo inteiro (comparação com precisão total)
    km_total = float(df_grupo["km_percorrido"].sum())
    lit_total = float(df_grupo["litragem"].sum())
    val_total = float(df_grupo["valor"].sum())

    if lit_total <= 0 or km_total <= 0:
        return {"grupo": grupo, "agressores": [], "destaques": [], "total_desperdicio": 0, "total_economia": 0, "total_agressores": 0, "total_destaques": 0, "kml_meta": None, "kml_grupo_avg": None, "veiculos_examinados": 0}

    kml_grupo_avg_exact = km_total / lit_total       # precisão total p/ comparação
    kml_grupo_avg       = round(kml_grupo_avg_exact, 2)  # arredondado p/ exibição

    # O "alvo" é a meta configurada (se existir), senão a média do grupo
    kml_alvo = kml_meta if kml_meta else kml_grupo_avg

    # Preço médio do litro no período para o grupo
    preco_medio = val_total / lit_total

    # Busca modelo de cada placa (do df completo de transações)
    df_all = cache.get_df()
    modelo_map = (
        df_all[df_all["grupo_veiculo"] == grupo]
        .drop_duplicates("placa")
        .set_index("placa")["modelo_veiculo"]
        .to_dict()
    )

    # Calcula km/L por placa — usa precisão total para a comparação
    agressores = []
    destaques = []
    veiculos_examinados = 0
    for placa, gp in df_grupo.groupby("placa"):
        km  = float(gp["km_percorrido"].sum())
        lit = float(gp["litragem"].sum())
        val = float(gp["valor"].sum())
        if km <= 0 or lit <= 0:
            continue
        veiculos_examinados += 1
        kml_real_exact = km / lit
        kml_real = round(kml_real_exact, 2)

        # Litros se estivesse na meta/alvo
        litros_na_alvo = km / kml_alvo
        delta_litros = lit - litros_na_alvo
        impacto = round(abs(delta_litros * preco_medio), 2)

        item = {
            "placa":       placa,
            "modelo":      modelo_map.get(placa, "—"),
            "kml_real":    kml_real,
            "kml_meta":    kml_alvo,
            "delta_kml":   round(kml_real_exact - kml_alvo, 2),
            "km_rodado":   round(km, 1),
            "litros":      round(lit, 1),
            "gasto":       round(val, 2),
        }

        if kml_real_exact < kml_grupo_avg_exact:
            item["desperdicio"] = round(max(delta_litros * preco_medio, 0), 2)
            agressores.append(item)
        else:
            item["economia"] = round(max(-delta_litros * preco_medio, 0), 2)
            destaques.append(item)

    agressores.sort(key=lambda x: x["desperdicio"], reverse=True)
    destaques.sort(key=lambda x: x["economia"], reverse=True)
    total_desperdicio = round(sum(a["desperdicio"] for a in agressores), 2)
    total_economia    = round(sum(d["economia"] for d in destaques), 2)

    return {
        "grupo":              grupo,
        "kml_meta":           kml_alvo,
        "kml_grupo_avg":      kml_grupo_avg,
        "combustivel_pred":   comb_pred,
        "preco_medio_litro":  round(preco_medio, 2),
        "total_desperdicio":  total_desperdicio,
        "total_economia":     total_economia,
        "total_agressores":   len(agressores),
        "total_destaques":    len(destaques),
        "veiculos_examinados": veiculos_examinados,
        "agressores":         agressores[:15],
        "destaques":          destaques[:15],
    }
