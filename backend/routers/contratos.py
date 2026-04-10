import logging
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Query

from db_fkm import get_fkm_df
from utils import safe_round

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contratos", tags=["contratos"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _ultimo_mes(df: pd.DataFrame) -> Optional[str]:
    if df.empty:
        return None
    meses = sorted(df["ano_mes"].dropna().unique().tolist())
    return meses[-1] if meses else None


def _get_df_filtrado(ano_mes: Optional[str], contrato: Optional[str]) -> pd.DataFrame:
    df = get_fkm_df()
    if df.empty:
        return df
    if not ano_mes:
        ano_mes = _ultimo_mes(df)
    if ano_mes:
        df = df[df["ano_mes"] == ano_mes]
    if contrato:
        df = df[df["contrato"] == contrato]
    # Remove linhas sem contrato válido
    df = df[df["contrato"].notna() & (df["contrato"] != "") & (df["contrato"] != "nan")]
    return df


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Filtros disponíveis
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/filtros")
def get_filtros():
    """Lista de contratos disponíveis com metadata (meses ativos, filiais, qtd veículos)."""
    df = get_fkm_df()
    df = df[df["contrato"].notna() & (df["contrato"] != "") & (df["contrato"] != "nan")]

    if df.empty:
        return []

    resultado = []
    for contrato, g in df.groupby("contrato"):
        meses   = sorted(g["ano_mes"].dropna().unique().tolist())
        filiais = sorted(g["filial"].dropna().unique().tolist())
        resultado.append({
            "contrato":     contrato,
            "qtd_veiculos": int(g["placa"].nunique()),
            "meses_ativos": len(meses),
            "primeiro_mes": meses[0] if meses else None,
            "ultimo_mes":   meses[-1] if meses else None,
            "filiais":      filiais,
        })

    resultado.sort(key=lambda x: x["qtd_veiculos"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: KPIs por Contrato
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis")
def get_kpis(
    ano_mes:  Optional[str] = Query(default=None),
    contrato: Optional[str] = Query(default=None),
):
    """KPIs consolidados por contrato (custo total, custo/km, km/l, breakdown de categorias)."""
    df = _get_df_filtrado(ano_mes, contrato)

    if df.empty:
        return []

    resultado = []
    for nome, g in df.groupby("contrato"):
        total_km     = float(g["total_km"].sum())
        total_litros = float(g["litros_comb"].sum())
        custo_comb   = float(g["valor_comb"].sum())
        custo_man    = float(g["manutencao"].sum())
        custo_pneus  = float(g["rodas_pneus"].sum())
        custo_lataria= float(g["lataria_pintura"].sum())
        custo_arla   = float(g["arla"].sum())
        custo_total  = float(g["total"].sum())

        resultado.append({
            "contrato":        nome,
            "ano_mes":         ano_mes or _ultimo_mes(get_fkm_df()),
            "qtd_veiculos":    int(g["placa"].nunique()),
            "total_km":        safe_round(total_km, 0),
            "total_litros":    safe_round(total_litros, 0),
            "custo_combustivel": safe_round(custo_comb, 2),
            "custo_manutencao":  safe_round(custo_man, 2),
            "custo_pneus":       safe_round(custo_pneus, 2),
            "custo_lataria":     safe_round(custo_lataria, 2),
            "custo_arla":        safe_round(custo_arla, 2),
            "custo_total":       safe_round(custo_total, 2),
            "custo_km":  safe_round(custo_total / total_km, 2) if total_km > 0 else 0,
            "media_kml": safe_round(total_km / total_litros, 2) if total_litros > 0 else 0,
            "pct_combustivel": safe_round(custo_comb / custo_total * 100, 1) if custo_total > 0 else 0,
            "pct_manutencao":  safe_round(custo_man / custo_total * 100, 1) if custo_total > 0 else 0,
        })

    resultado.sort(key=lambda x: x["custo_total"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Resumo de todos os contratos
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/resumo")
def get_resumo(ano_mes: Optional[str] = Query(default=None)):
    """Ranking de todos os contratos por custo total no mês selecionado."""
    df = get_fkm_df()
    df = df[df["contrato"].notna() & (df["contrato"] != "") & (df["contrato"] != "nan")]

    if df.empty:
        return []

    if not ano_mes:
        ano_mes = _ultimo_mes(df)
    df = df[df["ano_mes"] == ano_mes]

    if df.empty:
        return []

    resumo = []
    for contrato, g in df.groupby("contrato"):
        total_km    = float(g["total_km"].sum())
        custo_total = float(g["total"].sum())
        filiais     = g["filial"].dropna().unique().tolist()
        grupos      = g["grupo_veiculo"].dropna().unique().tolist()

        resumo.append({
            "contrato":     contrato,
            "custo_total":  safe_round(custo_total, 2),
            "custo_km":     safe_round(custo_total / total_km, 2) if total_km > 0 else 0,
            "total_km":     safe_round(total_km, 0),
            "qtd_veiculos": int(g["placa"].nunique()),
            "filial_principal": filiais[0] if filiais else None,
            "grupos": grupos,
        })

    resumo.sort(key=lambda x: x["custo_total"], reverse=True)
    return resumo


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Evolução mensal de um contrato
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/historico")
def get_historico(contrato: str = Query(...)):
    """Evolução mensal de um contrato específico."""
    df = get_fkm_df()
    df = df[df["contrato"] == contrato]

    if df.empty:
        return []

    evolucao = (
        df.groupby("ano_mes")
        .agg(
            total_km=("total_km", "sum"),
            total_valor=("total", "sum"),
            custo_combustivel=("valor_comb", "sum"),
            custo_manutencao=("manutencao", "sum"),
            qtd_veiculos=("placa", "nunique"),
        )
        .reset_index()
        .sort_values("ano_mes")
    )

    res = evolucao.to_dict(orient="records")
    for r in res:
        km = r["total_km"]
        r["custo_km"]  = safe_round(r["total_valor"] / km, 2) if km > 0 else 0
        r["total_km"]  = safe_round(km, 0)
        r["total_valor"]         = safe_round(r["total_valor"], 2)
        r["custo_combustivel"]   = safe_round(r["custo_combustivel"], 2)
        r["custo_manutencao"]    = safe_round(r["custo_manutencao"], 2)
    return res


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Veículos de um contrato
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/veiculos/{contrato}")
def get_veiculos(
    contrato: str,
    ano_mes:  Optional[str] = Query(default=None),
):
    """Veículos alocados a um contrato no mês selecionado, com métricas individuais."""
    df = get_fkm_df()
    df = df[df["contrato"] == contrato]

    if df.empty:
        return []

    if not ano_mes:
        ano_mes = _ultimo_mes(df)
    df = df[df["ano_mes"] == ano_mes]

    if df.empty:
        return []

    resultado = []
    for _, row in df.iterrows():
        km    = float(row.get("total_km", 0))
        litros = float(row.get("litros_comb", 0))
        custo = float(row.get("total", 0))
        resultado.append({
            "placa":              str(row.get("placa", "")),
            "modelo":             str(row.get("modelo_simplificado", "")),
            "grupo":              str(row.get("grupo_veiculo", "")),
            "filial":             str(row.get("filial", "")),
            "motorista":          str(row.get("motorista_principal", "")),
            "total_km":           safe_round(km, 0),
            "litros_comb":        safe_round(litros, 0),
            "custo_combustivel":  safe_round(float(row.get("valor_comb", 0)), 2),
            "custo_manutencao":   safe_round(float(row.get("manutencao", 0)), 2),
            "custo_total":        safe_round(custo, 2),
            "custo_km":           safe_round(custo / km, 2) if km > 0 else 0,
            "media_kml":          safe_round(km / litros, 2) if litros > 0 else 0,
        })

    resultado.sort(key=lambda x: x["custo_total"], reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Comparativo entre contratos
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/comparativo")
def get_comparativo(ano_mes: Optional[str] = Query(default=None)):
    """Comparação lado a lado de todos os contratos: custo/km, km/l, total, veículos."""
    df = get_fkm_df()
    df = df[df["contrato"].notna() & (df["contrato"] != "") & (df["contrato"] != "nan")]

    if df.empty:
        return []

    if not ano_mes:
        ano_mes = _ultimo_mes(df)
    df = df[df["ano_mes"] == ano_mes]

    if df.empty:
        return []

    comparativo = []
    for contrato, g in df.groupby("contrato"):
        total_km    = float(g["total_km"].sum())
        total_litros= float(g["litros_comb"].sum())
        custo_total = float(g["total"].sum())
        custo_comb  = float(g["valor_comb"].sum())
        custo_man   = float(g["manutencao"].sum()) + float(g["rodas_pneus"].sum()) + float(g["lataria_pintura"].sum())

        comparativo.append({
            "contrato":     contrato,
            "custo_total":  safe_round(custo_total, 2),
            "custo_km":     safe_round(custo_total / total_km, 2) if total_km > 0 else 0,
            "media_kml":    safe_round(total_km / total_litros, 2) if total_litros > 0 else 0,
            "total_km":     safe_round(total_km, 0),
            "qtd_veiculos": int(g["placa"].nunique()),
            "pct_comb":     safe_round(custo_comb / custo_total * 100, 1) if custo_total > 0 else 0,
            "pct_manut":    safe_round(custo_man / custo_total * 100, 1) if custo_total > 0 else 0,
        })

    comparativo.sort(key=lambda x: x["custo_total"], reverse=True)
    return comparativo
