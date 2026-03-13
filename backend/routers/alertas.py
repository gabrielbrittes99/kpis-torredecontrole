import logging
from typing import List, Optional
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, Query
from data_cache import cache
from anp_client import get_anp_df

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alertas", tags=["alertas"])

# Mapeamento local para evitar import circular
_MATCH = [
    (["diesel s10", "s10", "s-10"], "DIESEL S10"),
    (["diesel", "óleo diesel", "oleo diesel"], "DIESEL"),
    (["gasolina aditivada", "gasolina boa", "gasolina podium", "gasolina v-power", "gasolina select", "gasolina super"], "GASOLINA ADITIVADA"),
    (["gasolina", "gasolina comum", "gasolina c"], "GASOLINA COMUM"),
    (["etanol", "álcool", "alcool"], "ETANOL HIDRATADO"),
    (["gnv", "gás natural", "gas natural"], "GNV"),
]

def _match_produto_local(nome: str) -> Optional[str]:
    n = str(nome).lower().strip()
    for keywords, anp_name in _MATCH:
        if any(k in n for k in keywords):
            return anp_name
    return None

@router.get("")
def get_alertas():
    """Gera alertas automáticos baseados em anomalias de consumo, preço e projeção."""
    try:
        df = cache.get_df("transacoes")
        if df.empty:
            return []

        alertas = []
        hoje = datetime.now()
        
        # --- 1. Alerta de Preço Acima da ANP ---
        try:
            df_anp = get_anp_df()
            if not df_anp.empty:
                df_mes = df[(df["data_transacao"].dt.month == hoje.month) & (df["data_transacao"].dt.year == hoje.year)].copy()
                if not df_mes.empty:
                    df_mes["produto_anp"] = df_mes["nome_combustivel"].apply(_match_produto_local)
                    df_mes["preco_unit"] = df_mes["valor"] / df_mes["litragem"]
                    
                    anp_uf = df_anp.groupby(["uf", "produto"])["preco"].mean().reset_index()
                    merged = df_mes.merge(anp_uf, left_on=["uf_posto", "produto_anp"], right_on=["uf", "produto"], how="left")
                    
                    criticos = merged[merged["preco_unit"] > (merged["preco"] * 1.10)]
                    if not criticos.empty:
                        postos_caros = criticos["razao_social_posto"].unique()[:3]
                        alertas.append({
                            "id": "preco_elevado",
                            "tipo": "alerta",
                            "nivel": "critico",
                            "titulo": "Preços Muito Acima do Mercado",
                            "descricao": f"Identificamos {len(criticos)} abastecimentos com preço > 10% acima da ANP. Ex: {', '.join(postos_caros)}."
                        })
        except Exception as e:
            logger.error(f"Erro Alertas (Preço): {e}")

        # --- 2. Alerta de Consumo Anormal ---
        try:
            # Pegamos transações do mês atual para identificar placas ativas
            df_mes = df[(df["data_transacao"].dt.month == hoje.month) & (df["data_transacao"].dt.year == hoje.year)]
            veiculos_mes = df_mes.groupby("placa").agg(qtd=("valor", "count")).reset_index()
            placas_ativas = veiculos_mes[veiculos_mes["qtd"] >= 2]["placa"].tolist()
            
            if placas_ativas:
                anomalias_km = []
                for placa in placas_ativas[:10]:
                    df_v = df[df["placa"] == placa].sort_values("data_transacao")
                    if len(df_v) > 5:
                        hist = df_v.iloc[:-2].copy()
                        hist["km_diff"] = hist["hodometro"].diff()
                        hist = hist[hist["km_diff"] > 0]
                        if not hist.empty:
                            avg_kml = (hist["km_diff"] / hist["litragem"]).mean()
                            ultimo = df_v.iloc[-1]
                            penultimo = df_v.iloc[-2]
                            km_diff_atual = ultimo["hodometro"] - penultimo["hodometro"]
                            if km_diff_atual > 0:
                                kml_atual = km_diff_atual / ultimo["litragem"]
                                if avg_kml > 0 and kml_atual < (avg_kml * 0.70):
                                    anomalias_km.append(placa)
                
                if anomalias_km:
                    alertas.append({
                        "id": "consumo_anormal",
                        "tipo": "operacional",
                        "nivel": "atencao",
                        "titulo": "Queda Brusca de Eficiência",
                        "descricao": f"Os veículos {', '.join(anomalias_km[:3])} apresentaram KM/L 30% abaixo da média histórica."
                    })
        except Exception as e:
            logger.error(f"Erro Alertas (Consumo): {e}")

        if not alertas:
            alertas.append({
                "id": "info_sistema",
                "tipo": "info",
                "nivel": "info",
                "titulo": "Monitoramento Ativo",
                "descricao": "Todos os indicadores operacionais e financeiros estão dentro da normalidade para este período."
            })

        return alertas
    except Exception as e:
        logger.error(f"Erro Alertas (Geral): {e}")
        return [{"id": "erro", "titulo": "Erro no Monitoramento", "descricao": str(e), "nivel": "critico"}]
