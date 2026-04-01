"""
Módulo Pneus — Gestão de Pneus da Frota
Fonte: planilha 'Controle de Pneus.xlsx', aba 'Planilha1'.
"""
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from db_pneus import get_pneus_df, refresh_pneus_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pneus", tags=["pneus"])


@router.get("/debug")
def debug_pneus():
    """Endpoint de teste para verificar se o módulo está funcionando."""
    try:
        from db_pneus import get_pneus_df, _get_pneus_path
        df = get_pneus_df()
        path = _get_pneus_path()
        import os
        exists = os.path.exists(path)
        return {
            "status": "ok",
            "linhas": len(df),
            "path": path,
            "file_exists": exists,
            "colunas": list(df.columns) if not df.empty else [],
        }
    except Exception as e:
        return {"status": "error", "erro": str(e)}


def _apply_filters(
    df: pd.DataFrame,
    filial: Optional[str] = None,
    marca: Optional[str] = None,
    fornecedor: Optional[str] = None,
    eixo: Optional[str] = None,
    medida: Optional[str] = None,
    estado_pneu: Optional[str] = None,
    ano: Optional[str] = None,
    aro: Optional[str] = None,
) -> pd.DataFrame:
    df = df.copy()
    if filial:
        df = df[df["filial"] == filial]
    if marca:
        df = df[df["marca"] == marca]
    if fornecedor:
        df = df[df["fornecedor"] == fornecedor]
    if eixo:
        df = df[df["eixo"] == eixo]
    if medida:
        df = df[df["medida"] == medida]
    if estado_pneu:
        df = df[df["estado_pneu"] == estado_pneu]
    if ano:
        try:
            df = df[df["ano"] == float(ano)]
        except:
            pass
    if aro:
        try:
            df = df[df["p22_5"] == float(aro)]
        except:
            pass
    return df


def _safe_round(val, n=2):
    try:
        return round(float(val), n)
    except Exception:
        return None


def _clean_series(series):
    return sorted([v for v in series.dropna().unique().tolist() if v and str(v) != "nan"])


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: filtros disponíveis
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/filtros")
def get_filtros():
    df = get_pneus_df()
    if df.empty:
        return {"filiais": [], "marcas": [], "fornecedores": [], "eixos": [], "medidas": [], "meses": []}

    return {
        "filiais": _clean_series(df["filial"]),
        "marcas": _clean_series(df["marca"]),
        "fornecedores": _clean_series(df["fornecedor"]),
        "eixos": _clean_series(df["eixo"]),
        "medidas": _clean_series(df["medida"]),
        "aros": sorted([float(x) for x in df["p22_5"].dropna().unique() if x and float(x) > 0]),
        "meses": _clean_series(df["mes"]),
        "anos": [int(y) for y in sorted(df["ano"].dropna().unique())],
        "estados_pneu": _clean_series(df["estado_pneu"]),
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: KPIs principais
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis")
def get_kpis(
    filial: Optional[str] = Query(default=None),
    marca: Optional[str] = Query(default=None),
    fornecedor: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return {"total_pneus": 0, "total_valor": 0, "valor_medio": 0, "placas": 0, "fornecedores": 0, "marcas": 0, "filiais": 0}

    df = _apply_filters(df, filial, marca, fornecedor, ano=ano, aro=aro, medida=medida)

    total_pneus = int(df["quan"].sum()) if "quan" in df.columns else len(df)
    total_valor = float(df["total"].sum()) if "total" in df.columns else 0
    valor_medio = total_valor / total_pneus if total_pneus > 0 else 0
    placas = int(df["placa"].nunique()) if "placa" in df.columns else 0
    ticket_medio_veiculo = placas / total_pneus if total_pneus > 0 else 0

    return {
        "total_pneus": total_pneus,
        "total_valor": _safe_round(total_valor, 2),
        "valor_medio": _safe_round(valor_medio, 2),
        "ticket_medio_pneu": _safe_round(valor_medio, 2),
        "ticket_medio_veiculo": _safe_round(ticket_medio_veiculo, 2),
        "placas": placas,
        "fornecedores": int(df["fornecedor"].nunique()) if "fornecedor" in df.columns else 0,
        "marcas": int(df["marca"].nunique()) if "marca" in df.columns else 0,
        "filiais": int(df["filial"].nunique()) if "filial" in df.columns else 0,
        "novos": int(df[df["estado_pneu"] == "NOVO"]["quan"].sum()) if "estado_pneu" in df.columns else 0,
        "recapados": int(df[df["estado_pneu"] == "RECAP"]["quan"].sum()) if "estado_pneu" in df.columns else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: tabela principal
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/tabela")
def get_tabela(
    filial: Optional[str] = Query(default=None),
    marca: Optional[str] = Query(default=None),
    fornecedor: Optional[str] = Query(default=None),
    limit: int = Query(default=200, le=1000),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return {"cols": [], "rows": []}

    df = _apply_filters(df, filial, marca, fornecedor, ano=ano, aro=aro, medida=medida)

    cols = [
        "n_fogo", "dot", "data_envio", "filial", "placa", "veiculo",
        "marca", "modelo", "medida", "eixo", "estado_pneu", "fornecedor", "nf",
        "valor_un", "total",
    ]
    cols = [c for c in cols if c in df.columns]

    rows = df[cols].head(limit).fillna("").to_dict(orient="records")
    return {"cols": cols, "rows": rows}


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: distribuição por filial
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-filial")
def por_filial(
    marca: Optional[str] = Query(default=None),
    fornecedor: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, marca=marca, fornecedor=fornecedor, ano=ano, aro=aro, medida=medida)
    g = df.groupby("filial").agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
    ).reset_index()
    g["valor_medio"] = g["valor"] / g["quantidade"]
    return g.sort_values("valor", ascending=False).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: distribuição por marca
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-marca")
def por_marca(
    filial: Optional[str] = Query(default=None),
    fornecedor: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, fornecedor=fornecedor, ano=ano, aro=aro, medida=medida)
    g = df.groupby("marca").agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
    ).reset_index()
    g["valor_medio"] = g["valor"] / g["quantidade"]
    return g.sort_values("valor", ascending=False).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: distribuição por fornecedor
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-fornecedor")
def por_fornecedor(
    filial: Optional[str] = Query(default=None),
    marca: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, marca=marca, ano=ano, aro=aro, medida=medida)
    g = df.groupby("fornecedor").agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
    ).reset_index()
    g["percentual"] = (g["valor"] / g["valor"].sum() * 100).round(1)
    return g.sort_values("valor", ascending=False).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: distribuição por eixo
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-eixo")
def por_eixo(
    filial: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, ano=ano, aro=aro, medida=medida)
    g = df.groupby("eixo").agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
        valor_medio=("valor_un", "mean"),
    ).reset_index()
    return g.sort_values("quantidade", ascending=False).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: distribuição por medida
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-medida")
def por_medida(
    filial: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, ano=ano, aro=aro)
    df = df.copy()
    df["aro"] = df["medida"].astype(str).str.split("/").str[-1].str.strip()
    df["aro"] = df["aro"].replace(["", "nan", "-"], "N/I")
    
    g = df.groupby("aro").agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
    ).reset_index()
    g["medida"] = "Aro " + g["aro"]
    return g.sort_values("quantidade", ascending=False).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: distribuição por estado (UF)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-estado")
