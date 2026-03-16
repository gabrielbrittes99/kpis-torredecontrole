import logging
from datetime import datetime

import pandas as pd
from fastapi import APIRouter

from data_cache import cache
from anp_client import get_anp_df
from market_client import get_market_summary
from config import FUEL_GROUPS

router = APIRouter(prefix="/api/torre", tags=["torre"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weighted_projection(df_mes: pd.DataFrame):
    """Projeção ponderada usando os últimos 21 dias (pesos declinantes 3→1)."""
    if df_mes.empty:
        return 0.0, 0.0, 0
    gasto_diario = (
        df_mes.groupby(df_mes["data_transacao"].dt.date)["valor"]
        .sum()
        .sort_index(ascending=False)
    )
    weights, values = [], []
    w = 3.0
    for i, val in enumerate(gasto_diario):
        if i >= 21:
            break
        weights.append(w)
        values.append(float(val))
        w = max(1.0, w - 0.1)

    media_diaria = sum(v * w for v, w in zip(values, weights)) / sum(weights) if weights else 0.0
    hoje = datetime.now()
    dias_mes = pd.Period(hoje.strftime("%Y-%m"), freq="D").days_in_month
    dias_rest = max(0, dias_mes - hoje.day)
    gasto_atual = float(df_mes["valor"].sum())
    return gasto_atual + media_diaria * dias_rest, media_diaria, dias_rest


def _media_historica(df: pd.DataFrame):
    """Média dos últimos 3 meses completos (valor, litros, preço/L)."""
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    passado = df[df["data_transacao"] < inicio_mes]
    if passado.empty:
        return {"valor": 220000.0, "litros": 37000.0, "preco": 5.90}
    mensal = passado.groupby(passado["data_transacao"].dt.to_period("M")).agg(
        valor=("valor", "sum"), litros=("litragem", "sum")
    )
    ultimos = mensal.tail(3)
    avg_v = float(ultimos["valor"].mean())
    avg_l = float(ultimos["litros"].mean())
    return {"valor": avg_v, "litros": avg_l, "preco": avg_v / avg_l if avg_l > 0 else 5.90}


def _veiculos_com_problema(df: pd.DataFrame, df_mes: pd.DataFrame) -> list[dict]:
    """
    Retorna veículos com KM/L >= 30% abaixo da sua própria média histórica.
    Só avalia placas com >= 5 abastecimentos históricos e hodômetro válido.
    """
    problemas = []
    placas_mes = df_mes["placa"].unique()

    for placa in placas_mes:
        df_v = df[df["placa"] == placa].sort_values("data_transacao")
        df_v = df_v[df_v["hodometro"] > 0]
        if len(df_v) < 5:
            continue

        df_v = df_v.copy()
        df_v["km_diff"] = df_v["hodometro"].diff()
        validos = df_v[(df_v["km_diff"] > 0) & (df_v["km_diff"] < 2000) & (df_v["litragem"] > 0)].copy()
        if len(validos) < 4:
            continue

        validos["kml"] = validos["km_diff"] / validos["litragem"]
        media_hist = float(validos.iloc[:-1]["kml"].mean())
        kml_recente = float(validos.iloc[-1]["kml"])

        if media_hist > 0 and kml_recente < media_hist * 0.70:
            desvio = round((kml_recente / media_hist - 1) * 100, 1)
            problemas.append({
                "placa": placa,
                "kml_atual": round(kml_recente, 2),
                "kml_medio": round(media_hist, 2),
                "desvio_pct": desvio,
            })

    return sorted(problemas, key=lambda x: x["desvio_pct"])[:10]


def _mix_combustiveis(df_mes: pd.DataFrame) -> list[dict]:
    """Distribuição de gasto por grupo de combustível no mês."""
    if df_mes.empty:
        return []
    total = float(df_mes["valor"].sum())
    if total == 0:
        return []
    grp = df_mes.groupby("grupo_combustivel").agg(valor=("valor", "sum"), litros=("litragem", "sum"))
    result = []
    for grupo, row in grp.iterrows():
        result.append({
            "grupo": grupo,
            "valor": round(float(row["valor"]), 2),
            "litros": round(float(row["litros"]), 2),
            "pct_valor": round(float(row["valor"]) / total * 100, 1),
        })
    return sorted(result, key=lambda x: x["valor"], reverse=True)


def _anp_benchmark(df_mes: pd.DataFrame):
    """Retorna variação % do preço pago vs ANP e saving acumulado."""
    var_anp_pct, saving = 0.0, 0.0
    pago_medio, anp_medio = 0.0, 0.0
    try:
        from routers.benchmark import get_resumo_benchmark, get_comparativo_frota
        resumo = get_resumo_benchmark()
        var_anp_pct = resumo.get("variacao_media_pct", 0.0)
        saving = resumo.get("saving_total_mes", 0.0)
        comp = get_comparativo_frota()
        if comp:
            total_l = sum(c["total_litros"] for c in comp)
            if total_l > 0:
                pago_medio = sum(c["preco_frota"] * c["total_litros"] for c in comp) / total_l
                anp_validos = [c for c in comp if c.get("preco_anp_mercado")]
                total_l_anp = sum(c["total_litros"] for c in anp_validos)
                if total_l_anp > 0:
                    anp_medio = sum(c["preco_anp_mercado"] * c["total_litros"] for c in anp_validos) / total_l_anp
    except Exception as e:
        logger.warning(f"Torre: erro no benchmark ANP: {e}")
    return var_anp_pct, saving, pago_medio, anp_medio


def _flex_anp():
    """Análise flex etanol vs gasolina com preços ANP nacionais."""
    try:
        df_anp = get_anp_df()
        if df_anp.empty:
            return None
        g = df_anp[df_anp["produto"] == "GASOLINA COMUM"]["preco"].mean()
        e = df_anp[df_anp["produto"] == "ETANOL HIDRATADO"]["preco"].mean()
        if g > 0 and e > 0:
            ratio = (e / g) * 100
            return {
                "gasolina_preco": round(g, 3),
                "etanol_preco": round(e, 3),
                "ratio": round(ratio, 1),
                "recomendacao": "USE ETANOL" if ratio < 70 else "USE GASOLINA",
                "ponto_equilibrio": 70.0,
            }
    except Exception as e:
        logger.warning(f"Torre: erro no flex ANP: {e}")
    return None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/dashboard")
async def get_vigilancia_dashboard():
    try:
        df = cache.get_df().copy()
        hoje = datetime.now()
        df_mes = df[
            (df["data_transacao"].dt.month == hoje.month) &
            (df["data_transacao"].dt.year == hoje.year)
        ]
        df_hoje = df_mes[df_mes["data_transacao"].dt.date == hoje.date()]

        # ── Histórico e projeção ───────────────────────────────────────────
        hist = _media_historica(df)
        proj_valor, media_diaria, dias_rest = _weighted_projection(df_mes)
        gasto_atual = float(df_mes["valor"].sum())
        litros_atual = float(df_mes["litragem"].sum())
        gasto_hoje = float(df_hoje["valor"].sum())

        # ── Causa raiz do desvio ───────────────────────────────────────────
        causa_raiz, msg_causa = "DENTRO DA META", "Operação dentro do padrão histórico."
        if proj_valor > hist["valor"] * 1.02:
            proj_litros = litros_atual * (proj_valor / gasto_atual) if gasto_atual > 0 else hist["litros"]
            var_preco = (gasto_atual / litros_atual / hist["preco"] - 1) if litros_atual > 0 else 0
            var_volume = (proj_litros / hist["litros"] - 1) if hist["litros"] > 0 else 0
            if var_preco > var_volume and var_preco > 0:
                causa_raiz = "PREÇO ALTO"
                msg_causa = f"Preço médio está {var_preco*100:.1f}% acima do histórico."
            elif var_volume > 0:
                causa_raiz = "EXCESSO LITROS"
                msg_causa = f"Volume {var_volume*100:.1f}% acima do esperado."
            else:
                causa_raiz = "ANOMALIA"
                msg_causa = "Picos atípicos detectados no período."

        # ── Benchmark ANP ─────────────────────────────────────────────────
        var_anp_pct, saving, pago_medio, anp_medio = _anp_benchmark(df_mes)

        # ── Veículos com problema ─────────────────────────────────────────
        veiculos_problema = _veiculos_com_problema(df, df_mes)

        # ── Mix de combustíveis ───────────────────────────────────────────
        mix = _mix_combustiveis(df_mes)

        # ── Análise flex ──────────────────────────────────────────────────
        flex = _flex_anp()

        # ── Anomalias ─────────────────────────────────────────────────────
        anomalias = []
        if proj_valor > hist["valor"] * 1.02:
            anomalias.append({
                "id": "projecao_acima",
                "titulo": causa_raiz,
                "detalhe": msg_causa,
                "valor": f"{((proj_valor / hist['valor']) - 1)*100:+.1f}%",
                "tipo": "critica",
            })
        if var_anp_pct > 2.0:
            anomalias.append({
                "id": "preco_vs_anp",
                "titulo": "Preço Acima do Mercado",
                "detalhe": f"Frota pagando {var_anp_pct:.1f}% acima da ANP.",
                "valor": f"+{var_anp_pct:.1f}%",
                "tipo": "preco",
            })
        if veiculos_problema:
            anomalias.append({
                "id": "consumo_anormal",
                "titulo": f"{len(veiculos_problema)} Veículo(s) com Consumo Anormal",
                "detalhe": f"KM/L ≥ 30% abaixo da média. Ex: {veiculos_problema[0]['placa']} ({veiculos_problema[0]['desvio_pct']}%)",
                "valor": f"{len(veiculos_problema)} veículos",
                "tipo": "frota",
            })
        dias_mes = pd.Period(hoje.strftime("%Y-%m"), freq="D").days_in_month
        meta_diaria = hist["valor"] / dias_mes
        if gasto_hoje > meta_diaria * 1.3:
            anomalias.append({
                "id": "pico_hoje",
                "titulo": "Pico de Gasto Hoje",
                "detalhe": f"R$ {gasto_hoje:,.0f} vs meta diária R$ {meta_diaria:,.0f}",
                "valor": f"{((gasto_hoje / meta_diaria) - 1)*100:+.0f}%",
                "tipo": "gasto",
            })

        # ── Mercado externo (Brent, câmbio, notícias) ─────────────────────
        mercado = get_market_summary()

        return {
            "data": {
                "situacao": {
                    "orcamento": {
                        "projecao":     round(proj_valor, 0),
                        "gasto_atual":  round(gasto_atual, 0),
                        "media_diaria": round(media_diaria, 0),
                        "dias_restantes": dias_rest,
                        "pct_media_hist": round(proj_valor / hist["valor"] * 100, 1) if hist["valor"] else 0,
                        "referencia_hist": round(hist["valor"], 0),
                    },
                    "veiculos": {
                        "ativos": int(df_mes["placa"].nunique()),
                        "com_problema": len(veiculos_problema),
                        "lista_problema": veiculos_problema[:5],
                    },
                    "preco_anp": {
                        "variacao_pct": round(var_anp_pct, 2),
                        "pago_medio":   round(pago_medio, 4),
                        "anp_medio":    round(anp_medio, 4),
                    },
                    "saving": {
                        "valor": round(saving, 2),
                    },
                },
                "mix_combustiveis": mix,
                "anomalias": anomalias,
                "flex": flex,
                "mercado": mercado,
                "causa_raiz": causa_raiz,
            },
            "periodo": hoje.strftime("%Y-%m"),
            "ultima_atualizacao": hoje.isoformat(),
            "cache_ttl_segundos": 600,
        }

    except Exception as e:
        import traceback
        logger.error(f"Torre dashboard erro: {e}\n{traceback.format_exc()}")
        return {
            "data": {"error": str(e)},
            "periodo": "error",
            "ultima_atualizacao": datetime.now().isoformat(),
            "cache_ttl_segundos": 600,
        }
