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
# Filtros de atributo (colunas enriquecidas pelo cache)
# ---------------------------------------------------------------------------

def _apply_attr_filters(
    df: pd.DataFrame,
    combustivel: Optional[str] = None,
    filial: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
    grupo: Optional[str] = None,
) -> pd.DataFrame:
    """Aplica filtros não-temporais (combustível, filial, UF, região, grupo de veículo)."""
    if df.empty:
        return df
    df = df.copy()
    if combustivel:
        df = df[df["grupo_combustivel"] == combustivel]
    if filial:
        df = df[df["filial_nome"] == filial]
    if estado:
        df = df[df["filial_estado"] == estado]
    if regiao:
        df = df[df["filial_regiao"] == regiao]
    if grupo:
        df = df[df["grupo_veiculo"] == grupo]
    return df


# ---------------------------------------------------------------------------
# KPIs estratégicos
# ---------------------------------------------------------------------------

@router.get("/kpis-estrategicos")
def get_kpis_estrategicos(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    combustivel: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    regiao: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
):
    """
    KPIs de alto nível para a diretoria, com foco em impacto financeiro e eficiência.
    Respeita filtros de atributo (combustível/filial/UF/região/grupo).
    """
    df = cache.get_df()
    if df.empty:
        return {}
    df = _apply_attr_filters(df, combustivel, filial, estado, regiao, grupo)
    if df.empty:
        return {}

    # Puxa a data máxima real que existe na base de dados (dataset cutoff)
    hoje = df["data_transacao"].max()
    if pd.isna(hoje): hoje = datetime.now()
    
    mes_ref = mes if mes else hoje.month
    ano_ref = ano if ano else hoje.year
    
    # Determina se é o mês atual "em curso" (último mês do dataset) para usar Like-for-Like
    eh_mes_atual = (mes_ref == hoje.month and ano_ref == hoje.year)
    
    df_ano = df[df["data_transacao"].dt.year == ano_ref].copy()
    if df_ano.empty: return {}

    # 1. Financeiro: Gasto e Projeção
    gasto_ano = round(float(df_ano["valor"].sum()), 2)
    litros_ano = round(float(df_ano["litragem"].sum()), 0)

    meses_completos = mes_ref - 1
    if meses_completos > 0:
        df_meses_completos = df_ano[df_ano["data_transacao"].dt.month < mes_ref]
        media_mensal = float(df_meses_completos["valor"].sum()) / meses_completos
    else:
        df_m = df_ano[df_ano["data_transacao"].dt.month == mes_ref]
        media_mensal = float(df_m["valor"].sum())
        
    projecao_anual = round(media_mensal * 12, 2)

    # 2. Eficiência: KM/L Médio Ano
    df_hod = df_ano.dropna(subset=["hodometro", "placa"])
    km_ano = 0
    if not df_hod.empty:
        km_agg = df_hod.groupby("placa").agg(
            km_min=("hodometro", "min"),
            km_max=("hodometro", "max")
        )
        km_ano = float((km_agg["km_max"] - km_agg["km_min"]).sum())

    kml_medio = round(km_ano / litros_ano, 2) if litros_ano > 0 else 0

    # ── KPIs escopo do PERÍODO selecionado (refletem o filtro de mês) ──
    df_periodo = df_ano[df_ano["data_transacao"].dt.month == mes_ref].copy()
    gasto_periodo  = float(df_periodo["valor"].sum())
    litros_periodo = float(df_periodo["litragem"].sum())
    preco_medio_periodo = round(gasto_periodo / litros_periodo, 2) if litros_periodo > 0 else 0

    km_periodo = 0.0
    df_hod_periodo = df_periodo.dropna(subset=["hodometro", "placa"])
    if not df_hod_periodo.empty:
        km_agg_p = df_hod_periodo.groupby("placa").agg(
            km_min=("hodometro", "min"),
            km_max=("hodometro", "max")
        )
        km_periodo = float((km_agg_p["km_max"] - km_agg_p["km_min"]).sum())
    # Custo/km do período só é confiável com volume mínimo de km na frota filtrada
    custo_km_periodo = round(gasto_periodo / km_periodo, 3) if km_periodo >= 10_000 else 0

    # 3. Saving Real (vs ANP) - Passando Filtros
    from routers.benchmark import get_resumo_benchmark
    saving_resumo = get_resumo_benchmark(mes=mes_ref, ano=ano_ref)
    saving_acumulado = saving_resumo.get("saving_total_mes", 0.0) # Seria ideal ter o anual, mas o mensal já é um bom proxy de performance recente

    # 4. Mix e Diesel
    DIESEL_KEYWORDS = ["diesel", "s10", "s-10"]
    df_ano["eh_diesel"] = df_ano["nome_combustivel"].str.lower().apply(
        lambda n: any(k in n for k in DIESEL_KEYWORDS)
    )
    gasto_diesel = round(float(df_ano[df_ano["eh_diesel"]]["valor"].sum()), 2)
    pct_diesel = round(gasto_diesel / gasto_ano * 100, 1) if gasto_ano > 0 else 0

    # 5. Saúde Operacional (Score 0-100)
    # Penaliza por: Desvio de orçamento, baixo KM/L, Preço acima da ANP
    score = 100
    if media_mensal > (gasto_ano / (mes_ref or 1)) * 1.1: score -= 20
    if kml_medio < 2.5: score -= 15
    if saving_resumo.get("variacao_media_pct", 0) > 0: score -= 15

    # Projeção Mês Ativo (Run-rate ponderado Dias Úteis vs Fim de Semana)
    df_mes_ativo = df_ano[df_ano["data_transacao"].dt.month == mes_ref].copy()
    gasto_real_mes = float(df_mes_ativo["valor"].sum())

    dias_no_mes = calendar.monthrange(ano_ref, mes_ref)[1]
    if eh_mes_atual:
        # Usa a data real do servidor — não a última transação do banco.
        # Se for cedo e ainda não chegaram transações do dia, o dia atual
        # é um dia corrente (não restante) mas com dados incompletos.
        dia_referencia = datetime.now().day
    else:
        dia_referencia = dias_no_mes
    
    proj_restante = 0.0
    dias_restantes_uteis = 0
    dias_restantes_fds   = 0
    media_dia_util       = 0.0
    media_fds            = 0.0

    if dia_referencia > 0 and dia_referencia < dias_no_mes:
        df_mes_ativo["weekday"] = df_mes_ativo["data_transacao"].dt.dayofweek
        df_mes_ativo["dia"]     = df_mes_ativo["data_transacao"].dt.day

        # ── Ritmo baseado nos últimos 30 dias corridos (excluindo hoje) ──
        # Usa o histórico recente cross-mês para não distorcer com poucos
        # dias do mês atual. Hoje é excluído por ter dados parciais.
        from datetime import timedelta
        hoje_dt = datetime(ano_ref, mes_ref, dia_referencia)
        ontem_dt = hoje_dt - timedelta(days=1)
        inicio_30d = ontem_dt - timedelta(days=29)  # 30 dias completos até ontem

        df_30d = df[
            (df["data_transacao"] >= pd.Timestamp(inicio_30d)) &
            (df["data_transacao"] <= pd.Timestamp(ontem_dt))
        ].copy()
        df_30d["weekday"] = df_30d["data_transacao"].dt.dayofweek
        df_30d["dia_dt"]  = df_30d["data_transacao"].dt.date

        dias_uteis_30d = df_30d[~df_30d["weekday"].isin([5, 6])]["dia_dt"].nunique()
        dias_fds_30d   = df_30d[ df_30d["weekday"].isin([5, 6])]["dia_dt"].nunique()

        valor_uteis_30d = float(df_30d[~df_30d["weekday"].isin([5, 6])]["valor"].sum())
        valor_fds_30d   = float(df_30d[ df_30d["weekday"].isin([5, 6])]["valor"].sum())

        media_dia_util = valor_uteis_30d / dias_uteis_30d if dias_uteis_30d > 0 else 0.0
        media_fds      = valor_fds_30d   / dias_fds_30d   if dias_fds_30d   > 0 else media_dia_util * 0.1

        # Dias restantes = a partir de hoje (inclusive), pois hoje tem dados parciais
        for d in range(dia_referencia, dias_no_mes + 1):
            wd = datetime(ano_ref, mes_ref, d).weekday()
            if wd in [5, 6]:
                dias_restantes_fds += 1
            else:
                dias_restantes_uteis += 1

        proj_restante = (media_dia_util * dias_restantes_uteis) + (media_fds * dias_restantes_fds)

    proj_total_mes = round(gasto_real_mes + proj_restante, 2)

    return {
        "status": "success",
        "ano_atual": ano_ref,
        "mes_ref": mes_ref,
        "eh_mes_atual": eh_mes_atual,
        "gasto_ano": gasto_ano,
        "litros_ano": litros_ano,
        "gasto_mes_atual_real": round(gasto_real_mes, 2),
        "proj_restante_mes": round(proj_restante, 2),
        "media_mensal": round(media_mensal, 2),
        "projecao_mes_atual": proj_total_mes,
        "projecao_anual": projecao_anual,
        "kml_medio": kml_medio,
        "preco_medio_litro": preco_medio_periodo,
        "preco_medio_ano": round(gasto_ano / litros_ano, 2) if litros_ano > 0 else 0,
        "custo_por_km": custo_km_periodo,
        "custo_por_km_ano": round(gasto_ano / km_ano, 3) if km_ano > 0 else 0,
        "saving_acumulado_mes": saving_acumulado,
        "saving_resumo_anp": saving_resumo,
        "pct_diesel": pct_diesel,
        "score_saude": max(score, 0),
        "veiculos_ativos_mes": int(df_mes_ativo["placa"].nunique()) if not df_mes_ativo.empty else 0,
        "meses_completos": meses_completos,
        "dia_referencia_proj": dia_referencia,
        "dias_restantes_uteis": dias_restantes_uteis,
        "media_dia_util": round(media_dia_util, 2),
    }



