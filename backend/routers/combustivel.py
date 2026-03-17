import calendar
from datetime import datetime
from typing import Optional

import pandas as pd
from data_cache import cache
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/combustivel", tags=["combustivel"])


def _apply_filters(
    df: pd.DataFrame,
    tipo_abastecimento: Optional[str],
    combustivel: Optional[str],
    placa: Optional[str],
) -> pd.DataFrame:
    if tipo_abastecimento:
        df = df[df["tipo_abastecimento"] == tipo_abastecimento]
    if combustivel:
        df = df[df["grupo_combustivel"] == combustivel]
    if placa:
        df = df[df["placa"] == placa.upper()]
    return df


# ---------------------------------------------------------------------------
# Filtros disponíveis
# ---------------------------------------------------------------------------


@router.get("/filtros")
def get_filtros():
    """Valores únicos disponíveis para os filtros do dashboard."""
    df = cache.get_df()
    if df.empty:
        return {
            "tipos_abastecimento": [],
            "combustiveis": [],
            "placas": [],
            "meses_disponiveis": [],
        }

    return {
        "tipos_abastecimento": sorted(
            df["tipo_abastecimento"].dropna().unique().tolist()
        ),
        "combustiveis": sorted(df["grupo_combustivel"].dropna().unique().tolist()),
        "placas": sorted(df["placa"].dropna().unique().tolist()),
        "meses_disponiveis": sorted(
            df["data_transacao"].dt.to_period("M").astype(str).unique().tolist()
        ),
    }


# ---------------------------------------------------------------------------
# KPIs principais
# ---------------------------------------------------------------------------