def por_estado(
    filial: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, aro=aro, medida=medida)
    g = df.groupby("estado").agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
    ).reset_index()
    return g.sort_values("valor", ascending=False).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: distribuição por tipo (Novo vs Recap)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-tipo")
def por_tipo(
    filial: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, ano=ano, aro=aro, medida=medida)
    g = df.groupby("estado_pneu").agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
        valor_medio=("valor_un", "mean"),
    ).reset_index()
    return g.to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: timeline de compras por mês (com comparação por ano)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/timeline")
def timeline(
    ano: Optional[str] = Query(default=None),
    filial: Optional[str] = Query(default=None),
    marca: Optional[str] = Query(default=None),
    fornecedor: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return {"anos": [], "meses": [], "series": []}
    df = _apply_filters(df, filial=filial, marca=marca, fornecedor=fornecedor, aro=aro, medida=medida)

    meses_ordem = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

    g = df.groupby(["ano", "mes"]).agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
    ).reset_index()
    g["mes"] = pd.Categorical(g["mes"], categories=meses_ordem, ordered=True)
    g = g.sort_values(["ano", "mes"])

    # Monta séries por ano
    anos_disponiveis = sorted(g["ano"].unique())
    series = []
    for y in anos_disponiveis:
        dados_ano = g[g["ano"] == y]
        pontos = []
        for m in meses_ordem:
            linha = dados_ano[dados_ano["mes"] == m]
            if len(linha):
                pontos.append({"mes": m, "valor": round(float(linha.iloc[0]["valor"]), 2), "quantidade": int(linha.iloc[0]["quantidade"])})
            else:
                pontos.append({"mes": m, "valor": 0, "quantidade": 0})
        series.append({"ano": int(y) if pd.notna(y) else y, "dados": pontos})

    return {"anos": [int(y) if pd.notna(y) else y for y in anos_disponiveis], "meses": meses_ordem, "series": series}


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: top pneus mais caros
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/top-caros")
def top_caros(
    limit: int = Query(default=10, le=50),
    filial: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, ano=ano, aro=aro, medida=medida)
    cols = ["n_fogo", "marca", "modelo", "filial", "placa", "medida", "eixo", "valor_un", "total", "fornecedor"]
    cols = [c for c in cols if c in df.columns]
    top = df.nlargest(limit, "valor_un")[cols]
    return top.fillna("").to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: ranking de placas (veículos com mais pneus)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/por-placa")
def por_placa(
    filial: Optional[str] = Query(default=None),
    limit: int = Query(default=20, le=100),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, ano=ano, aro=aro, medida=medida)
    g = df.groupby(["placa", "veiculo", "filial"]).agg(
        quantidade=("quan", "sum"),
        valor=("total", "sum"),
    ).reset_index()
    return g.sort_values("quantidade", ascending=False).head(limit).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: refresh cache
# ═══════════════════════════════════════════════════════════════════════════
@router.post("/cache/refresh")
def refresh_cache():
    return refresh_pneus_cache()