# ---------------------------------------------------------------------------
# Tendência mensal (12 meses)
# ---------------------------------------------------------------------------

@router.get("/tendencia-12-meses")
def get_tendencia_12_meses(
    combustivel: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    regiao: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
):
    """Últimos 12 meses de custo total, litros e preço médio. Respeita filtros de atributo."""
    df = cache.get_df()
    if df.empty:
        return []

    df = _apply_attr_filters(df, combustivel, filial, estado, regiao, grupo)
    if df.empty:
        return []
    
    # Identificar o último mês com dados completos vs mês atual parcial
    hoje = df["data_transacao"].max()
    if pd.isna(hoje): hoje = datetime.now()
    
    mes_atual = hoje.month
    ano_atual = hoje.year
    mes_parcial = f"{ano_atual}-{mes_atual:02d}"
    
    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    agg = (
        df.groupby("ano_mes")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd_veiculos=("placa", "nunique"),
            qtd_abastecimentos=("valor", "count"),
            dias_com_dados=("data_transacao", lambda x: x.dt.date.nunique()),
        )
        .reset_index()
        .sort_values("ano_mes")
        .tail(12)
    )
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(2)

    # Variação mês a mês
    agg["variacao_valor"] = agg["total_valor"].diff().round(2)
    agg["variacao_pct"] = (agg["total_valor"].pct_change() * 100).round(2)
    
    # Identificar se o mês é parcial (mês atual com menos de 25 dias de dados)
    # ou seja, um mês completo tem pelo menos 25 dias úteis
    agg["parcial"] = (agg["ano_mes"] == mes_parcial) & (agg["dias_com_dados"] < 25)

    return [
        {
            "ano_mes": row["ano_mes"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 0),
            "preco_medio": float(row["preco_medio"]),
            "qtd_veiculos": int(row["qtd_veiculos"]),
            "qtd_abastecimentos": int(row["qtd_abastecimentos"]),
            "dias_com_dados": int(row["dias_com_dados"]),
            "parcial": bool(row["parcial"]),
            "variacao_valor": float(row["variacao_valor"]) if pd.notna(row["variacao_valor"]) else None,
            "variacao_pct": float(row["variacao_pct"]) if pd.notna(row["variacao_pct"]) else None,
        }
        for _, row in agg.iterrows()
    ]