@router.get("/kpis")
def get_kpis(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    tipo_abastecimento: Optional[str] = Query(None),
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """KPIs do mês selecionado + mês anterior + projeção de fechamento."""
    df = _apply_filters(cache.get_df(), tipo_abastecimento, combustivel, placa)

    if df.empty:
        return {}

    # Determina mês de referência: filtro explícito ou último mês com dados
    if mes and ano:
        mes_ref, ano_ref = mes, ano
    else:
        ultima_data = df["data_transacao"].max()
        mes_ref, ano_ref = int(ultima_data.month), int(ultima_data.year)

    total_dias_mes = calendar.monthrange(ano_ref, mes_ref)[1]

    # Filtra para o mês selecionado
    df_mes = df[
        (df["data_transacao"].dt.month == mes_ref)
        & (df["data_transacao"].dt.year == ano_ref)
    ]

    total_valor = round(float(df_mes["valor"].sum()), 2)
    total_litros = round(float(df_mes["litragem"].sum()), 3)
    preco_medio = round(total_valor / total_litros, 4) if total_litros > 0 else 0
    qtd_abastecimentos = int(len(df_mes))
    dias_com_dados = int(df_mes["data_transacao"].dt.date.nunique())

    # Mês anterior
    data_ant = datetime(ano_ref, mes_ref, 1) - relativedelta(months=1)
    df_mes_ant = df[
        (df["data_transacao"].dt.month == data_ant.month)
        & (df["data_transacao"].dt.year == data_ant.year)
    ]
    valor_mes_anterior = round(float(df_mes_ant["valor"].sum()), 2)
    litros_mes_anterior = round(float(df_mes_ant["litragem"].sum()), 3)
    preco_medio_ant = round(valor_mes_anterior / litros_mes_anterior, 4) if litros_mes_anterior > 0 else 0

    # Variação de preço/L vs mês anterior (para o KPI card)
    variacao_preco_pct = (
        round((preco_medio - preco_medio_ant) / preco_medio_ant * 100, 2)
        if preco_medio_ant > 0 else 0
    )

    # Dia real do calendário
    hoje = datetime.now()
    if hoje.month == mes_ref and hoje.year == ano_ref:
        dia_calendario = min(hoje.day, total_dias_mes)
    else:
        dia_calendario = total_dias_mes  # mês fechado

    # Projeção: mês atual = projetar; mês fechado = realizado = projeção
    media_diaria_valor  = total_valor  / dias_com_dados if dias_com_dados > 0 else 0
    media_diaria_litros = total_litros / dias_com_dados if dias_com_dados > 0 else 0
    if hoje.month == mes_ref and hoje.year == ano_ref:
        projecao_valor  = round(media_diaria_valor  * total_dias_mes, 2)
        projecao_litros = round(media_diaria_litros * total_dias_mes, 3)
    else:
        projecao_valor  = total_valor
        projecao_litros = total_litros

    variacao_valor = round(projecao_valor - valor_mes_anterior, 2)
    variacao_pct = (
        round(variacao_valor / valor_mes_anterior * 100, 2)
        if valor_mes_anterior > 0 else 0
    )

    if variacao_pct > 2:   status = "ALTA"
    elif variacao_pct < -2: status = "BAIXA"
    else:                   status = "ESTAVEL"

    return {
        "total_valor":        total_valor,
        "total_litros":       total_litros,
        "preco_medio":        preco_medio,
        "variacao_preco_pct": variacao_preco_pct,
        "qtd_abastecimentos": qtd_abastecimentos,
        "valor_mes_atual":    total_valor,
        "litros_mes_atual":   total_litros,
        "valor_mes_anterior": valor_mes_anterior,
        "litros_mes_anterior": litros_mes_anterior,
        "dias_com_dados":     dias_com_dados,
        "dia_calendario":     dia_calendario,
        "total_dias_mes":     total_dias_mes,
        "mes_ref":            mes_ref,
        "ano_ref":            ano_ref,
        "projecao_valor":     projecao_valor,
        "projecao_litros":    projecao_litros,
        "variacao_valor":     variacao_valor,
        "variacao_pct":       variacao_pct,
        "status":             status,
        "ultima_atualizacao": (
            cache.last_updated.isoformat() if cache.last_updated else None
        ),
    }


@router.get("/kpis-estrategicos")
def get_kpis_estrategicos(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    tipo_abastecimento: Optional[str] = Query(None),
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """Novos KPIs Estratégicos com Projeção Ponderada conforme briefing Gritsch."""
    df = _apply_filters(cache.get_df(), tipo_abastecimento, combustivel, placa)

    if df.empty:
        return {}

    if mes and ano:
        mes_ref, ano_ref = mes, ano
    else:
        ultima_data = df["data_transacao"].max()
        mes_ref, ano_ref = int(ultima_data.month), int(ultima_data.year)

    df_mes = df[
        (df["data_transacao"].dt.month == mes_ref)
        & (df["data_transacao"].dt.year == ano_ref)
    ].copy()

    if df_mes.empty:
        return {}

    total_valor = float(df_mes["valor"].sum())
    total_litros = float(df_mes["litragem"].sum())

    # 1. Custo por KM rodado
    df_hod = df_mes.dropna(subset=["hodometro", "placa"])
    km_rodado_total = 0
    if not df_hod.empty:
        km_agg = df_hod.groupby("placa").agg(
            km_min=("hodometro", "min"),
            km_max=("hodometro", "max")
        )
        km_agg["km_rodado"] = km_agg["km_max"] - km_agg["km_min"]
        km_rodado_total = float(km_agg[km_agg["km_rodado"] > 0]["km_rodado"].sum())

    custo_por_km = total_valor / km_rodado_total if km_rodado_total > 0 else 0
    km_por_litro = km_rodado_total / total_litros if total_litros > 0 else 0

    # 2. Saving real do mês (vs ANP)
    from routers.benchmark import _match_produto
    from anp_client import get_anp_df

    df_anp = get_anp_df()
    saving_total = 0
    
    if not df_anp.empty:
        df_mes["produto_anp"] = df_mes["nome_combustivel"].apply(_match_produto)
        df_frota = df_mes[df_mes["produto_anp"].notna()]
        
        if not df_frota.empty:
            frota_agg = (
                df_frota.groupby(["uf_posto", "produto_anp"])
                .apply(lambda g: pd.Series({
                    "preco_frota": (g["valor"].sum() / g["litragem"].sum() if g["litragem"].sum() > 0 else 0),
                    "total_litros": g["litragem"].sum()
                }))
                .reset_index()
            )
            anp_agg = (
                df_anp.groupby(["uf", "produto"])["preco"]
                .mean().reset_index().rename(columns={"uf": "uf_posto", "produto": "produto_anp", "preco": "preco_anp"})
            )
            merged = frota_agg.merge(anp_agg, on=["uf_posto", "produto_anp"], how="left")
            
            for _, row in merged.iterrows():
                if pd.notna(row["preco_anp"]):
                    desvio = float(row["preco_frota"]) - float(row["preco_anp"])
                    if desvio < 0:
                        saving_total += abs(desvio) * float(row["total_litros"])

    # 3. Abastecimentos Fora de Rota
    df_hist_placa = df[df["placa"].isin(df_mes["placa"].unique())]
    uf_primarias = df_hist_placa.groupby("placa")["uf_posto"].apply(
        lambda x: x.mode()[0] if not x.mode().empty else None
    ).to_dict() if not df_hist_placa.empty else {}

    fora_de_rota = 0
    for _, row in df_mes.iterrows():
        p = row["placa"]
        if p in uf_primarias and uf_primarias[p] and row["uf_posto"] != uf_primarias[p]:
            fora_de_rota += 1
            
    pct_fora_rota = (fora_de_rota / len(df_mes)) * 100 if len(df_mes) > 0 else 0

    # 4. Projeção de Fechamento (Média Ponderada 3 Meses)
    def get_avg_diario(m_target, a_target):
        df_t = df[(df["data_transacao"].dt.month == m_target) & (df["data_transacao"].dt.year == a_target)]
        if df_t.empty: return 0
        dias = len(df_t["data_transacao"].dt.date.unique())
        return float(df_t["valor"].sum() / dias) if dias > 0 else 0

    avg0 = total_valor / len(df_mes["data_transacao"].dt.date.unique()) if not df_mes.empty else 0
    m1 = datetime(ano_ref, mes_ref, 1) - relativedelta(months=1)
    avg1 = get_avg_diario(m1.month, m1.year)
    m2 = datetime(ano_ref, mes_ref, 1) - relativedelta(months=2)
    avg2 = get_avg_diario(m2.month, m2.year)

    weighted_daily = (avg0 * 0.5) + (avg1 * 0.3) + (avg2 * 0.2) if (avg1 > 0 or avg2 > 0) else avg0
    
    total_dias = calendar.monthrange(ano_ref, mes_ref)[1]
    dia_atual = datetime.now().day if (mes_ref == datetime.now().month and ano_ref == datetime.now().year) else total_dias
    dias_rest = max(0, total_dias - dia_atual)
    
    proj_valor = total_valor + (weighted_daily * dias_rest)
    
    # Orçamento (5% acima do mês anterior como base)
    df_ant = df[(df["data_transacao"].dt.month == m1.month) & (df["data_transacao"].dt.year == m1.year)]
    budget = (float(df_ant["valor"].sum()) * 1.05) if not df_ant.empty else (total_valor * 1.15)
    
    meta_necessaria = (budget - total_valor) / dias_rest if dias_rest > 0 else 0
    desvio = proj_valor - budget
    pct_budget = (proj_valor / budget * 100) if budget > 0 else 0

    return {
        "custo_por_km": round(custo_por_km, 2),
        "km_por_litro": round(km_por_litro, 2),
        "saving_real": round(saving_total, 2),
        "fora_de_rota_qtd": fora_de_rota,
        "fora_de_rota_pct": round(pct_fora_rota, 1),
        "projecao_fechamento": round(proj_valor, 2),
        "meta_diaria_necessaria": round(meta_necessaria, 2),
        "desvio_reais": round(desvio, 2),
        "percentual_orcamento": round(pct_budget, 1),
        "dias_restantes": dias_rest,
        "abastecimentos_fora_rota": fora_de_rota
    }


# ---------------------------------------------------------------------------
# Gasto diário do mês
# ---------------------------------------------------------------------------


@router.get("/diario")
def get_diario(
    mes: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    tipo_abastecimento: Optional[str] = Query(None),
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """Gasto diário para o mês/ano selecionado."""
    df = _apply_filters(cache.get_df(), tipo_abastecimento, combustivel, placa)

    if df.empty:
        return []

    if mes is None or ano is None:
        ultima_data = df["data_transacao"].max()
        mes = mes or int(ultima_data.month)
        ano = ano or int(ultima_data.year)

    df_mes = df[
        (df["data_transacao"].dt.month == mes) & (df["data_transacao"].dt.year == ano)
    ]

    if df_mes.empty:
        return []

    result = (
        df_mes.groupby(df_mes["data_transacao"].dt.date)
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd_abastecimentos=("valor", "count"),
        )
        .reset_index()
        .rename(columns={"data_transacao": "dia"})
        .sort_values("dia")
    )

    return [
        {
            "dia": str(row["dia"]),
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 3),
            "qtd_abastecimentos": int(row["qtd_abastecimentos"]),
        }
        for _, row in result.iterrows()
    ]


# ---------------------------------------------------------------------------
# Distribuição por tipo de combustível
# ---------------------------------------------------------------------------


@router.get("/por-tipo")
def get_por_tipo(
    tipo_abastecimento: Optional[str] = Query(None),
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """Distribuição por tipo de combustível."""
    df = _apply_filters(cache.get_df(), tipo_abastecimento, combustivel, placa)

    if df.empty:
        return []

    total_litros_geral = float(df["litragem"].sum())

    result = (
        df.groupby("grupo_combustivel")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
        )
        .reset_index()
        .sort_values("total_litros", ascending=False)
    )

    return [
        {
            "nome_combustivel": row["grupo_combustivel"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 3),
            "qtd": int(row["qtd"]),
            "pct_litros": (
                round(float(row["total_litros"]) / total_litros_geral * 100, 1)
                if total_litros_geral > 0
                else 0
            ),
        }
        for _, row in result.iterrows()
    ]


# ---------------------------------------------------------------------------
# Histórico mensal de preço médio
# ---------------------------------------------------------------------------


@router.get("/historico-mensal")
def get_historico_mensal(
    tipo_abastecimento: Optional[str] = Query(None),
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
    por_combustivel: bool = Query(False, description="Separar série por tipo de combustível"),
):
    """
    Totais e preço médio por mês.
    Com por_combustivel=true retorna uma série por tipo, para comparar diesel vs diesel.
    """
    df = _apply_filters(cache.get_df(), tipo_abastecimento, combustivel, placa)

    if df.empty:
        return []

    df = df.copy()
    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    if por_combustivel:
        result = (
            df.groupby(["ano_mes", "grupo_combustivel"])
            .agg(total_valor=("valor", "sum"), total_litros=("litragem", "sum"))
            .reset_index()
            .sort_values(["grupo_combustivel", "ano_mes"])
        )
        # Retorna estrutura de séries: [{combustivel, dados:[{ano_mes, ...}]}]
        meses = sorted(result["ano_mes"].unique())
        tipos = sorted(result["grupo_combustivel"].unique())
        series = []
        for tipo in tipos:
            sub = result[result["grupo_combustivel"] == tipo].set_index("ano_mes")
            pontos = []
            for mes in meses:
                if mes in sub.index:
                    r = sub.loc[mes]
                    litros = float(r["total_litros"])
                    valor = float(r["total_valor"])
                    pontos.append({
                        "ano_mes": mes,
                        "total_valor": round(valor, 2),
                        "total_litros": round(litros, 0),
                        "preco_medio_litro": round(valor / litros, 4) if litros > 0 else 0,
                    })
                else:
                    pontos.append({"ano_mes": mes, "total_valor": 0, "total_litros": 0, "preco_medio_litro": None})
            series.append({"combustivel": tipo, "dados": pontos})
        return {"meses": meses, "series": series}

    result = (
        df.groupby("ano_mes")
        .agg(total_valor=("valor", "sum"), total_litros=("litragem", "sum"))
        .reset_index()
        .sort_values("ano_mes")
    )
    return [
        {
            "ano_mes": row["ano_mes"],
            "preco_medio_litro": (
                round(float(row["total_valor"]) / float(row["total_litros"]), 4)
                if float(row["total_litros"]) > 0 else 0
            ),
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 3),
        }
        for _, row in result.iterrows()
    ]


