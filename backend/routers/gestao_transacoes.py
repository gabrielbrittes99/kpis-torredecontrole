"""
Gestão de Transações — Monitoramento de aprovadas/recusadas

Fonte: DW silver.truckpag_analitico_transacao
(alimentado pela API TruckPag, contém aprovadas E recusadas)
"""
import logging
from typing import Optional, Dict, Any

import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Query

from db_dw import get_dw_engine
from sqlalchemy import text
from utils import safe_round

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gestao-transacoes", tags=["gestao_transacoes"])

# Mapa de motivos de recusa conforme documentação TruckPag
MOTIVOS_RECUSA: Dict[int, str] = {
    1:  "Valor / Preço Divergente",
    2:  "Estabelecimento Incorreto",
    3:  "Dois Combustíveis",
    4:  "Dois Serviços",
    5:  "Lançamento Incorreto (Bomba Interna)",
    6:  "Duplicidade de Transação",
    7:  "Serviço Incorreto",
    8:  "Placa Incorreta",
    9:  "Transação de Teste",
    10: "NFe/NFSe Cancelada",
}


def _get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _fetch_dw(data_inicio: str, data_fim: str, status: Optional[str] = None) -> pd.DataFrame:
    """Consulta transações do DW silver por período e status opcional."""
    engine = get_dw_engine()

    where_status = ""
    if status:
        where_status = f"AND transacao_status = '{status.upper()}'"

    sql = f"""
        SELECT
            transacao_id,
            transacao_data,
            transacao_valor,
            transacao_tipo,
            transacao_status,
            veiculo_placa,
            motorista_nome,
            combustivel_nome,
            litragem,
            quilometragem,
            hodometro_anterior,
            valor_litro,
            estabelecimento_nome,
            estabelecimento_cnpj,
            mensagem,
            motivo_estorno_id,
            motivo_estorno_descricao
        FROM silver.truckpag_analitico_transacao
        WHERE transacao_data::date >= '{data_inicio}'
          AND transacao_data::date <= '{data_fim}'
          {where_status}
        ORDER BY transacao_data DESC
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)

    return df


def _extract_motivo(row) -> str:
    """Extrai motivo de recusa de uma linha do DataFrame."""
    if pd.notna(row.get("motivo_estorno_descricao")) and str(row["motivo_estorno_descricao"]).strip():
        return str(row["motivo_estorno_descricao"]).strip()
    motivo_id = row.get("motivo_estorno_id")
    if pd.notna(motivo_id) and int(motivo_id) in MOTIVOS_RECUSA:
        return MOTIVOS_RECUSA[int(motivo_id)]
    mensagem = str(row.get("mensagem") or "").strip()
    if mensagem:
        return mensagem.split(" - ")[0].strip()
    return "Motivo não informado"


def _df_to_list(df: pd.DataFrame) -> list[dict]:
    """Converte DataFrame para lista de dicts com motivo descritivo."""
    records = []
    for _, row in df.iterrows():
        r = {
            "transacao_id": int(row["transacao_id"]) if pd.notna(row.get("transacao_id")) else None,
            "transacao_data": str(row["transacao_data"]) if pd.notna(row.get("transacao_data")) else None,
            "transacao_valor": float(row["transacao_valor"]) if pd.notna(row.get("transacao_valor")) else 0,
            "transacao_status": str(row.get("transacao_status", "")),
            "veiculo_placa": str(row.get("veiculo_placa", "")),
            "motorista_nome": str(row.get("motorista_nome", "")),
            "combustivel_nome": str(row.get("combustivel_nome", "")),
            "litragem": float(row["litragem"]) if pd.notna(row.get("litragem")) else 0,
            "valor_litro": float(row["valor_litro"]) if pd.notna(row.get("valor_litro")) else 0,
            "estabelecimento_nome": str(row.get("estabelecimento_nome", "")),
            "motivo_descricao": _extract_motivo(row),
        }
        records.append(r)
    return records


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: KPIs do Dia
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis-dia")
def get_kpis_dia():
    """KPIs consolidados do dia: aprovadas, recusadas, taxa, volume."""
    hoje = _get_today()

    try:
        df = _fetch_dw(hoje, hoje)
    except Exception as e:
        logger.error(f"Gestão transações: falha ao consultar DW: {e}")
        return {
            "valor_total": 0, "qtd_aprovadas": 0, "qtd_recusadas": 0,
            "taxa_aprovacao": 0, "taxa_recusa": 0,
            "veiculos_unicos": 0, "total_transacoes": 0,
        }

    total = len(df)
    if total == 0:
        return {
            "valor_total": 0, "qtd_aprovadas": 0, "qtd_recusadas": 0,
            "taxa_aprovacao": 0, "taxa_recusa": 0,
            "veiculos_unicos": 0, "total_transacoes": 0,
        }

    qtd_aprovadas = int((df["transacao_status"] == "APROVADA").sum())
    qtd_recusadas = int((df["transacao_status"] == "RECUSADA").sum())
    valor_total = float(df["transacao_valor"].fillna(0).sum())
    placas = df["veiculo_placa"].dropna().nunique()

    return {
        "valor_total": safe_round(valor_total, 2),
        "qtd_aprovadas": qtd_aprovadas,
        "qtd_recusadas": qtd_recusadas,
        "taxa_aprovacao": safe_round(qtd_aprovadas / total * 100, 1) if total > 0 else 0,
        "taxa_recusa": safe_round(qtd_recusadas / total * 100, 1) if total > 0 else 0,
        "veiculos_unicos": int(placas),
        "total_transacoes": total,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Transações Recusadas
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/recusadas")
def get_recusadas(
    data_inicio: Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    data_fim:    Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    limit:       int = Query(default=50),
):
    """Lista de transações recusadas, ordenadas da mais recente."""
    hoje = _get_today()
    data_inicio = data_inicio or hoje
    data_fim = data_fim or hoje

    try:
        df = _fetch_dw(data_inicio, data_fim, status="RECUSADA")
    except Exception as e:
        logger.error(f"Gestão transações recusadas: {e}")
        return []

    return _df_to_list(df.head(limit))


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Ranking de Motivos de Recusa
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/motivos-ranking")
def get_motivos_ranking(
    data_inicio: Optional[str] = Query(default=None),
    data_fim:    Optional[str] = Query(default=None),
):
    """Ranking dos motivos de recusa com contagem e percentual."""
    hoje = _get_today()
    data_inicio = data_inicio or hoje
    data_fim = data_fim or hoje

    try:
        df = _fetch_dw(data_inicio, data_fim, status="RECUSADA")
    except Exception as e:
        logger.error(f"Gestão transações motivos: {e}")
        return []

    if df.empty:
        return []

    motivos = df.apply(_extract_motivo, axis=1)
    contagem = motivos.value_counts()
    total = len(df)

    return [
        {"motivo": m, "qtd": int(q), "pct": safe_round(q / total * 100, 1)}
        for m, q in contagem.items()
    ]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Analítico completo (todas as transações)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/analitico")
def get_analitico(
    data_inicio: Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    data_fim:    Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    status:      Optional[str] = Query(default=None, description="recusada | aprovada"),
):
    """Todas as transações do período, com filtro opcional de status."""
    hoje = _get_today()
    data_inicio = data_inicio or hoje
    data_fim = data_fim or hoje

    status_filter = None
    if status and status.lower() in ("recusada", "recusadas"):
        status_filter = "RECUSADA"
    elif status and status.lower() in ("aprovada", "aprovadas"):
        status_filter = "APROVADA"

    try:
        df = _fetch_dw(data_inicio, data_fim, status=status_filter)
    except Exception as e:
        logger.error(f"Gestão transações analítico: {e}")
        return []

    return _df_to_list(df)