# ---------------------------------------------------------------------------
# Distribuição por tipo de combustível (todos os dados)
# ---------------------------------------------------------------------------

@router.get("/mix-combustiveis")
def get_mix_combustiveis(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    combustivel: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    regiao: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
):
    """Retorna o mix de combustível do mês selecionado e do ano selecionado."""
    df = cache.get_df().copy()
    if df.empty:
        return {"mes": [], "ano": []}

    df = _apply_attr_filters(df, combustivel, filial, estado, regiao, grupo)
    if df.empty:
        return {"mes": [], "ano": []}

    hoje = df["data_transacao"].max()
    if pd.isna(hoje): hoje = datetime.now()
    mes_ref = mes if mes else hoje.month
    ano_ref = ano if ano else hoje.year
    
    def categorize(name):
        n = str(name).upper()
        if any(k in n for k in ["DIESEL", "S10", "S-10", "BIODIESEL"]): return "DIESEL"
        if "GASOLINA" in n: return "GASOLINA"
        if any(k in n for k in ["ETANOL", "ALCOOL", "ÁLCOOL"]): return "ETANOL"
        if "GNV" in n: return "GNV"
        if "ARLA" in n: return "ARLA"
        return "OUTROS"

    df["categoria"] = df["nome_combustivel"].apply(categorize)

    def get_agg(target_df):
        if target_df.empty: return []
        total = float(target_df["valor"].sum())
        agg = target_df.groupby("categoria").agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum")
        ).reset_index()
        return [
            {
                "combustivel": r["categoria"],
                "total_valor": round(float(r["total_valor"]), 2),
                "pct": round(float(r["total_valor"]) / total * 100, 1) if total > 0 else 0
            } for _, r in agg.iterrows()
        ]

    # Mix Mês Selecionado
    df_mes = df[(df["data_transacao"].dt.month == mes_ref) & (df["data_transacao"].dt.year == ano_ref)]
    # Mix Ano Selecionado
    df_ano = df[df["data_transacao"].dt.year == ano_ref]

    return {
        "mes": get_agg(df_mes),
        "ano": get_agg(df_ano)
    }


