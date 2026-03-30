"""
TCO — Total Cost of Ownership (Custo Total de Propriedade)

Estratégia de dados por período:
  - Meses cobertos pelo FKM (jan/2025–fev/2026): usa FKM como fonte de verdade.
    O FKM já consolida: combustível, manutenção, pneus, lataria, arla.
  - Mês corrente (ainda não no FKM): usa cache TruckPag (transações + pedágios).
  - Valor FIPE / valor de compra: SQL Server (get_veiculos_df).

Join key: placa normalizada (uppercase, sem hífen) — padrão em todas as fontes.
"""
import logging
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Query

from data_cache import cache
from db_fkm import get_fkm_df
from utils import safe_round, apply_time_filters, apply_attribute_filters, norm_placa

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tco", tags=["tco"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fkm_meses_disponiveis() -> list[str]:
    df = get_fkm_df()
    return sorted(df["ano_mes"].dropna().unique().tolist()) if not df.empty else []


def _get_fkm_periodo(ano_mes: Optional[str]) -> pd.DataFrame:
    """Retorna FKM filtrado por ano_mes (ou o mais recente disponível)."""
    df = get_fkm_df()
    if df.empty:
        return df
    if not ano_mes:
        meses = _fkm_meses_disponiveis()
        ano_mes = meses[-1] if meses else None
    if ano_mes:
        df = df[df["ano_mes"] == ano_mes]
    return df


def _get_fipe_map() -> dict:
    """Retorna {placa: valor_fipe} do SQL Server."""
    try:
        from db_sqlserver import get_veiculos_df
        veic = get_veiculos_df()
        if veic.empty:
            return {}
        veic = veic.copy()
        veic["Placa"] = veic["Placa"].apply(norm_placa)
        # ValorAtualFIPE ou ValorCompra como fallback
        col = "ValorAtualFIPE" if "ValorAtualFIPE" in veic.columns else \
              "ValorCompra"    if "ValorCompra"    in veic.columns else None
        if not col:
            return {}
        return veic.set_index("Placa")[col].to_dict()
    except Exception as e:
        logger.warning(f"TCO: falha ao buscar FIPE: {e}")
        return {}


