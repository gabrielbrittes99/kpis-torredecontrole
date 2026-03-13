import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Query
from pydantic import BaseModel

from data_cache import cache
from anp_client import get_anp_df

router = APIRouter(prefix="/api/torre", tags=["torre"])
logger = logging.getLogger(__name__)

class TorreResponse(BaseModel):
    data: dict
    periodo: str
    ultima_atualizacao: str
    cache_ttl_segundos: int = 600

def _get_weighted_projection(df_mes: pd.DataFrame):
    if df_mes.empty:
        return 0, 0, 0
    gasto_diario = df_mes.groupby(df_mes["data_transacao"].dt.date)["valor"].sum().sort_index(ascending=False)
    if len(gasto_diario) == 0:
        return 0, 0, 0
    weights, values = [], []
    current_weight = 3.0
    for i, (date, val) in enumerate(gasto_diario.items()):
        if i >= 21: break
        weights.append(current_weight)
        values.append(val)
        current_weight = max(1.0, current_weight - 0.1)
    weighted_avg = sum(v * w for v, w in zip(values, weights)) / sum(weights) if weights else 0
    hoje = datetime.now()
    dias_no_mes = pd.Period(hoje.strftime("%Y-%m"), freq='D').days_in_month
    dias_corridos = hoje.day
    dias_restantes = max(0, dias_no_mes - dias_corridos)
    gasto_atual = df_mes["valor"].sum()
    projecao_restante = weighted_avg * dias_restantes
    return float(gasto_atual + projecao_restante), float(weighted_avg), int(dias_restantes)

def _get_indicadores_historicos(df: pd.DataFrame):
    hoje = datetime.now()
    primeiro_dia_atual = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    df_passado = df[df["data_transacao"] < primeiro_dia_atual]
    if df_passado.empty:
        return {"valor": 220000.0, "preco": 5.90, "litros_mes": 37000.0}
    mensal = df_passado.groupby(df_passado["data_transacao"].dt.to_period("M")).agg({"valor": "sum", "litragem": "sum"})
    ultimos_3 = mensal.tail(3)
    if ultimos_3.empty:
        return {"valor": 220000.0, "preco": 5.90, "litros_mes": 37000.0}
    avg_valor = float(ultimos_3["valor"].mean())
    avg_litros = float(ultimos_3["litragem"].mean())
    return {"valor": avg_valor, "preco": avg_valor/avg_litros if avg_litros > 0 else 5.90, "litros_mes": avg_litros}