@router.get("/gastos-filiais")
def get_gastos_filiais_matriz(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    combustivel: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    regiao: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
):
    """Matriz de gastos por filial e tipo de combustível vs média 3 meses anteriores ao selecionado."""
    from db_sqlserver import get_veiculos_df

    df_tp = cache.get_df().copy()
    df_veic = get_veiculos_df()

    if df_tp.empty:
        return []

    df_tp = _apply_attr_filters(df_tp, combustivel, None, estado, regiao, grupo)
    if df_tp.empty:
        return []

    hoje = df_tp["data_transacao"].max()
    if pd.isna(hoje): hoje = datetime.now()
    mes_ref = mes if mes else hoje.month
    ano_ref = ano if ano else hoje.year

    # Join com filiais
    df_tp["placa_norm"] = df_tp["placa"].str.upper().str.replace("-", "").str.strip()
    df_veic["Placa"] = df_veic["Placa"].str.upper().str.replace("-", "").str.strip()
    
    df = df_tp.merge(df_veic[["Placa", "FilialOperacional"]], left_on="placa_norm", right_on="Placa", how="left")
    df["FilialOperacional"] = df["FilialOperacional"].fillna("NÃO IDENTIFICADA")

    # Filtro de filial é aplicado após o join (o nome vem da tabela de veículos, não do cache)
    if filial:
        df = df[df["FilialOperacional"] == filial]
        if df.empty:
            return []

    def categorize(name):
        n = str(name).upper()
        if any(k in n for k in ["DIESEL", "S10", "S-10", "BIODIESEL"]): return "DIESEL"
        if "GASOLINA" in n: return "GASOLINA"
        if any(k in n for k in ["ETANOL", "ALCOOL", "ÁLCOOL"]): return "ETANOL"
        if "ARLA" in n: return "ARLA"
        return "OUTROS"
    
    df["categoria"] = df["nome_combustivel"].apply(categorize)
    
    # Mês selecionado
    df_mes = df[(df["data_transacao"].dt.month == mes_ref) & (df["data_transacao"].dt.year == ano_ref)]
    
    # Médias 3 meses (anteriores ao mês de referência)
    ref_dt = datetime(ano_ref, mes_ref, 1)
    m1 = ref_dt - relativedelta(months=1)
    m2 = ref_dt - relativedelta(months=2)
    m3 = ref_dt - relativedelta(months=3)
    df_hist = df[df["data_transacao"].dt.to_period("M").isin([m1.strftime("%Y-%m"), m2.strftime("%Y-%m"), m3.strftime("%Y-%m")])]
    
    # Agregação Mês
    agg_mes = df_mes.groupby(["FilialOperacional", "categoria"])["valor"].sum().reset_index()
    
    # Agregação Histórica (Média)
    agg_hist = df_hist.groupby(["FilialOperacional", "categoria", df_hist["data_transacao"].dt.to_period("M")])["valor"].sum().reset_index()
    agg_avg = agg_hist.groupby(["FilialOperacional", "categoria"])["valor"].mean().reset_index().rename(columns={"valor": "media_3m"})
    
    # Merge Final
    filiais = sorted(df["FilialOperacional"].unique())
    categorias = ["DIESEL", "ETANOL", "ARLA", "GASOLINA"]
    
    result = []
    for f in filiais:
        row = {"filial": f, "dados": {}}
        total_f_mes = 0
        total_f_avg = 0
        
        for c in categorias:
            val_mes = float(agg_mes[(agg_mes["FilialOperacional"] == f) & (agg_mes["categoria"] == c)]["valor"].sum())
            val_avg = float(agg_avg[(agg_avg["FilialOperacional"] == f) & (agg_avg["categoria"] == c)]["media_3m"].sum())
            
            row["dados"][c] = {
                "valor": round(val_mes, 2),
                "media_3m": round(val_avg, 2),
                "desvio_pct": round(((val_mes / val_avg) - 1) * 100, 1) if val_avg > 0 else 0
            }
            total_f_mes += val_mes
            total_f_avg += val_avg
            
        row["total_mes"] = round(total_f_mes, 2)
        row["total_avg"] = round(total_f_avg, 2)
        row["desvio_geral_pct"] = round(((total_f_mes / total_f_avg) - 1) * 100, 1) if total_f_avg > 0 else 0
        
        # Só adiciona ao resultado se houver movimentação financeira no real ou no histórico
        if total_f_mes > 0 or total_f_avg > 0:
            result.append(row)
        
    return result