def _build_tco_row(placa: str, custo_comb: float, custo_pedagio: float,
                   custo_man: float, custo_pneus: float, custo_lataria: float,
                   custo_arla: float, total_km: float,
                   modelo: str, grupo: str, filial: str, fipe_map: dict) -> dict:
    custo_total = custo_comb + custo_pedagio + custo_man + custo_pneus + custo_lataria + custo_arla
    valor_fipe  = fipe_map.get(placa)
    pct_fipe    = safe_round(custo_total / float(valor_fipe) * 100, 1) if valor_fipe and float(valor_fipe) > 0 else None
    return {
        "placa":             placa,
        "modelo":            modelo,
        "grupo":             grupo,
        "filial":            filial,
        "custo_combustivel": safe_round(custo_comb, 2),
        "custo_pedagio":     safe_round(custo_pedagio, 2),
        "custo_manutencao":  safe_round(custo_man, 2),
        "custo_pneus":       safe_round(custo_pneus, 2),
        "custo_lataria":     safe_round(custo_lataria, 2),
        "custo_arla":        safe_round(custo_arla, 2),
        "custo_total":       safe_round(custo_total, 2),
        "total_km":          safe_round(total_km, 0),
        "custo_km":          safe_round(custo_total / total_km, 4) if total_km > 0 else 0,
        "valor_fipe":        safe_round(float(valor_fipe), 2) if valor_fipe else None,
        "pct_custo_vs_fipe": pct_fipe,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: TCO por veículo (via FKM — fonte de verdade para meses fechados)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-veiculo")
def get_por_veiculo(
    ano_mes:  Optional[str] = Query(default=None, description="YYYY-MM (usa FKM). Omitir = mês mais recente do FKM."),
    filial:   Optional[str] = Query(default=None),
    grupo:    Optional[str] = Query(default=None),
    limit:    int           = Query(default=30, le=200),
):
    """
    TCO por veículo usando FKM como fonte de verdade.
    Inclui: combustível, pedágio (estimado via TruckPag), manutenção, pneus, lataria, arla.
    """
    df_fkm = _get_fkm_periodo(ano_mes)
    if df_fkm.empty:
        return []

    if filial:
        df_fkm = df_fkm[df_fkm["filial"] == filial]
    if grupo:
        df_fkm = df_fkm[df_fkm["grupo_veiculo"] == grupo]

    # Pedágio do mesmo período via cache TruckPag
    df_pedag = cache.get_df("pedagios")
    if ano_mes and not df_pedag.empty:
        df_pedag = df_pedag.copy()
        df_pedag["ano_mes"] = df_pedag["data_transacao"].dt.to_period("M").astype(str)
        df_pedag = df_pedag[df_pedag["ano_mes"] == ano_mes]
    pedagio_map = df_pedag.groupby("placa")["valor"].sum().to_dict() if not df_pedag.empty else {}

    fipe_map = _get_fipe_map()

    resultado = []
    for _, row in df_fkm.iterrows():
        placa = str(row.get("placa", ""))
        resultado.append(_build_tco_row(
            placa         = placa,
            custo_comb    = float(row.get("valor_comb", 0)),
            custo_pedagio = float(pedagio_map.get(placa, 0)),
            custo_man     = float(row.get("manutencao", 0)),
            custo_pneus   = float(row.get("rodas_pneus", 0)),
            custo_lataria = float(row.get("lataria_pintura", 0)),
            custo_arla    = float(row.get("arla", 0)),
            total_km      = float(row.get("total_km", 0)),
            modelo        = str(row.get("modelo_simplificado", "")),
            grupo         = str(row.get("grupo_veiculo", "")),
            filial        = str(row.get("filial", "")),
            fipe_map      = fipe_map,
        ))

    resultado.sort(key=lambda x: x["custo_total"], reverse=True)
    return resultado[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: TCO para um veículo específico (caminho: /por-veiculo/{placa})
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-veiculo/{placa}")
def get_tco_veiculo(
    placa:   str,
    ano_mes: Optional[str] = Query(default=None),
):
    """Consolida combustível, pedágio e manutenção para uma placa específica."""
    placa_norm = norm_placa(placa)
    df_fkm = _get_fkm_periodo(ano_mes)
    df_fkm = df_fkm[df_fkm["placa"] == placa_norm]

    if df_fkm.empty:
        # Fallback: usa cache TruckPag (mês corrente não coberto pelo FKM)
        df_fuel  = cache.get_df("transacoes")
        df_pedag = cache.get_df("pedagios")
        df_fuel  = df_fuel[df_fuel["placa"]  == placa_norm]
        df_pedag = df_pedag[df_pedag["placa"] == placa_norm]
        return _build_tco_row(
            placa=placa_norm, custo_comb=float(df_fuel["valor"].sum()),
            custo_pedagio=float(df_pedag["valor"].sum()),
            custo_man=0, custo_pneus=0, custo_lataria=0, custo_arla=0,
            total_km=0, modelo="", grupo="", filial="",
            fipe_map=_get_fipe_map(),
        )

    row = df_fkm.iloc[0] if len(df_fkm) == 1 else df_fkm.iloc[0]

    df_pedag = cache.get_df("pedagios")
    if ano_mes and not df_pedag.empty:
        df_pedag = df_pedag.copy()
        df_pedag["ano_mes"] = df_pedag["data_transacao"].dt.to_period("M").astype(str)
        df_pedag = df_pedag[(df_pedag["placa"] == placa_norm) & (df_pedag["ano_mes"] == ano_mes)]
    else:
        df_pedag = df_pedag[df_pedag["placa"] == placa_norm]

    return _build_tco_row(
        placa=placa_norm,
        custo_comb    = float(df_fkm["valor_comb"].sum()),
        custo_pedagio = float(df_pedag["valor"].sum()),
        custo_man     = float(df_fkm["manutencao"].sum()),
        custo_pneus   = float(df_fkm["rodas_pneus"].sum()),
        custo_lataria = float(df_fkm["lataria_pintura"].sum()),
        custo_arla    = float(df_fkm["arla"].sum()),
        total_km      = float(df_fkm["total_km"].sum()),
        modelo        = str(row.get("modelo_simplificado", "")),
        grupo         = str(row.get("grupo_veiculo", "")),
        filial        = str(row.get("filial", "")),
        fipe_map      = _get_fipe_map(),
    )


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: KPIs consolidados da frota
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis")
def get_kpis(ano_mes: Optional[str] = Query(default=None)):
    """KPIs consolidados de TCO da frota: total, média por veículo, breakdown %."""
    df_fkm = _get_fkm_periodo(ano_mes)
    if df_fkm.empty:
        return {}

    custo_comb    = float(df_fkm["valor_comb"].sum())
    custo_man     = float(df_fkm["manutencao"].sum())
    custo_pneus   = float(df_fkm["rodas_pneus"].sum())
    custo_lataria = float(df_fkm["lataria_pintura"].sum())
    custo_arla    = float(df_fkm["arla"].sum())
    total_km      = float(df_fkm["total_km"].sum())

    # Pedágio do mesmo mês
    df_pedag = cache.get_df("pedagios")
    if ano_mes and not df_pedag.empty:
        df_pedag = df_pedag.copy()
        df_pedag["ano_mes"] = df_pedag["data_transacao"].dt.to_period("M").astype(str)
        df_pedag = df_pedag[df_pedag["ano_mes"] == ano_mes]
    custo_pedagio = float(df_pedag["valor"].sum()) if not df_pedag.empty else 0

    custo_total = custo_comb + custo_pedagio + custo_man + custo_pneus + custo_lataria + custo_arla
    qtd_veiculos = int(df_fkm["placa"].nunique())

    return {
        "ano_mes":           ano_mes or _fkm_meses_disponiveis()[-1] if _fkm_meses_disponiveis() else None,
        "qtd_veiculos":      qtd_veiculos,
        "custo_total":       safe_round(custo_total, 2),
        "custo_medio_veiculo": safe_round(custo_total / qtd_veiculos, 2) if qtd_veiculos > 0 else 0,
        "custo_km":          safe_round(custo_total / total_km, 4) if total_km > 0 else 0,
        "total_km":          safe_round(total_km, 0),
        "breakdown": {
            "combustivel": {"valor": safe_round(custo_comb, 2),    "pct": safe_round(custo_comb / custo_total * 100, 1) if custo_total > 0 else 0},
            "pedagio":     {"valor": safe_round(custo_pedagio, 2), "pct": safe_round(custo_pedagio / custo_total * 100, 1) if custo_total > 0 else 0},
            "manutencao":  {"valor": safe_round(custo_man, 2),     "pct": safe_round(custo_man / custo_total * 100, 1) if custo_total > 0 else 0},
            "pneus":       {"valor": safe_round(custo_pneus, 2),   "pct": safe_round(custo_pneus / custo_total * 100, 1) if custo_total > 0 else 0},
            "lataria":     {"valor": safe_round(custo_lataria, 2), "pct": safe_round(custo_lataria / custo_total * 100, 1) if custo_total > 0 else 0},
            "arla":        {"valor": safe_round(custo_arla, 2),    "pct": safe_round(custo_arla / custo_total * 100, 1) if custo_total > 0 else 0},
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: TCO por Filial
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-filial")
def get_por_filial(ano_mes: Optional[str] = Query(default=None)):
    """TCO agregado por filial."""
    df_fkm = _get_fkm_periodo(ano_mes)
    if df_fkm.empty:
        return []

    resultado = []
    for filial, g in df_fkm.groupby("filial"):
        total_km    = float(g["total_km"].sum())
        custo_comb  = float(g["valor_comb"].sum())
        custo_man   = float(g["manutencao"].sum()) + float(g["rodas_pneus"].sum()) + float(g["lataria_pintura"].sum())
        custo_total = float(g["total"].sum())
        resultado.append({
            "filial":        filial,
            "custo_total":   safe_round(custo_total, 2),
            "custo_km":      safe_round(custo_total / total_km, 4) if total_km > 0 else 0,
            "total_km":      safe_round(total_km, 0),
            "qtd_veiculos":  int(g["placa"].nunique()),
            "pct_comb":      safe_round(custo_comb / custo_total * 100, 1) if custo_total > 0 else 0,
            "pct_manut":     safe_round(custo_man / custo_total * 100, 1) if custo_total > 0 else 0,
        })
    resultado.sort(key=lambda x: x["custo_total"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: TCO por Grupo de Veículo
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-grupo")
def get_por_grupo(ano_mes: Optional[str] = Query(default=None)):
    """TCO por grupo de veículo (Truck, Toco, Leve, etc)."""
    df_fkm = _get_fkm_periodo(ano_mes)
    if df_fkm.empty:
        return []

    resultado = []
    for grupo, g in df_fkm.groupby("grupo_veiculo"):
        total_km    = float(g["total_km"].sum())
        custo_total = float(g["total"].sum())
        resultado.append({
            "grupo":        grupo,
            "custo_total":  safe_round(custo_total, 2),
            "custo_km":     safe_round(custo_total / total_km, 4) if total_km > 0 else 0,
            "total_km":     safe_round(total_km, 0),
            "qtd_veiculos": int(g["placa"].nunique()),
        })
    resultado.sort(key=lambda x: x["custo_total"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Evolução Mensal do TCO (série histórica do FKM)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/evolucao-mensal")
def get_evolucao_mensal(
    filial: Optional[str] = Query(default=None),
    grupo:  Optional[str] = Query(default=None),
):
    """Série mensal de TCO a partir do FKM (14 meses disponíveis)."""
    df = get_fkm_df()
    if df.empty:
        return []

    if filial:
        df = df[df["filial"] == filial]
    if grupo:
        df = df[df["grupo_veiculo"] == grupo]

    evolucao = (
        df.groupby("ano_mes")
        .agg(
            custo_total=("total", "sum"),
            custo_combustivel=("valor_comb", "sum"),
            custo_manutencao=("manutencao", "sum"),
            custo_pneus=("rodas_pneus", "sum"),
            total_km=("total_km", "sum"),
            qtd_veiculos=("placa", "nunique"),
        )
        .reset_index()
        .sort_values("ano_mes")
    )

    res = evolucao.to_dict(orient="records")
    for r in res:
        km = r["total_km"]
        r["custo_km"]          = safe_round(r["custo_total"] / km, 4) if km > 0 else 0
        r["custo_total"]       = safe_round(r["custo_total"], 2)
        r["custo_combustivel"] = safe_round(r["custo_combustivel"], 2)
        r["custo_manutencao"]  = safe_round(r["custo_manutencao"], 2)
        r["custo_pneus"]       = safe_round(r["custo_pneus"], 2)
        r["total_km"]          = safe_round(km, 0)
    return res


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Ranking (mantém compatibilidade com implementação anterior)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/ranking")
def get_ranking_tco(
    ano_mes: Optional[str] = Query(default=None),
    limit:   int           = Query(default=20, le=100),
):
    """Ranking de veículos com maior TCO. Alias para /por-veiculo com limit."""
    return get_por_veiculo(ano_mes=ano_mes, filial=None, grupo=None, limit=limit)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Alerta — custo alto vs FIPE
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/alerta-custo-alto")
def get_alerta_custo_alto(
    pct_fipe_limite: float = Query(default=30.0, description="% do valor FIPE — alerta acima desse limite"),
    ano_mes:         Optional[str] = Query(default=None),
):
    """
    Veículos cujo TCO acumulado no mês ultrapassa X% do valor FIPE.
    Útil para decisão de renovação da frota.
    """
    veiculos = get_por_veiculo(ano_mes=ano_mes, filial=None, grupo=None, limit=500)

    alertas = [
        v for v in veiculos
        if v.get("pct_custo_vs_fipe") is not None and v["pct_custo_vs_fipe"] >= pct_fipe_limite
    ]
    alertas.sort(key=lambda x: x["pct_custo_vs_fipe"], reverse=True)
    return alertas