@router.get("/dashboard", response_model=TorreResponse)
async def get_vigilancia_dashboard():
    try:
        df = cache.get_df().copy()
        hoje = datetime.now()
        df_mes = df[(df["data_transacao"].dt.month == hoje.month) & (df["data_transacao"].dt.year == hoje.year)]
        df_hoje = df_mes[df_mes["data_transacao"].dt.date == hoje.date()]
        
        hist = _get_indicadores_historicos(df)
        meta_orcamento = hist["valor"]
        
        proj_valor, meta_diaria_ponderada, dias_rest = _get_weighted_projection(df_mes)
        litros_atuais = float(df_mes["litragem"].sum())
        proj_litros = litros_atuais * (proj_valor / df_mes["valor"].sum()) if not df_mes.empty and df_mes["valor"].sum() > 0 else 0
        preco_medio_atual = df_mes["valor"].sum() / df_mes["litragem"].sum() if not df_mes.empty and df_mes["litragem"].sum() > 0 else hist["preco"]
        
        causa_raiz, msg_causa = "DENTRO DA META", "Operação seguindo o padrão histórico."
        if proj_valor > meta_orcamento:
            var_preco = (preco_medio_atual / hist["preco"]) - 1
            var_volume = (proj_litros / hist["litros_mes"]) - 1
            if var_preco > var_volume and var_preco > 0:
                causa_raiz = "PREÇO ALTO"
                msg_causa = f"O aumento se deve ao Preço Médio (está {var_preco*100:.1f}% acima do histórico)."
            elif var_volume > 0:
                causa_raiz = "EXCESSO LITROS"
                msg_causa = f"O aumento se deve ao Volume (consumo {var_volume*100:.1f}% acima do esperado)."
            else:
                causa_raiz, msg_causa = "ANOMALIA", "Aumento detectado por picos atípicos de gasto."

        gasto_hoje = float(df_hoje["valor"].sum())
        dias_no_mes = pd.Period(hoje.strftime("%Y-%m"), freq='D').days_in_month
        meta_diaria = meta_orcamento / dias_no_mes
        # 2. Benchmarks (ANP e Interno)
        var_anp_pct, saving_acumulado = 0.0, 0.0
        pago_medio, anp_medio = hist["preco"], hist["preco"]
        
        try:
            from routers.benchmark import get_resumo_benchmark, get_comparativo_frota
            bench_resumo = get_resumo_benchmark()
            var_anp_pct = bench_resumo.get("variacao_media_pct", 0.0)
            saving_acumulado = bench_resumo.get("saving_total_mes", 0.0)
            
            # Pega o preço pago e o anp do comparativo geral
            comp = get_comparativo_frota()
            if comp:
                # Média ponderada dos preços pagos vs mercado
                pago_medio = sum(c["preco_frota"] * c["total_litros"] for c in comp) / sum(c["total_litros"] for c in comp)
                anp_medio = sum(c["preco_anp_mercado"] * c["total_litros"] for c in comp if c["preco_anp_mercado"]) / sum(c["total_litros"] for c in comp if c["preco_anp_mercado"])
        except Exception as e:
            logger.warning(f"Erro ao calcular benchmarks no torre: {e}")

        # 3. Análise Flex Automática (Baseada em ANP Recente)
        flex_analysis = {"gasolina_preco": 5.80, "etanol_preco": 3.90, "ratio": 67.0, "recomendacao": "DADOS INDISPONÍVEIS", "economia_potencial": "0%"}
        try:
            df_anp = get_anp_df()
            if not df_anp.empty:
                # Preços médios nacionais mais recentes para o Flex
                g_preco = df_anp[df_anp["produto"] == "GASOLINA COMUM"]["preco"].mean()
                e_preco = df_anp[df_anp["produto"] == "ETANOL HIDRATADO"]["preco"].mean()
                if g_preco > 0 and e_preco > 0:
                    ratio = (e_preco / g_preco) * 100
                    rec = "USE ETANOL" if ratio < 70 else "USE GASOLINA"
                    econ = f"{abs(70 - ratio):.1f}%" if ratio < 70 else "0%"
                    flex_analysis = {
                        "gasolina_preco": round(g_preco, 2),
                        "etanol_preco": round(e_preco, 2),
                        "ratio": round(ratio, 1),
                        "recomendacao": rec,
                        "economia_potencial": econ
                    }
        except: pass

        # 4. Detecção de Anomalias Reais
        anomalias = []
        if proj_valor > meta_orcamento:
            anomalias.append({
                "id": 1, 
                "titulo": causa_raiz, 
                "detalhe": msg_causa, 
                "valor": f"{((proj_valor/meta_orcamento)-1)*100:+.1f}%", 
                "tipo": "critica"
            })
            
        # Alerta de variação vs ANP
        if var_anp_pct > 2.0:
            anomalias.append({
                "id": 10,
                "titulo": "PREÇO vs MERCADO",
                "detalhe": f"Sua frota está pagando {var_anp_pct:.1f}% acima da média ANP da semana.",
                "valor": f"+{var_anp_pct:.1f}%",
                "tipo": "preco"
            })

        # Gasto diário
        gasto_hoje = float(df_hoje["valor"].sum())
        dias_no_mes = pd.Period(hoje.strftime("%Y-%m"), freq='D').days_in_month
        meta_diaria = meta_orcamento / dias_no_mes
        if gasto_hoje > meta_diaria * 1.2:
            anomalias.append({
                "id": 2, 
                "titulo": "Pico de Gasto Hoje", 
                "detalhe": f"R$ {gasto_hoje:.2f} vs meta diária R$ {meta_diaria:.2f}", 
                "valor": f"{((gasto_hoje/meta_diaria)-1)*100:+.1f}%", 
                "tipo": "gasto"
            })

        # Veículos com consumo atípico (lógica simplificada)
        anomalias.append({"id": 4, "titulo": "Projeção Final", "detalhe": f"Fecha em R$ {proj_valor:.0f} vs meta histórica R$ {meta_orcamento:.0f}", "valor": f"R$ {proj_valor-meta_orcamento:.0f}", "tipo": "rota"})

        return {
            "data": {
                "situacao": {
                    "orcamento": {"valor": round((proj_valor / meta_orcamento * 100) if meta_orcamento else 0, 1), "projecao": round(proj_valor, 0), "meta": meta_orcamento},
                    "veiculos": {"count": 3, "ativos": df["placa"].nunique()},
                    "preco_anp": {"variacao": round(var_anp_pct, 1), "pago": round(pago_medio, 2), "anp": round(anp_medio, 2)},
                    "saving": {"valor": round(saving_total_acumulado := saving_acumulado, 2)}
                },
                "projecao_detalhe": {
                    "valor_projetado": round(proj_valor, 0), "meta_diaria": round(meta_diaria, 0), "dias_restantes": dias_rest, "desvio_total": round(proj_valor - meta_orcamento, 0),
                    "gasto_dia_atual": round(gasto_hoje, 0)
                },
                "anomalias": anomalias,
                "flex_analysis": flex_analysis,
                "score": {"precos": 78, "frota": 61, "orcamento": int(max(0, 100 - (proj_valor/meta_orcamento-1)*200)) if meta_orcamento else 100, "rota": 65}
            },
            "periodo": hoje.strftime("%Y-%m"),
            "ultima_atualizacao": hoje.isoformat(),
            "cache_ttl_segundos": 600
        }

    except Exception as e:
        import traceback
        return {"data": {"error": str(e), "trace": traceback.format_exc()}, "periodo": "error", "ultima_atualizacao": datetime.now().isoformat()}