# ---------------------------------------------------------------------------
# Resumo comparativo mês atual vs mês anterior
# ---------------------------------------------------------------------------

@router.get("/comparativo-meses")
def get_comparativo_meses(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    combustivel: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    regiao: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
):
    """Comparação detalhada entre mês selecionado e seu anterior, respeitando LFL se for o mês corrente.
    Respeita filtros de atributo (combustível/filial/UF/região/grupo)."""
    df = cache.get_df()
    if df.empty:
        return {}

    df = _apply_attr_filters(df, combustivel, filial, estado, regiao, grupo)
    if df.empty:
        return {}

    hoje = df["data_transacao"].max()
    if pd.isna(hoje): hoje = datetime.now()
    mes_ref = mes if mes else hoje.month
    ano_ref = ano if ano else hoje.year
    eh_mes_atual = (mes_ref == hoje.month and ano_ref == hoje.year)
    
    ref_dt = datetime(ano_ref, mes_ref, 1)
    
    if eh_mes_atual:
        # Usa a data real do servidor — não a última transação do banco,
        # que pode não ter chegado ainda se for cedo.
        dia_referencia = datetime.now().day
    else:
        dia_referencia = calendar.monthrange(ano_ref, mes_ref)[1]

    def resumo_mes(m, a, ate_dia=None):
        cond = (df["data_transacao"].dt.month == m) & (df["data_transacao"].dt.year == a)
        if ate_dia:
            cond &= (df["data_transacao"].dt.day <= ate_dia)
        sub = df[cond].copy()
        if sub.empty:
            return None
        
        litros = float(sub["litragem"].sum())
        valor = float(sub["valor"].sum())
        
        # Cálculo de KM no período
        km_periodo = 0
        df_hod = sub.dropna(subset=["hodometro", "placa"])
        if not df_hod.empty:
            km_agg = df_hod.groupby("placa").agg(
                min_h=("hodometro", "min"),
                max_h=("hodometro", "max")
            )
            km_periodo = float((km_agg["max_h"] - km_agg["min_h"]).sum())

        # custo_km só é confiável quando há km suficiente para a frota.
        # Com poucos dias, hodômetro esparso distorce o cálculo.
        # Exige mínimo de 50.000 km para garantir representatividade.
        custo_km = round(valor / km_periodo, 2) if km_periodo >= 50_000 else 0

        return {
            "mes": m,
            "ano": a,
            "total_valor": round(valor, 2),
            "total_litros": round(litros, 0),
            "total_km": round(km_periodo, 0),
            "preco_medio": round(valor / litros, 2) if litros > 0 else 0,
            "custo_km": custo_km,
            "dias_com_dados": int(sub["data_transacao"].dt.date.nunique()),
        }

    # Agora o comparativo é "Justo": do dia 1 ao dia X do mês atual vs dia 1 ao X dos meses anteriores
    data_anterior = ref_dt - relativedelta(months=1)
    
    atual = resumo_mes(mes_ref, ano_ref)
    anterior = resumo_mes(data_anterior.month, data_anterior.year, ate_dia=dia_referencia)

    # Média dos últimos 3 meses até o mesmo dia (excluindo o atual)
    ultimos_3_meses = []
    for i in range(1, 4):
        d = ref_dt - relativedelta(months=i)
        r = resumo_mes(d.month, d.year, ate_dia=dia_referencia)
        if r: ultimos_3_meses.append(r)
    
    avg_3_meses = None
    if ultimos_3_meses:
        avg_valor = sum(m["total_valor"] for m in ultimos_3_meses) / len(ultimos_3_meses)
        avg_preco = sum(m["preco_medio"] for m in ultimos_3_meses) / len(ultimos_3_meses)
        avg_litros = sum(m["total_litros"] for m in ultimos_3_meses) / len(ultimos_3_meses)
        avg_custo_km = sum(m["custo_km"] for m in ultimos_3_meses) / len(ultimos_3_meses)
        avg_3_meses = {
            "total_valor": round(avg_valor, 2),
            "total_litros": round(avg_litros, 0),
            "preco_medio": round(avg_preco, 2),
            "custo_km": round(avg_custo_km, 3),
            "meses_base": len(ultimos_3_meses)
        }

    variacao = {}
    if atual and anterior and anterior["total_valor"] > 0:
        variacao = {
            "valor_abs": round(atual["total_valor"] - anterior["total_valor"], 2),
            "valor_pct": round((atual["total_valor"] - anterior["total_valor"]) / anterior["total_valor"] * 100, 1),
            "litros_pct": round(((atual["total_litros"] / anterior["total_litros"]) - 1) * 100, 1) if anterior["total_litros"] > 0 else 0,
            "preco_abs": round(atual["preco_medio"] - anterior["preco_medio"], 2),
            "preco_pct": round((atual["preco_medio"] / anterior["preco_medio"] - 1) * 100, 1) if anterior["preco_medio"] > 0 else 0,
            "custo_km_abs": round(atual["custo_km"] - anterior["custo_km"], 2),
            "custo_km_pct": round((atual["custo_km"] / anterior["custo_km"] - 1) * 100, 1) if anterior["custo_km"] > 0 else 0,
        }

    variacao_avg = {}
    if atual and avg_3_meses and avg_3_meses["total_valor"] > 0:
        variacao_avg = {
            "valor_abs": round(atual["total_valor"] - avg_3_meses["total_valor"], 2),
            "valor_pct": round((atual["total_valor"] - avg_3_meses["total_valor"]) / avg_3_meses["total_valor"] * 100, 1),
            "litros_pct": round(((atual["total_litros"] / avg_3_meses["total_litros"]) - 1) * 100, 1) if avg_3_meses["total_litros"] > 0 else 0,
            "preco_abs": round(atual["preco_medio"] - avg_3_meses["preco_medio"], 2),
            "preco_pct": round((atual["preco_medio"] / avg_3_meses["preco_medio"] - 1) * 100, 1) if avg_3_meses["preco_medio"] > 0 else 0,
            "custo_km_abs": round(atual["custo_km"] - avg_3_meses["custo_km"], 2),
            "custo_km_pct": round((atual["custo_km"] / avg_3_meses["custo_km"] - 1) * 100, 1) if avg_3_meses["custo_km"] > 0 else 0,
        }

    return {
        "mes_atual": atual,
        "mes_anterior": anterior,
        "media_3_meses": avg_3_meses,
        "variacao": variacao,
        "variacao_vs_media": variacao_avg
    }