# ---------------------------------------------------------------------------
# Top postos
# ---------------------------------------------------------------------------


@router.get("/top-postos")
def get_top_postos(
    limit: int = Query(default=10, le=50),
    tipo_abastecimento: Optional[str] = Query(None),
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """Top postos por preço e benchmark ANP (para o Painel de Decisão)."""
    df = _apply_filters(cache.get_df(), tipo_abastecimento, combustivel, placa)

    if df.empty:
        return []

    # Agrupa por posto para pegar preço médio real pago
    postos_agg = (
        df.groupby(["razao_social_posto", "cidade_posto", "uf_posto"])
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            nome_combustivel_amostra=("nome_combustivel", "first")
        )
        .reset_index()
    )

    # Cruza com ANP (lógica simplificada similar ao benchmark municipal)
    from anp_client import get_anp_df
    from routers.benchmark import _match_produto
    df_anp = get_anp_df()
    
    resultados = []
    for _, row in postos_agg.iterrows():
        preco_medio = row["total_valor"] / row["total_litros"] if row["total_litros"] > 0 else 0
        prod_anp = _match_produto(row["nome_combustivel_amostra"])
        
        # Filtra ANP para o posto
        anp_ref = df_anp[
            (df_anp["uf"] == row["uf_posto"]) & 
            (df_anp["municipio"] == row["cidade_posto"].upper().strip()) & 
            (df_anp["produto"] == prod_anp)
        ]["preco"].mean() if not df_anp.empty else None
        
        # Fallback para estadual se municipal falhar
        if pd.isna(anp_ref) and not df_anp.empty:
            anp_ref = df_anp[
                (df_anp["uf"] == row["uf_posto"]) & 
                (df_anp["produto"] == prod_anp)
            ]["preco"].mean()

        var_pct = round((preco_medio - anp_ref) / anp_ref * 100, 2) if anp_ref else 0
        
        resultados.append({
            "razao_social_posto": row["razao_social_posto"],
            "cidade_posto": row["cidade_posto"],
            "uf_posto": row["uf_posto"],
            "preco_medio": round(float(preco_medio), 3),
            "variacao_pct": var_pct,
            "total_valor": round(float(row["total_valor"]), 2)
        })

    # Ordena pelo melhor preço (menor variação vs ANP)
    return sorted(resultados, key=lambda x: x["variacao_pct"])[:limit]


