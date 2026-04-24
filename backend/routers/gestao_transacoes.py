"""
Gestão de Transações — Monitoramento de aprovadas/recusadas

Fonte: DW silver.truckpag_analitico_transacao
(alimentado pela API TruckPag, contém aprovadas E recusadas)
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
from db_dw import get_dw_engine
from fastapi import APIRouter, Query
from sqlalchemy import text
from utils import safe_round

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gestao-transacoes", tags=["gestao_transacoes"])

# Mapa de motivos de recusa conforme documentação TruckPag
MOTIVOS_RECUSA: Dict[int, str] = {
    1: "Valor / Preço Divergente",
    2: "Estabelecimento Incorreto",
    3: "Dois Combustíveis",
    4: "Dois Serviços",
    5: "Lançamento Incorreto (Bomba Interna)",
    6: "Duplicidade de Transação",
    7: "Serviço Incorreto",
    8: "Placa Incorreta",
    9: "Transação de Teste",
    10: "NFe/NFSe Cancelada",
}


def _get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _fetch_dw(
    data_inicio: str, data_fim: str, status: Optional[str] = None
) -> pd.DataFrame:
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
            motivo_estorno_descricao,
            cartao_numero,
            tipo_medidor_unidade
        FROM silver.truckpag_analitico_transacao
        WHERE transacao_data::date >= '{data_inicio}'
          AND transacao_data::date <= '{data_fim}'
          {where_status}
        ORDER BY transacao_data DESC
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)

    return df


import re


def _extract_regras(mensagem: str) -> dict:
    """Extrai informações de regras violadas (ex: Valor do Litro acima da regra)."""
    if not mensagem:
        return {}

    # Exemplo de erro TruckPag: "Valor do litro (7.60) acima do teto (7.51)"
    # Ou "Valor do litro 7,60 acima do teto de R$ 7,51"
    # Vamos fazer um regex flexível para capturar números decimais próximos de palavras como 'acima', 'teto', 'regra'
    # Procurando padrão simples: "Valor do Litro(7.60) acima da regra R$(7.51)"

    resultado = {}

    # Tenta extrair valores de litro
    match_litro = re.search(
        r"(?:[Ll]itro|R\$/L|R\$ / L)[^\d]*?(\d+[\.,]\d+)[^\d]*?(?:acima|excede|regra|teto|limite)[^\d]*?(\d+[\.,]\d+)",
        mensagem,
        re.IGNORECASE,
    )
    if match_litro:
        try:
            val_tentado = float(match_litro.group(1).replace(",", "."))
            val_regra = float(match_litro.group(2).replace(",", "."))
            resultado["tipo_regra"] = "Preço/L"
            resultado["valor_tentado"] = val_tentado
            resultado["valor_regra"] = val_regra
            return resultado
        except Exception:
            pass

    # Tenta extrair valores totais
    match_valor = re.search(
        r"(?:[Vv]alor|R\$)[^\d]*?(\d+[\.,]\d+)[^\d]*?(?:acima|excede|regra|teto|limite)[^\d]*?(\d+[\.,]\d+)",
        mensagem,
        re.IGNORECASE,
    )
    if match_valor:
        try:
            val_tentado = float(match_valor.group(1).replace(",", "."))
            val_regra = float(match_valor.group(2).replace(",", "."))
            resultado["tipo_regra"] = "Valor Total"
            resultado["valor_tentado"] = val_tentado
            resultado["valor_regra"] = val_regra
            return resultado
        except Exception:
            pass

    return resultado


def _extract_motivo(row) -> str:
    """Extrai motivo de recusa de uma linha do DataFrame."""
    if (
        pd.notna(row.get("motivo_estorno_descricao"))
        and str(row["motivo_estorno_descricao"]).strip()
    ):
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
            "transacao_id": int(row["transacao_id"])
            if pd.notna(row.get("transacao_id"))
            else None,
            "transacao_data": str(row["transacao_data"])
            if pd.notna(row.get("transacao_data"))
            else None,
            "transacao_valor": float(row["transacao_valor"])
            if pd.notna(row.get("transacao_valor"))
            else 0,
            "transacao_status": str(row.get("transacao_status", "")),
            "veiculo_placa": str(row.get("veiculo_placa", "")),
            "motorista_nome": str(row.get("motorista_nome", "")),
            "combustivel_nome": str(row.get("combustivel_nome", "")),
            "litragem": float(row["litragem"]) if pd.notna(row.get("litragem")) else 0,
            "valor_litro": float(row["valor_litro"])
            if pd.notna(row.get("valor_litro"))
            else 0,
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
            "valor_total": 0,
            "qtd_aprovadas": 0,
            "qtd_recusadas": 0,
            "taxa_aprovacao": 0,
            "taxa_recusa": 0,
            "veiculos_unicos": 0,
            "total_transacoes": 0,
        }

    total = len(df)
    if total == 0:
        return {
            "valor_total": 0,
            "qtd_aprovadas": 0,
            "qtd_recusadas": 0,
            "taxa_aprovacao": 0,
            "taxa_recusa": 0,
            "veiculos_unicos": 0,
            "total_transacoes": 0,
        }

    qtd_aprovadas = int((df["transacao_status"] == "APROVADA").sum())
    qtd_recusadas = int((df["transacao_status"] == "RECUSADA").sum())
    valor_total = float(df["transacao_valor"].fillna(0).sum())
    placas = df["veiculo_placa"].dropna().nunique()

    return {
        "valor_total": safe_round(valor_total, 2),
        "qtd_aprovadas": qtd_aprovadas,
        "qtd_recusadas": qtd_recusadas,
        "taxa_aprovacao": safe_round(qtd_aprovadas / total * 100, 1)
        if total > 0
        else 0,
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
    data_fim: Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    limit: int = Query(default=50),
):
    """Fila de monitoramento de transações recusadas (Semaforo)."""
    hoje = _get_today()
    data_inicio = data_inicio or hoje
    data_fim = data_fim or hoje

    try:
        # Busca TODAS as transações do período (aprovadas e recusadas)
        df = _fetch_dw(data_inicio, data_fim, status=None)
    except Exception as e:
        logger.error(f"Gestão transações recusadas: {e}")
        return []

    if df.empty:
        return []

    # Ordena chronologicamente
    df = df.sort_values("transacao_data", ascending=True)

    pending = {}  # placa -> lista de rows recusadas pendentes
    resolved = []  # lista de tuples (row_recusada, tempo_resolucao)

    for _, row in df.iterrows():
        placa = str(row.get("veiculo_placa", "")).strip()
        if not placa or placa == "nan":
            continue

        status = str(row.get("transacao_status", "")).upper()
        if status == "RECUSADA":
            if placa not in pending:
                pending[placa] = []
            pending[placa].append(row)
        elif status == "APROVADA":
            if placa in pending and pending[placa]:
                # Todas as recusas pendentes para esta placa foram resolvidas por esta aprovação
                try:
                    res_time = pd.to_datetime(row["transacao_data"])
                except Exception:
                    res_time = pd.Timestamp.now()
                for p_row in pending[placa]:
                    resolved.append((p_row, res_time))
                pending[placa] = []  # Limpa a fila da placa

    now_ts = pd.Timestamp.now()
    results = []

    def _build_dict(r, color):
        return {
            "transacao_id": int(r["transacao_id"])
            if pd.notna(r.get("transacao_id"))
            else None,
            "transacao_data": str(r["transacao_data"])
            if pd.notna(r.get("transacao_data"))
            else None,
            "estabelecimento_nome": str(r.get("estabelecimento_nome", "")),
            "estabelecimento_cnpj": str(r.get("estabelecimento_cnpj", "")),
            "cartao_numero": str(r.get("cartao_numero", "")),
            "veiculo_placa": str(r.get("veiculo_placa", "")),
            "motorista_nome": str(r.get("motorista_nome", "")),
            "hodometro_anterior": int(r["hodometro_anterior"])
            if pd.notna(r.get("hodometro_anterior"))
            else None,
            "quilometragem": int(r["quilometragem"])
            if pd.notna(r.get("quilometragem"))
            else None,
            "tipo_medidor_unidade": str(r.get("tipo_medidor_unidade", "")),
            "litragem": float(r["litragem"]) if pd.notna(r.get("litragem")) else 0,
            "combustivel_nome": str(r.get("combustivel_nome", "")),
            "valor_litro": float(r["valor_litro"])
            if pd.notna(r.get("valor_litro"))
            else 0,
            "transacao_valor": float(r["transacao_valor"])
            if pd.notna(r.get("transacao_valor"))
            else 0,
            "transacao_status": str(r.get("transacao_status", "")),
            "motivo_descricao": _extract_motivo(r),
            "regras_sistema": _extract_regras(str(r.get("mensagem", ""))),
            "semaforo": color,
        }

    # Adiciona as pendentes (Amarelo ou Vermelho)
    for placa, rows in pending.items():
        for row in rows:
            try:
                t_data = pd.to_datetime(row["transacao_data"])
                if t_data.tzinfo is not None:
                    t_data = t_data.tz_convert(None)
                diff_minutes = (now_ts - t_data).total_seconds() / 60.0
            except Exception:
                diff_minutes = 0

            color = "red" if diff_minutes >= 5 else "yellow"
            results.append(_build_dict(row, color))

    # Adiciona as resolvidas (Verde) - aparece temporariamente e some na próxima atualização
    for row, res_time in resolved:
        try:
            if res_time.tzinfo is not None:
                res_time = res_time.tz_convert(None)
            diff_minutes = (now_ts - res_time).total_seconds() / 60.0
        except Exception:
            diff_minutes = 0

        # Mantém na tela apenas as aprovações muito recentes (<= 2.5 minutos)
        # Assim o operador vê que ficou verde e logo a transação limpa da tela
        if diff_minutes <= 2.5:
            results.append(_build_dict(row, "green"))

    # Ordena: o registro mais NOVO no topo (descending) para vermos sempre os ultimos alertas
    results.sort(
        key=lambda x: str(x["transacao_data"]) if x["transacao_data"] else "",
        reverse=True,
    )

    return results[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Ranking de Motivos de Recusa
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/motivos-ranking")
def get_motivos_ranking(
    data_inicio: Optional[str] = Query(default=None),
    data_fim: Optional[str] = Query(default=None),
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
# ENDPOINT: Aprovações Recentes (painel lateral)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/aprovadas-recentes")
def get_aprovadas_recentes(limit: int = Query(default=10)):
    """Últimas transações aprovadas do dia para o painel Aprovações Recentes."""
    hoje = _get_today()
    try:
        df = _fetch_dw(hoje, hoje, status="APROVADA")
    except Exception as e:
        logger.error(f"Gestão transações aprovadas-recentes: {e}")
        return []

    if df.empty:
        return []

    df = df.sort_values("transacao_data", ascending=False).head(limit)

    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "transacao_id": int(row["transacao_id"])
                if pd.notna(row.get("transacao_id"))
                else None,
                "transacao_data": str(row["transacao_data"])
                if pd.notna(row.get("transacao_data"))
                else None,
                "veiculo_placa": str(row.get("veiculo_placa", "")),
                "combustivel_nome": str(row.get("combustivel_nome", "")),
                "transacao_valor": float(row["transacao_valor"])
                if pd.notna(row.get("transacao_valor"))
                else 0,
                "litragem": float(row["litragem"])
                if pd.notna(row.get("litragem"))
                else 0,
                "valor_litro": float(row["valor_litro"])
                if pd.notna(row.get("valor_litro"))
                else 0,
                "estabelecimento_nome": str(row.get("estabelecimento_nome", "")),
            }
        )
    return records


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Atividade por hora (sparkline)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/atividade-hora")
def get_atividade_hora(horas: int = Query(default=6)):
    """Contagem de aprovadas e recusadas por hora nas últimas N horas."""
    hoje = _get_today()
    try:
        df = _fetch_dw(hoje, hoje)
    except Exception as e:
        logger.error(f"Gestão transações atividade-hora: {e}")
        return []

    if df.empty:
        agora = pd.Timestamp.now().replace(minute=0, second=0, microsecond=0)
        return [
            {"hora": (agora - pd.Timedelta(hours=i)).strftime("%H:00"), "aprovadas": 0, "recusadas": 0}
            for i in range(horas - 1, -1, -1)
        ]

    ts = pd.to_datetime(df["transacao_data"])
    if ts.dt.tz is not None:
        ts = ts.dt.tz_convert(None)
    df["hora"] = ts.dt.strftime("%H:00")

    agora = pd.Timestamp.now().replace(minute=0, second=0, microsecond=0)
    janela = [(agora - pd.Timedelta(hours=i)).strftime("%H:00") for i in range(horas - 1, -1, -1)]

    result = []
    for h in janela:
        fatia = df[df["hora"] == h]
        result.append(
            {
                "hora": h,
                "aprovadas": int((fatia["transacao_status"] == "APROVADA").sum()),
                "recusadas": int((fatia["transacao_status"] == "RECUSADA").sum()),
            }
        )
    return result


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Top postos do dia
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/top-postos")
def get_top_postos(limit: int = Query(default=3)):
    """Top N estabelecimentos por número de transações hoje."""
    hoje = _get_today()
    try:
        df = _fetch_dw(hoje, hoje)
    except Exception as e:
        logger.error(f"Gestão transações top-postos: {e}")
        return []

    if df.empty:
        return []

    df["estabelecimento_nome"] = df["estabelecimento_nome"].fillna("Desconhecido").str.strip()
    ranking = (
        df.groupby("estabelecimento_nome")
        .size()
        .sort_values(ascending=False)
        .head(limit)
    )
    total = len(df)
    return [
        {"nome": nome, "qtd": int(q), "pct": safe_round(q / total * 100, 1)}
        for nome, q in ranking.items()
    ]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Analítico completo (todas as transações)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/analitico")
def get_analitico(
    data_inicio: Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    data_fim: Optional[str] = Query(default=None, description="AAAA-MM-DD"),
    status: Optional[str] = Query(default=None, description="recusada | aprovada"),
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