# ---------------------------------------------------------------------------
# Análise a partir de um mês de referência (ex: "Boom da guerra em Fev/2026")
# Permite ancorar em um mês e ver a evolução ponderada até o mês-alvo.
# ---------------------------------------------------------------------------

@router.get("/analise-referencia")
def get_analise_referencia(
    mes_ref: int = Query(..., description="Mês de referência (âncora)"),
    ano_ref: int = Query(..., description="Ano de referência"),
    mes_ate: Optional[int] = Query(None, description="Mês final da janela (default: último mês com dados)"),
    ano_ate: Optional[int] = Query(None, description="Ano final da janela"),
    combustivel: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    regiao: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
):
    """
    Retorna a evolução mês-a-mês entre um mês de referência e o mês-alvo,
    incluindo médias ponderadas (por litragem/km) e variações vs a referência.
    Respeita os filtros de atributo.
    """
    df_raw = cache.get_df()
    if df_raw.empty:
        return {}

    # df_scope = filtros NÃO-combustível (usado para calcular km real da frota)
    # df_fuel  = df_scope + filtro de combustível (usado para valor/litros/preço)
    df_scope = _apply_attr_filters(df_raw, None, filial, estado, regiao, grupo)
    df_fuel  = _apply_attr_filters(df_scope, combustivel, None, None, None, None)
    if df_fuel.empty:
        return {"status": "empty", "referencia": None, "serie": [], "ponderado": None}

    # Define mês-fim (alvo) — default = último mês com dados
    ultima = df_fuel["data_transacao"].max()
    if pd.isna(ultima):
        ultima = datetime.now()
    mes_fim = mes_ate if mes_ate else int(ultima.month)
    ano_fim = ano_ate if ano_ate else int(ultima.year)

    dt_ref = datetime(ano_ref, mes_ref, 1)
    dt_fim = datetime(ano_fim, mes_fim, 1)

    # Garante ordem correta (ref sempre ≤ fim)
    invertido = False
    if dt_fim < dt_ref:
        dt_ref, dt_fim = dt_fim, dt_ref
        invertido = True

    def _calcular_km(hod_df: pd.DataFrame) -> float:
        """KM por diff consecutivo de hodômetro por placa. Descarta diffs ≤0 ou >2000 km."""
        if hod_df.empty:
            return 0.0
        total = 0.0
        for _, g in hod_df.sort_values("data_transacao").groupby("placa"):
            diffs = g["hodometro"].diff()
            validos = diffs[(diffs > 0) & (diffs <= 2000)]
            total += float(validos.sum())
        return total

    def _preco_laspeyres(sub_fuel: pd.DataFrame, pesos: dict) -> float:
        """
        Preço médio ponderado pelo mix de combustível do mês de referência (índice de Laspeyres).
        Pesos = {grupo_combustivel: fração_litros_ref}.
        Isolando mudança de preço de mudança de mix entre meses.
        """
        if sub_fuel.empty or not pesos:
            return 0.0
        total_ponderado = 0.0
        total_peso_usado = 0.0
        for comb, peso in pesos.items():
            sub_c = sub_fuel[sub_fuel["grupo_combustivel"] == comb]
            litros_c = float(sub_c["litragem"].sum())
            valor_c  = float(sub_c["valor"].sum())
            if litros_c > 0:
                total_ponderado += (valor_c / litros_c) * peso
                total_peso_usado += peso
        return round(total_ponderado / total_peso_usado, 2) if total_peso_usado > 0 else 0.0

    def kpis_mes(m: int, a: int):
        sub_fuel = df_fuel[(df_fuel["data_transacao"].dt.month == m) & (df_fuel["data_transacao"].dt.year == a)]
        if sub_fuel.empty:
            return None
        valor  = float(sub_fuel["valor"].sum())
        litros = float(sub_fuel["litragem"].sum())

        placas = sub_fuel["placa"].unique()
        hod_scope = df_scope[
            (df_scope["data_transacao"].dt.month == m)
            & (df_scope["data_transacao"].dt.year == a)
            & (df_scope["placa"].isin(placas))
            & df_scope["hodometro"].notna()
            & (df_scope["hodometro"] > 0)
        ]
        km = _calcular_km(hod_scope)

        preco    = round(valor / litros, 2) if litros > 0 else 0
        custo_km = round(valor / km, 3) if km >= 1_000 else 0

        return {
            "mes": m,
            "ano": a,
            "rotulo": f"{m:02d}/{a}",
            "total_valor": round(valor, 2),
            "total_litros": round(litros, 0),
            "total_km": round(km, 0),
            "preco_medio": preco,
            "custo_km": custo_km,
            "qtd_veiculos": int(sub_fuel["placa"].nunique()),
            "_sub_fuel": sub_fuel,  # removido antes de retornar ao cliente
        }

    def pct(novo, base):
        if base is None or base == 0:
            return None
        return round((novo / base - 1) * 100, 1)

    def abs_diff(novo, base, casas=2):
        if base is None:
            return None
        return round(novo - base, casas)

    # Referência (mês-âncora)
    ref_raw = kpis_mes(dt_ref.month, dt_ref.year)
    if not ref_raw:
        return {"status": "sem_dados_referencia", "referencia": None, "serie": [], "ponderado": None}

    # Pesos do mês de referência por grupo_combustivel (índice de Laspeyres)
    # Usados fixos em todos os meses para isolar variação de preço da variação de mix.
    sub_ref = ref_raw.pop("_sub_fuel")
    litros_por_comb_ref = sub_ref.groupby("grupo_combustivel")["litragem"].sum()
    total_litros_ref_comb = float(litros_por_comb_ref.sum())
    pesos_ref = (litros_por_comb_ref / total_litros_ref_comb).to_dict() if total_litros_ref_comb > 0 else {}

    # Preço de referência já é a média ponderada do próprio mês (pesos somam 1, mesmo resultado)
    ref_raw["preco_ponderado"] = ref_raw["preco_medio"]
    ref = ref_raw

    # Série: cada mês da janela [ref → fim] com deltas vs referência
    # preco_pct e preco_abs usam o índice de Laspeyres (mix fixo da referência)
    serie = []
    cursor = dt_ref
    while cursor <= dt_fim:
        k = kpis_mes(cursor.month, cursor.year)
        if k:
            sub_m = k.pop("_sub_fuel")
            k["preco_ponderado"] = _preco_laspeyres(sub_m, pesos_ref)

            k["valor_pct"]     = pct(k["total_valor"],  ref["total_valor"])
            k["litros_pct"]    = pct(k["total_litros"], ref["total_litros"])
            k["km_pct"]        = pct(k["total_km"],     ref["total_km"]) if ref["total_km"] > 0 else None
            # Variação de preço: Laspeyres (mix fixo da ref) → isola efeito-preço do efeito-mix
            k["preco_abs"]     = abs_diff(k["preco_ponderado"], ref["preco_ponderado"], 2) if ref["preco_ponderado"] > 0 else None
            k["preco_pct"]     = pct(k["preco_ponderado"], ref["preco_ponderado"])
            k["custo_km_abs"]  = abs_diff(k["custo_km"], ref["custo_km"], 3) if (ref["custo_km"] > 0 and k["custo_km"] > 0) else None
            k["custo_km_pct"]  = pct(k["custo_km"], ref["custo_km"]) if (ref["custo_km"] > 0 and k["custo_km"] > 0) else None
            k["eh_referencia"] = (k["mes"] == ref["mes"] and k["ano"] == ref["ano"])
            serie.append(k)
        cursor = cursor + relativedelta(months=1)

    # Médias ponderadas do período completo (ref até fim, inclusive)
    dt_ini_ts = pd.Timestamp(dt_ref)
    ultimo_dia = calendar.monthrange(dt_fim.year, dt_fim.month)[1]
    dt_fim_ts = pd.Timestamp(datetime(dt_fim.year, dt_fim.month, ultimo_dia, 23, 59, 59))

    df_fuel_janela  = df_fuel[(df_fuel["data_transacao"]  >= dt_ini_ts) & (df_fuel["data_transacao"]  <= dt_fim_ts)]
    df_scope_janela = df_scope[(df_scope["data_transacao"] >= dt_ini_ts) & (df_scope["data_transacao"] <= dt_fim_ts)]

    ponderado = None
    if not df_fuel_janela.empty:
        v_j = float(df_fuel_janela["valor"].sum())
        l_j = float(df_fuel_janela["litragem"].sum())

        placas_janela = df_fuel_janela["placa"].unique()
        hod_janela = df_scope_janela[
            df_scope_janela["placa"].isin(placas_janela)
            & df_scope_janela["hodometro"].notna()
            & (df_scope_janela["hodometro"] > 0)
        ]
        km_j = _calcular_km(hod_janela)

        # Preço simples da janela (total gasto / total litros)
        preco_simples_janela = round(v_j / l_j, 2) if l_j > 0 else 0
        custo_km_pond = round(v_j / km_j, 3) if km_j >= 1_000 else 0

        # Preço Laspeyres do último mês da série (mês-alvo vs mês-âncora)
        # Responde: "quanto custaria em X o mesmo mix de combustível de fevereiro?"
        ultimo = serie[-1] if serie else None
        preco_laspeyres_ultimo = ultimo["preco_ponderado"] if ultimo else preco_simples_janela

        preco_vs_ref_pct = None
        if ref["preco_ponderado"] > 0 and preco_laspeyres_ultimo > 0:
            preco_vs_ref_pct = round((preco_laspeyres_ultimo / ref["preco_ponderado"] - 1) * 100, 1)
        custo_km_vs_ref_pct = None
        if ref["custo_km"] > 0 and custo_km_pond > 0:
            custo_km_vs_ref_pct = round((custo_km_pond / ref["custo_km"] - 1) * 100, 1)

        n_meses = len(serie)
        ponderado = {
            # Preço do último mês com mix fixo da referência (Laspeyres)
            "preco_medio_ponderado": preco_laspeyres_ultimo,
            "custo_km_ponderado": custo_km_pond,
            "gasto_total_janela": round(v_j, 2),
            "litros_total_janela": round(l_j, 0),
            "km_total_janela": round(km_j, 0),
            "gasto_medio_mensal": round(v_j / n_meses, 2) if n_meses > 0 else 0,
            "n_meses": n_meses,
            "preco_vs_ref_pct": preco_vs_ref_pct,
            "custo_km_vs_ref_pct": custo_km_vs_ref_pct,
            # Mix usado como peso (para transparência)
            "pesos_combustivel_ref": {k: round(v * 100, 1) for k, v in pesos_ref.items()},
        }

    return {
        "status": "success",
        "referencia": ref,
        "serie": serie,
        "ponderado": ponderado,
        "invertido": invertido,
    }
