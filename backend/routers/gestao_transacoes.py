import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException

from truckpag_api import truckpag_api
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


def _get_today() -> tuple[str, str]:
    hoje = datetime.now().strftime("%Y-%m-%d")
    return hoje, hoje


def _get_default_dates() -> tuple[str, str]:
    fim = datetime.now()
    inicio = fim - timedelta(days=7)
    return inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")


def _extract_motivo(tx: Dict[str, Any]) -> str:
    """
    Extrai o motivo de recusa.
    Ordem de preferência:
    1. motivo_estorno_descricao (campo direto)
    2. MOTIVOS_RECUSA[motivo_estorno_id] (mapa local)
    3. mensagem (campo livre da API — remove sufixo " - Transacao XXXXXX")
    4. "Motivo não informado"
    """
    if tx.get("motivo_estorno_descricao"):
        return tx["motivo_estorno_descricao"]
    motivo_id = tx.get("motivo_estorno_id")
    if motivo_id and motivo_id in MOTIVOS_RECUSA:
        return MOTIVOS_RECUSA[motivo_id]
    mensagem = tx.get("mensagem", "") or ""
    if mensagem:
        # A mensagem vem no formato "Motivo - TPAG v2 - Posto X - Transacao 123"
        # Pegamos apenas o primeiro segmento (o motivo real)
        return mensagem.split(" - ")[0].strip()
    return "Motivo não informado"


def _enrich(tx: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza campos e adiciona descrição amigável do motivo."""
    tx["motivo_descricao"] = _extract_motivo(tx)
    return tx


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: KPIs do Dia
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis-dia")
async def get_kpis_dia():
    """KPIs consolidados do dia: aprovadas, recusadas, taxa, volume."""
    data_ini, data_fim = _get_today()

    try:
        todas = await truckpag_api.get_transacoes_analitico(data_ini, data_fim)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    total = len(todas)
    qtd_recusadas = sum(1 for t in todas if t.get("transacao_status") == "RECUSADA")
    qtd_aprovadas = sum(1 for t in todas if t.get("transacao_status") == "APROVADA")

    valor_total = sum(float(t.get("transacao_valor") or 0) for t in todas)
    placas = {t.get("veiculo_placa") for t in todas if t.get("veiculo_placa")}

    taxa_aprovacao = safe_round(qtd_aprovadas / total * 100, 1) if total > 0 else 0
    taxa_recusa    = safe_round(qtd_recusadas / total * 100, 1) if total > 0 else 0

    return {
        "valor_total":    safe_round(valor_total, 2),
        "qtd_aprovadas":  qtd_aprovadas,
        "qtd_recusadas":  qtd_recusadas,
        "taxa_aprovacao": taxa_aprovacao,
        "taxa_recusa":    taxa_recusa,
        "veiculos_unicos": len(placas),
        "total_transacoes": total,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Transações Recusadas
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/recusadas")
async def get_recusadas(
    data_inicio: Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    data_fim:    Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    limit:       int = Query(default=50),
):
    """Lista de transações recusadas, ordenadas da mais recente."""
    if not data_inicio or not data_fim:
        data_inicio, data_fim = _get_today()

    try:
        dados = await truckpag_api.get_transacoes_analitico(data_inicio, data_fim, status=["RECUSADA"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    dados = [_enrich(d) for d in dados]
    dados.sort(key=lambda x: x.get("transacao_data", ""), reverse=True)
    return dados[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Ranking de Motivos de Recusa
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/motivos-ranking")
async def get_motivos_ranking(
    data_inicio: Optional[str] = Query(default=None),
    data_fim:    Optional[str] = Query(default=None),
):
    """Ranking dos motivos de recusa com contagem e percentual."""
    if not data_inicio or not data_fim:
        data_inicio, data_fim = _get_today()

    try:
        recusadas = await truckpag_api.get_transacoes_analitico(data_inicio, data_fim, status=["RECUSADA"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not recusadas:
        return []

    contagem: Dict[str, int] = {}
    for r in recusadas:
        descricao = _extract_motivo(r)
        contagem[descricao] = contagem.get(descricao, 0) + 1

    total = len(recusadas)
    resultado = [
        {
            "motivo": m,
            "qtd": q,
            "pct": safe_round(q / total * 100, 1),
        }
        for m, q in contagem.items()
    ]
    resultado.sort(key=lambda x: x["qtd"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Analítico completo (todas as transações)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/analitico")
async def get_analitico(
    data_inicio: Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    data_fim:    Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    status:      Optional[str] = Query(default=None, description="recusada | aprovada"),
):
    """Todas as transações do período, com filtro opcional de status."""
    if not data_inicio or not data_fim:
        data_inicio, data_fim = _get_default_dates()

    status_filter = None
    if status and status.lower() in ("recusada", "recusadas"):
        status_filter = ["RECUSADA"]

    try:
        dados = await truckpag_api.get_transacoes_analitico(data_inicio, data_fim, status=status_filter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return [_enrich(d) for d in dados]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Veículos Live
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/veiculos")
async def get_veiculos_live():
    """Lista de veículos cadastrados na TruckPag."""
    return await truckpag_api.get_veiculos()
