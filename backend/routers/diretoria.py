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
def get_kpis_estrategicos(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None)
):
    """
    KPIs de alto nível para a diretoria, com foco em impacto financeiro e eficiência.
    """
    df = cache.get_df()
    if df.empty:
        return {}

    hoje = datetime.now()
    mes_ref = mes if mes else hoje.month
    ano_ref = ano if ano else hoje.year
    
    # Determina se é o mês atual "em curso" para usar Like-for-Like
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
    custo_km = round(gasto_ano / km_ano, 3) if km_ano > 0 else 0

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
        # Se for o mês atual, verificamos até que dia temos dados
        dia_referencia = int(df_mes_ativo["data_transacao"].dt.day.max()) if not df_mes_ativo.empty else hoje.day
    else:
        dia_referencia = dias_no_mes
    
    proj_restante = 0.0
    
    if dia_referencia > 0 and dia_referencia < dias_no_mes:
        # Identifica se a data da transação ocorreu em final de semana (5=Sábado, 6=Domingo)
        df_mes_ativo["weekday"] = df_mes_ativo["data_transacao"].dt.dayofweek
        
        # Separa transações
        df_fds = df_mes_ativo[df_mes_ativo["weekday"].isin([5, 6])]
        df_uteis = df_mes_ativo[~df_mes_ativo["weekday"].isin([5, 6])]
        
        # Conta a quantidade de dias úteis e de finais de semana ATÉ o dia de referência
        dias_passados_uteis = 0
        dias_passados_fds = 0
        
        for d in range(1, dia_referencia + 1):
            wd = datetime(ano_ref, mes_ref, d).weekday()
            if wd in [5, 6]:
                dias_passados_fds += 1
            else:
                dias_passados_uteis += 1
                
        # Calcula médias
        media_dia_util = float(df_uteis["valor"].sum()) / dias_passados_uteis if dias_passados_uteis > 0 else 0
        media_fds = float(df_fds["valor"].sum()) / dias_passados_fds if dias_passados_fds > 0 else 0
        
        # Se uma das médias for zero por falta de amostra, usa a média geral como fallback
        if media_dia_util == 0 and media_fds == 0:
            media_geral = gasto_real_mes / dia_referencia
            media_dia_util = media_geral
            media_fds = media_geral
        elif media_dia_util == 0:
            media_dia_util = media_fds
        elif media_fds == 0:
            media_fds = media_dia_util
            
        # Conta quantos dias úteis e fds FALTAM para o mês acabar
        dias_restantes_uteis = 0
        dias_restantes_fds = 0
        
        for d in range(dia_referencia + 1, dias_no_mes + 1):
            wd = datetime(ano_ref, mes_ref, d).weekday()
            if wd in [5, 6]:
                dias_restantes_fds += 1
            else:
                dias_restantes_uteis += 1
                
        # Projeta o restante
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
        "custo_por_km": custo_km,
        "saving_acumulado_mes": saving_acumulado,
        "saving_resumo_anp": saving_resumo,
        "pct_diesel": pct_diesel,
        "score_saude": max(score, 0),
        "veiculos_ativos_mes": int(df_mes_ativo["placa"].nunique()) if not df_mes_ativo.empty else 0,
        "meses_completos": meses_completos,
        "dia_referencia_proj": dia_referencia
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
def get_mix_combustiveis(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None)
):
    """Retorna o mix de combustível do mês selecionado e do ano selecionado."""
    df = cache.get_df().copy()
    if df.empty:
        return {"mes": [], "ano": []}

    hoje = datetime.now()
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
    ano: Optional[int] = Query(None)
):
    """Matriz de gastos por filial e tipo de combustível vs média 3 meses anteriores ao selecionado."""
    from db_sqlserver import get_veiculos_df
    
    df_tp = cache.get_df().copy()
    df_veic = get_veiculos_df()
    
    if df_tp.empty:
        return []

    hoje = datetime.now()
    mes_ref = mes if mes else hoje.month
    ano_ref = ano if ano else hoje.year

    # Join com filiais
    df_tp["placa_norm"] = df_tp["placa"].str.upper().str.replace("-", "").str.strip()
    df_veic["Placa"] = df_veic["Placa"].str.upper().str.replace("-", "").str.strip()
    
    df = df_tp.merge(df_veic[["Placa", "FilialOperacional"]], left_on="placa_norm", right_on="Placa", how="left")
    df["FilialOperacional"] = df["FilialOperacional"].fillna("NÃO IDENTIFICADA")
    
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
    ano: Optional[int] = Query(None)
):
    """Comparação detalhada entre mês selecionado e seu anterior, respeitando LFL se for o mês corrente."""
    df = cache.get_df()
    if df.empty:
        return {}

    hoje = datetime.now()
    mes_ref = mes if mes else hoje.month
    ano_ref = ano if ano else hoje.year
    eh_mes_atual = (mes_ref == hoje.month and ano_ref == hoje.year)
    
    ref_dt = datetime(ano_ref, mes_ref, 1)
    
    if eh_mes_atual:
        # Se for o mês atual, a referência de "até que dia" é o último dado ou hoje.
        ultima_transacao = df[df["data_transacao"].dt.month == mes_ref]["data_transacao"].max()
        dia_referencia = ultima_transacao.day if not pd.isna(ultima_transacao) else hoje.day
    else:
        # Se for um mês passado, pegamos o mês cheio
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

        return {
            "mes": m,
            "ano": a,
            "total_valor": round(valor, 2),
            "total_litros": round(litros, 0),
            "total_km": round(km_periodo, 0),
            "preco_medio": round(valor / litros, 4) if litros > 0 else 0,
            "custo_km": round(valor / km_periodo, 3) if km_periodo > 0 else 0,
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
            "preco_medio": round(avg_preco, 4),
            "custo_km": round(avg_custo_km, 3),
            "meses_base": len(ultimos_3_meses)
        }

    variacao = {}
    if atual and anterior and anterior["total_valor"] > 0:
        variacao = {
            "valor_abs": round(atual["total_valor"] - anterior["total_valor"], 2),
            "valor_pct": round((atual["total_valor"] - anterior["total_valor"]) / anterior["total_valor"] * 100, 1),
            "litros_pct": round(((atual["total_litros"] / anterior["total_litros"]) - 1) * 100, 1) if anterior["total_litros"] > 0 else 0,
            "preco_abs": round(atual["preco_medio"] - anterior["preco_medio"], 4),
            "custo_km_abs": round(atual["custo_km"] - anterior["custo_km"], 3) if anterior["custo_km"] > 0 else 0,
        }

    variacao_avg = {}
    if atual and avg_3_meses and avg_3_meses["total_valor"] > 0:
        variacao_avg = {
            "valor_abs": round(atual["total_valor"] - avg_3_meses["total_valor"], 2),
            "valor_pct": round((atual["total_valor"] - avg_3_meses["total_valor"]) / avg_3_meses["total_valor"] * 100, 1),
            "litros_pct": round(((atual["total_litros"] / avg_3_meses["total_litros"]) - 1) * 100, 1) if avg_3_meses["total_litros"] > 0 else 0,
            "preco_abs": round(atual["preco_medio"] - avg_3_meses["preco_medio"], 4),
            "custo_km_abs": round(atual["custo_km"] - avg_3_meses["custo_km"], 3) if avg_3_meses["custo_km"] > 0 else 0,
        }

    return {
        "mes_atual": atual,
        "mes_anterior": anterior,
        "media_3_meses": avg_3_meses,
        "variacao": variacao,
        "variacao_vs_media": variacao_avg
    }
