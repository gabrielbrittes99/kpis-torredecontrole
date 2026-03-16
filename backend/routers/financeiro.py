"""
Contas a pagar — títulos TruckPag e NF-e vinculadas.
Fonte: tabelas integration_truckpag_titulos e integration_truckpag_nfe_vinculos
       (lidas diretamente do PostgreSQL — nunca bate na API TruckPag)
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from db import get_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/financeiro", tags=["financeiro"])


def _query_titulos() -> list[dict]:
    sql = """
        SELECT
            t.titulo_id,
            t.data_geracao  AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS data_geracao,
            t.data_vencimento AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS data_vencimento,
            t.valor_total,
            COUNT(ti.id) AS qtd_transacoes
        FROM integration_truckpag_titulos t
        LEFT JOIN integration_truckpag_titulo_itens ti ON ti.titulo_id = t.id
        GROUP BY t.id, t.titulo_id, t.data_geracao, t.data_vencimento, t.valor_total
        ORDER BY t.data_vencimento DESC
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().fetchall()
    return [dict(r) for r in rows]


def _query_nfe_por_titulo(titulo_id_db: int) -> list[dict]:
    sql = """
        SELECT
            n.numero_nfe,
            n.chave_nfe,
            n.valor_total,
            n.data_emissao AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS data_emissao,
            n.vencimento_previsto AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS vencimento_previsto,
            n.cnpj_destinatario,
            n.operacao
        FROM integration_truckpag_nfe_vinculos n
        JOIN integration_truckpag_titulo_itens ti ON ti.transacao_id = n.id_transacao
        WHERE ti.titulo_id = :titulo_id
        ORDER BY n.data_emissao DESC
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"titulo_id": titulo_id_db}).mappings().fetchall()
    return [dict(r) for r in rows]


def _titulo_status(vencimento: datetime, valor: float) -> str:
    agora = datetime.now()
    if vencimento.tzinfo:
        agora = datetime.now(timezone.utc).astimezone(vencimento.tzinfo)
    if vencimento < agora:
        return "vencido"
    diff = (vencimento - agora).days
    if diff <= 3:
        return "vence_em_breve"
    return "a_vencer"


@router.get("/contas-a-pagar")
def get_contas_a_pagar():
    """
    Resumo de contas a pagar: títulos abertos, vencidos e a vencer.
    """
    try:
        titulos_raw = _query_titulos()
        agora = datetime.now()

        titulos = []
        total_a_vencer = 0.0
        total_vencido = 0.0
        total_vence_em_breve = 0.0
        proximo_vencimento = None

        for r in titulos_raw:
            venc = r["data_vencimento"]
            if hasattr(venc, "replace"):
                venc_naive = venc.replace(tzinfo=None) if venc.tzinfo else venc
            else:
                venc_naive = venc

            status = _titulo_status(venc_naive, float(r["valor_total"]))
            dias_ate_vencer = (venc_naive - agora).days

            titulo = {
                "titulo_id":       r["titulo_id"],
                "data_geracao":    r["data_geracao"].isoformat() if r["data_geracao"] else None,
                "data_vencimento": venc_naive.isoformat(),
                "valor_total":     float(r["valor_total"]),
                "qtd_transacoes":  int(r["qtd_transacoes"]),
                "status":          status,
                "dias_ate_vencer": dias_ate_vencer,
            }
            titulos.append(titulo)

            if status == "vencido":
                total_vencido += titulo["valor_total"]
            elif status == "vence_em_breve":
                total_vence_em_breve += titulo["valor_total"]
                if proximo_vencimento is None or venc_naive < proximo_vencimento["data"]:
                    proximo_vencimento = {"data": venc_naive, "valor": titulo["valor_total"], "titulo_id": titulo["titulo_id"]}
            else:
                total_a_vencer += titulo["valor_total"]
                if proximo_vencimento is None or venc_naive < proximo_vencimento["data"]:
                    proximo_vencimento = {"data": venc_naive, "valor": titulo["valor_total"], "titulo_id": titulo["titulo_id"]}

        return {
            "resumo": {
                "total_titulos":        len(titulos),
                "total_a_vencer":       round(total_a_vencer, 2),
                "total_vence_em_breve": round(total_vence_em_breve, 2),
                "total_vencido":        round(total_vencido, 2),
                "total_geral":          round(total_a_vencer + total_vence_em_breve + total_vencido, 2),
                "proximo_vencimento": {
                    "data":      proximo_vencimento["data"].isoformat() if proximo_vencimento else None,
                    "valor":     proximo_vencimento["valor"] if proximo_vencimento else None,
                    "titulo_id": proximo_vencimento["titulo_id"] if proximo_vencimento else None,
                } if proximo_vencimento else None,
            },
            "titulos": titulos,
            "atualizado_em": agora.isoformat(),
        }

    except Exception as e:
        logger.error(f"Financeiro (contas-a-pagar): {e}")
        return {"error": str(e)}


@router.get("/historico-titulos")
def get_historico_titulos():
    """
    Histórico completo de títulos com valor e data — útil para tendência de gasto semanal.
    """
    try:
        titulos_raw = _query_titulos()
        historico = []
        for r in titulos_raw:
            venc = r["data_vencimento"]
            ger = r["data_geracao"]
            historico.append({
                "titulo_id":       r["titulo_id"],
                "data_geracao":    ger.isoformat() if ger else None,
                "data_vencimento": venc.isoformat() if venc else None,
                "valor_total":     float(r["valor_total"]),
                "qtd_transacoes":  int(r["qtd_transacoes"]),
            })
        return {"titulos": historico, "total": len(historico)}

    except Exception as e:
        logger.error(f"Financeiro (historico): {e}")
        return {"error": str(e)}


@router.get("/nfe")
def get_nfe(limite: int = 50, cnpj_destinatario: str = None):
    """
    NF-e recentes vinculadas a abastecimentos.
    Filtrável por CNPJ do destinatário (filial Gritsch).
    """
    try:
        sql = """
            SELECT
                n.id_transacao,
                n.numero_nfe,
                n.chave_nfe,
                n.valor_total,
                n.data_emissao   AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS data_emissao,
                n.vencimento_previsto AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS vencimento_previsto,
                n.cnpj_destinatario,
                n.operacao
            FROM integration_truckpag_nfe_vinculos n
            WHERE (:cnpj IS NULL OR n.cnpj_destinatario = :cnpj)
            ORDER BY n.data_emissao DESC
            LIMIT :limite
        """
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text(sql), {
                "cnpj": cnpj_destinatario,
                "limite": limite,
            }).mappings().fetchall()

        nfes = []
        for r in rows:
            nfes.append({
                "id_transacao":      r["id_transacao"],
                "numero_nfe":        r["numero_nfe"],
                "chave_nfe":         r["chave_nfe"],
                "valor_total":       float(r["valor_total"]) if r["valor_total"] else None,
                "data_emissao":      r["data_emissao"].isoformat() if r["data_emissao"] else None,
                "vencimento_previsto": r["vencimento_previsto"].isoformat() if r["vencimento_previsto"] else None,
                "cnpj_destinatario": r["cnpj_destinatario"],
                "operacao":          r["operacao"],
            })

        return {"nfes": nfes, "total": len(nfes)}

    except Exception as e:
        logger.error(f"Financeiro (nfe): {e}")
        return {"error": str(e)}