# ---------------------------------------------------------------------------
# Impacto de variação de preços
# ---------------------------------------------------------------------------


@router.get("/impacto-preco")
def get_impacto_preco(
    meses_historico: int = Query(default=3, ge=1, le=12),
    tipo_abastecimento: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """
    Compara volume histórico médio (N meses completos) com preço atual.
    Permite simular impacto de alta/baixa de preços no custo mensal.
    """
    df = _apply_filters(cache.get_df(), tipo_abastecimento, None, placa)

    if df.empty:
        return {"combustiveis": [], "total": {}, "meses_historico": meses_historico}

    df = df.copy()
    ultima_data = df["data_transacao"].max()
    mes_ref = int(ultima_data.month)
    ano_ref = int(ultima_data.year)

    mask_atual = (df["data_transacao"].dt.month == mes_ref) & (
        df["data_transacao"].dt.year == ano_ref
    )
    df_atual = df[mask_atual]

    df["_periodo"] = df["data_transacao"].dt.to_period("M")
    meses_completos = sorted(df[~mask_atual]["_periodo"].unique())[-meses_historico:]
    df_hist = df[df["_periodo"].isin(meses_completos)]

    if df_hist.empty:
        return {"combustiveis": [], "total": {}, "meses_historico": meses_historico}

    result = []
    for comb in sorted(df["grupo_combustivel"].dropna().unique()):
        h = df_hist[df_hist["grupo_combustivel"] == comb]
        a = df_atual[df_atual["grupo_combustivel"] == comb]

        if h.empty:
            continue

        litros_por_mes = h.groupby("_periodo")["litragem"].sum()
        media_litros_mes = float(litros_por_mes.mean())

        total_litros_hist = float(h["litragem"].sum())
        preco_hist = float(h["valor"].sum()) / total_litros_hist if total_litros_hist > 0 else 0

        litros_atual = float(a["litragem"].sum())
        if litros_atual > 0:
            preco_atual = float(a["valor"].sum()) / litros_atual
        else:
            preco_atual = preco_hist

        custo_hist_mensal = media_litros_mes * preco_hist
        custo_atual_mensal = media_litros_mes * preco_atual
        variacao_valor = custo_atual_mensal - custo_hist_mensal
        variacao_pct = (variacao_valor / custo_hist_mensal * 100) if custo_hist_mensal > 0 else 0

        result.append({
            "combustivel": comb,
            "media_litros_mes": round(media_litros_mes, 0),
            "preco_historico": round(preco_hist, 4),
            "preco_atual": round(preco_atual, 4),
            "custo_hist_mensal": round(custo_hist_mensal, 2),
            "custo_atual_mensal": round(custo_atual_mensal, 2),
            "variacao_valor": round(variacao_valor, 2),
            "variacao_pct": round(variacao_pct, 2),
        })

    total_custo_hist = sum(r["custo_hist_mensal"] for r in result)
    total_custo_atual = sum(r["custo_atual_mensal"] for r in result)
    total_variacao = total_custo_atual - total_custo_hist

    return {
        "combustiveis": result,
        "total": {
            "custo_hist_mensal": round(total_custo_hist, 2),
            "custo_atual_mensal": round(total_custo_atual, 2),
            "variacao_valor": round(total_variacao, 2),
            "variacao_pct": round(total_variacao / total_custo_hist * 100, 2) if total_custo_hist > 0 else 0,
        },
        "meses_historico": meses_historico,
        "meses_base": [str(m) for m in meses_completos],
    }


# ---------------------------------------------------------------------------
# Resumo por período — mês anterior / últimos 3 / últimos 6 meses
# ---------------------------------------------------------------------------


@router.get("/resumo-periodo")
def get_resumo_periodo(
    meses: int = Query(default=1, ge=1, le=12),
    tipo_abastecimento: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """
    Breakdown por tipo de combustível no período selecionado (meses completos),
    com comparativo vs período anterior equivalente.
    meses=1 → mês anterior completo vs mês retrasado
    meses=3 → últimos 3 meses vs 3 meses antes
    meses=6 → últimos 6 meses vs 6 meses antes
    """
    df = _apply_filters(cache.get_df(), tipo_abastecimento, None, placa)
    if df.empty:
        return {"combustiveis": [], "total": {}, "meses_incluidos": []}

    df = df.copy()
    ultima_data = df["data_transacao"].max()
    mes_ref = int(ultima_data.month)
    ano_ref = int(ultima_data.year)

    mask_atual = (df["data_transacao"].dt.month == mes_ref) & (
        df["data_transacao"].dt.year == ano_ref
    )
    df["_p"] = df["data_transacao"].dt.to_period("M")

    # Período selecionado: N meses completos mais recentes (excluindo mês atual)
    todos_completos = sorted(df[~mask_atual]["_p"].unique())
    meses_periodo   = todos_completos[-meses:]
    meses_anterior  = todos_completos[-(meses * 2) : -meses]

    df_p = df[df["_p"].isin(meses_periodo)]
    df_a = df[df["_p"].isin(meses_anterior)] if meses_anterior else pd.DataFrame()

    def _agg(g: pd.DataFrame):
        tv = float(g["valor"].sum())
        tl = float(g["litragem"].sum())
        return tv, tl, round(tv / tl, 4) if tl > 0 else 0

    combustiveis = []
    for comb in sorted(df_p["grupo_combustivel"].dropna().unique()):
        gp = df_p[df_p["grupo_combustivel"] == comb]
        ga = df_a[df_a["grupo_combustivel"] == comb] if not df_a.empty else pd.DataFrame()

        tv, tl, pl = _agg(gp)
        tv_a, tl_a, pl_a = _agg(ga) if not ga.empty else (None, None, None)

        combustiveis.append({
            "combustivel": comb,
            "total_valor":   round(tv, 2),
            "total_litros":  round(tl, 0),
            "preco_litro":   pl,
            "qtd_abastecimentos": int(len(gp)),
            # Comparativo vs período anterior
            "total_valor_ant":  round(tv_a, 2) if tv_a is not None else None,
            "total_litros_ant": round(tl_a, 0) if tl_a is not None else None,
            "preco_litro_ant":  pl_a,
            "var_valor":  round(tv - tv_a, 2) if tv_a is not None else None,
            "var_pct":    round((tv - tv_a) / tv_a * 100, 1) if tv_a else None,
            "var_preco":  round(pl - pl_a, 4) if pl_a is not None else None,
            "var_litros": round(tl - tl_a, 0) if tl_a is not None else None,
        })

    # Ordena por litros desc (maior volume = maior relevância)
    combustiveis.sort(key=lambda x: x["total_litros"], reverse=True)

    # Totais gerais
    tv_tot = float(df_p["valor"].sum())
    tl_tot = float(df_p["litragem"].sum())
    tv_tot_a = float(df_a["valor"].sum()) if not df_a.empty else None
    tl_tot_a = float(df_a["litragem"].sum()) if not df_a.empty else None

    return {
        "meses": meses,
        "meses_incluidos": [str(m) for m in meses_periodo],
        "meses_comparativo": [str(m) for m in meses_anterior],
        "combustiveis": combustiveis,
        "total": {
            "total_valor":    round(tv_tot, 2),
            "total_litros":   round(tl_tot, 0),
            "preco_medio":    round(tv_tot / tl_tot, 4) if tl_tot > 0 else 0,
            "total_valor_ant":  round(tv_tot_a, 2) if tv_tot_a is not None else None,
            "total_litros_ant": round(tl_tot_a, 0) if tl_tot_a is not None else None,
            "var_valor":  round(tv_tot - tv_tot_a, 2) if tv_tot_a is not None else None,
            "var_pct":    round((tv_tot - tv_tot_a) / tv_tot_a * 100, 1) if tv_tot_a else None,
        },
    }


# ---------------------------------------------------------------------------
# Custo por dia da semana (dia útil vs fim de semana)
# ---------------------------------------------------------------------------


@router.get("/custo-dia-semana")
def get_custo_dia_semana(
    combustivel: Optional[str] = Query(None),
    placa: Optional[str] = Query(None),
):
    """Média de gasto por dia: dias úteis (seg-sex) vs fim de semana (sáb-dom), por mês."""
    df = _apply_filters(cache.get_df(), None, combustivel, placa)
    if df.empty:
        return []

    df = df.copy()
    df["_periodo"] = df["data_transacao"].dt.to_period("M").astype(str)
    df["_tipo"] = df["data_transacao"].dt.dayofweek.apply(
        lambda x: "fds" if x >= 5 else "util"
    )
    df["_data"] = df["data_transacao"].dt.date

    resultado = []
    for periodo in sorted(df["_periodo"].unique()):
        df_mes = df[df["_periodo"] == periodo]
        row = {"periodo": periodo}

        for tipo in ["util", "fds"]:
            df_t = df_mes[df_mes["_tipo"] == tipo]
            dias = int(df_t["_data"].nunique())
            tv = float(df_t["valor"].sum())
            tl = float(df_t["litragem"].sum())
            row[f"total_valor_{tipo}"]  = round(tv, 2)
            row[f"total_litros_{tipo}"] = round(tl, 3)
            row[f"dias_{tipo}"]         = dias
            row[f"media_valor_{tipo}"]  = round(tv / dias, 2) if dias > 0 else 0
            row[f"media_litros_{tipo}"] = round(tl / dias, 3) if dias > 0 else 0

        # Razão fim-de-semana / dia-útil (>1 = fds gasta mais por dia)
        mu = row["media_valor_util"]
        mf = row["media_valor_fds"]
        row["ratio_fds_util"] = round(mf / mu, 3) if mu > 0 else None

        resultado.append(row)

    return resultado[-12:]  # últimos 12 meses


# ---------------------------------------------------------------------------
# Forçar atualização do cache
# ---------------------------------------------------------------------------


@router.post("/cache/refresh")
def refresh_cache():
    """Força atualização imediata do cache."""
    cache.force_refresh()
    df = cache.get_df()
    ultima_data = df["data_transacao"].max() if not df.empty else None
    return {
        "message": "Cache atualizado",
        "ultima_atualizacao": cache.last_updated.isoformat(),
        "total_registros": int(len(df)),
        "data_mais_recente": ultima_data.isoformat() if ultima_data is not None else None,
    }


@router.get("/outliers")
def get_outliers():
    """Retorna transações sinalizadas como outliers (Combustível indevido ou Veículo em Venda)."""
    df = cache.get_df()
    
    if df.empty:
        return {"combustivel": [], "venda": []}
    
    # 1. Combustível Indevido (ex: Pesado com Gasolina)
    df_comb = df[df["flag_combustivel_indevido"] == True][
        ["id", "data_transacao", "placa", "modelo_veiculo", "grupo_veiculo", "nome_combustivel", "litragem", "valor"]
    ].sort_values("data_transacao", ascending=False)
    
    # 2. Veículos em Venda/Vendido
    df_venda = df[df["flag_venda"] == True][
        ["id", "data_transacao", "placa", "modelo_veiculo", "filial_nome", "nome_combustivel", "litragem", "valor"]
    ].sort_values("data_transacao", ascending=False)
    
    return {
        "resumo": {
            "total_transacoes": int(len(df)),
            "qtd_outliers_combustivel": int(len(df_comb)),
            "qtd_outliers_venda": int(len(df_venda)),
        },
        "combustivel": df_comb.head(100).to_dict(orient="records"),
        "venda": df_venda.head(100).to_dict(orient="records"),
    }
