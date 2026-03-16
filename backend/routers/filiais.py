"""
KPIs por Filial, Estado e Região.
Usa as colunas filial_nome / filial_estado / filial_regiao do cache enriquecido.
"""
import logging
from datetime import datetime
from typing import Annotated, Optional

import pandas as pd
from fastapi import APIRouter, Query

from data_cache import cache
from config import REGIOES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/filiais", tags=["filiais"])


def _kpis_grupo(df: pd.DataFrame, label: str, valor: str) -> dict:
    """
    Calcula KPIs de um agrupamento de transações.
    Retorna dict com gasto, litros, preço médio, KM/L, custo/km.
    """
    if df.empty:
        return {
            "nome": label, "agrupamento": valor,
            "valor_total": 0, "litros_total": 0,
            "preco_medio_l": None, "km_total": None,
            "km_l": None, "custo_km": None,
            "qtd_abastecimentos": 0, "placas_ativas": 0,
        }

    valor_total = float(df["valor"].sum())
    litros_total = float(df["litragem"].sum())
    preco_medio = round(valor_total / litros_total, 4) if litros_total > 0 else None

    # KM rodado via hodômetro (diff por placa)
    km_total = None
    custo_km = None
    km_l = None
    try:
        df_ord = df.sort_values(["placa", "data_transacao"])
        df_ord = df_ord[df_ord["hodometro"] > 0].copy()
        df_ord["km_diff"] = df_ord.groupby("placa")["hodometro"].diff()
        validos = df_ord[(df_ord["km_diff"] > 0) & (df_ord["km_diff"] < 2000)]
        if not validos.empty:
            km_total = float(validos["km_diff"].sum())
            if km_total > 0:
                custo_km = round(valor_total / km_total, 4)
                km_l = round(km_total / litros_total, 3) if litros_total > 0 else None
    except Exception as e:
        logger.warning(f"KM calc ({label}): {e}")

    return {
        "nome":               label,
        "agrupamento":        valor,
        "valor_total":        round(valor_total, 2),
        "litros_total":       round(litros_total, 2),
        "preco_medio_l":      preco_medio,
        "km_total":           round(km_total, 0) if km_total else None,
        "km_l":               km_l,
        "custo_km":           custo_km,
        "qtd_abastecimentos": int(len(df)),
        "placas_ativas":      int(df["placa"].nunique()),
    }


def _filtrar_periodo(df: pd.DataFrame, mes, ano) -> pd.DataFrame:
    hoje = datetime.now()
    m = int(mes) if mes and str(mes).isdigit() else hoje.month
    a = int(ano) if ano and str(ano).isdigit() else hoje.year
    return df[(df["data_transacao"].dt.month == m) & (df["data_transacao"].dt.year == a)]


def _periodo_str(mes, ano) -> str:
    hoje = datetime.now()
    m = int(mes) if mes and str(mes).isdigit() else hoje.month
    a = int(ano) if ano and str(ano).isdigit() else hoje.year
    return f"{a}-{m:02d}"


@router.get("/resumo")
def get_resumo_filiais(
    mes: Annotated[Optional[int], Query(ge=1, le=12)] = None,
    ano: Annotated[Optional[int], Query(ge=2020)] = None,
    regiao: Optional[str] = None,
    estado: Optional[str] = None,
):
    """
    KPIs consolidados por filial no período.
    Filtros opcionais: regiao, estado.
    """
    try:
        df = cache.get_df()
        df = _filtrar_periodo(df, mes, ano)
        df = df[df["filial_nome"] != ""]

        if regiao:
            df = df[df["filial_regiao"] == regiao]
        if estado:
            df = df[df["filial_estado"] == estado]

        if df.empty:
            return {"filiais": [], "periodo": _periodo_str(mes, ano)}

        filiais = []
        for filial_nome, grupo in df.groupby("filial_nome"):
            estado_filial = grupo["filial_estado"].iloc[0]
            regiao_filial = grupo["filial_regiao"].iloc[0]
            kpis = _kpis_grupo(grupo, filial_nome, filial_nome)
            kpis["estado"] = estado_filial
            kpis["regiao"] = regiao_filial

            # Preço médio por grupo de combustível (comparação justa)
            preco_por_grupo = {}
            for grp_nome, grp_df in grupo.groupby("grupo_combustivel"):
                litros = float(grp_df["litragem"].sum())
                valor = float(grp_df["valor"].sum())
                if litros > 0:
                    preco_por_grupo[grp_nome] = round(valor / litros, 4)

            # Mix de gasto por combustível (%)
            mix_pct = (
                grupo.groupby("grupo_combustivel")["valor"]
                .sum()
                .apply(lambda v: round(float(v) / kpis["valor_total"] * 100, 1) if kpis["valor_total"] else 0)
                .to_dict()
            )
            kpis["preco_por_grupo"] = preco_por_grupo
            kpis["mix_combustivel"] = mix_pct
            # Remove preco_medio_l blended — usar preco_por_grupo para comparações
            kpis.pop("preco_medio_l", None)
            filiais.append(kpis)

        filiais.sort(key=lambda x: x["valor_total"], reverse=True)

        # Total geral do período (filtrado)
        total = _kpis_grupo(df, "TOTAL", "geral")

        hoje = datetime.now()
        return {
            "filiais": filiais,
            "total":   total,
            "periodo": _periodo_str(mes, ano),
        }

    except Exception as e:
        logger.error(f"Filiais (resumo): {e}")
        return {"error": str(e)}


@router.get("/por-regiao")
def get_por_regiao(
    mes: Annotated[Optional[int], Query(ge=1, le=12)] = None,
    ano: Annotated[Optional[int], Query(ge=2020)] = None,
):
    """KPIs agrupados por região geográfica."""
    try:
        df = cache.get_df()
        df = _filtrar_periodo(df, mes, ano)
        df = df[df["filial_regiao"] != ""]

        regioes = []
        for regiao, grupo in df.groupby("filial_regiao"):
            kpis = _kpis_grupo(grupo, regiao, regiao)
            kpis["filiais_ativas"] = int(grupo["filial_nome"].nunique())
            kpis["pct_valor_total"] = 0  # preenchido abaixo
            regioes.append(kpis)

        total_valor = sum(r["valor_total"] for r in regioes)
        for r in regioes:
            r["pct_valor_total"] = round(r["valor_total"] / total_valor * 100, 1) if total_valor else 0

        regioes.sort(key=lambda x: x["valor_total"], reverse=True)

        hoje = datetime.now()
        return {
            "regioes": regioes,
            "periodo": _periodo_str(mes, ano),
        }

    except Exception as e:
        logger.error(f"Filiais (por-regiao): {e}")
        return {"error": str(e)}


@router.get("/por-estado")
def get_por_estado(
    mes: Annotated[Optional[int], Query(ge=1, le=12)] = None,
    ano: Annotated[Optional[int], Query(ge=2020)] = None,
    regiao: Optional[str] = None,
):
    """KPIs agrupados por estado (UF)."""
    try:
        df = cache.get_df()
        df = _filtrar_periodo(df, mes, ano)
        df = df[df["filial_estado"] != ""]

        if regiao:
            df = df[df["filial_regiao"] == regiao]

        estados = []
        for estado, grupo in df.groupby("filial_estado"):
            regiao_est = grupo["filial_regiao"].iloc[0]
            kpis = _kpis_grupo(grupo, estado, estado)
            kpis["regiao"] = regiao_est
            kpis["filiais_ativas"] = int(grupo["filial_nome"].nunique())
            estados.append(kpis)

        total_valor = sum(e["valor_total"] for e in estados)
        for e in estados:
            e["pct_valor_total"] = round(e["valor_total"] / total_valor * 100, 1) if total_valor else 0

        estados.sort(key=lambda x: x["valor_total"], reverse=True)

        hoje = datetime.now()
        return {
            "estados": estados,
            "periodo": _periodo_str(mes, ano),
        }

    except Exception as e:
        logger.error(f"Filiais (por-estado): {e}")
        return {"error": str(e)}


@router.get("/evolucao")
def get_evolucao_filial(
    filial: str = Query(..., description="Nome da filial (ex: Gritsch Curitiba)"),
    meses: int = Query(6, ge=1, le=12),
):
    """Evolução mensal de gasto e eficiência de uma filial específica."""
    try:
        df = cache.get_df()
        df = df[df["filial_nome"] == filial]
        if df.empty:
            return {"filial": filial, "historico": []}

        hoje = datetime.now()
        historico = []
        for i in range(meses - 1, -1, -1):
            periodo = hoje - pd.DateOffset(months=i)
            df_m = df[
                (df["data_transacao"].dt.month == periodo.month) &
                (df["data_transacao"].dt.year == periodo.year)
            ]
            kpis = _kpis_grupo(df_m, filial, f"{periodo.year}-{periodo.month:02d}")
            kpis["mes"] = f"{periodo.year}-{periodo.month:02d}"
            historico.append(kpis)

        return {"filial": filial, "historico": historico}

    except Exception as e:
        logger.error(f"Filiais (evolucao): {e}")
        return {"error": str(e)}


@router.get("/comparativo")
def get_comparativo_filiais(
    mes: Annotated[Optional[int], Query(ge=1, le=12)] = None,
    ano: Annotated[Optional[int], Query(ge=2020)] = None,
    metrica: str = "valor_total",
    grupo_combustivel: Optional[str] = None,
):
    """
    Ranking de filiais por uma métrica.

    Para métricas de preço (preco_medio_l), use o filtro grupo_combustivel
    para garantir comparação justa entre filiais — Diesel vs Diesel, Gasolina vs Gasolina.

    Grupos válidos: Diesel, Gasolina, Álcool, Arla
    """
    try:
        df = cache.get_df()
        df = _filtrar_periodo(df, mes, ano)
        df = df[df["filial_nome"] != ""]

        metricas_validas = {"valor_total", "preco_medio_l", "km_l", "custo_km"}
        if metrica not in metricas_validas:
            return {"error": f"Métrica inválida. Use: {metricas_validas}"}

        # Para preco_medio_l sem filtro de grupo, retorna aviso
        if metrica == "preco_medio_l" and not grupo_combustivel:
            return {
                "aviso": (
                    "Para comparar preço entre filiais, informe o grupo_combustivel. "
                    "Comparar médias de filiais com mix de combustível diferente não é significativo. "
                    "Use: grupo_combustivel=Diesel | Gasolina | Álcool"
                ),
                "grupos_disponiveis": sorted(df["grupo_combustivel"].unique().tolist()),
                "filiais": [],
                "metrica": metrica,
                "periodo": _periodo_str(mes, ano),
            }

        # Filtra por grupo se informado
        if grupo_combustivel:
            df = df[df["grupo_combustivel"] == grupo_combustivel]
            if df.empty:
                return {
                    "filiais": [], "metrica": metrica,
                    "grupo_combustivel": grupo_combustivel,
                    "periodo": _periodo_str(mes, ano),
                }

        filiais = []
        for filial_nome, grupo in df.groupby("filial_nome"):
            kpis = _kpis_grupo(grupo, filial_nome, filial_nome)
            kpis["estado"] = grupo["filial_estado"].iloc[0]
            kpis["regiao"] = grupo["filial_regiao"].iloc[0]
            # Inclui o grupo filtrado para clareza
            if grupo_combustivel:
                kpis["grupo_combustivel"] = grupo_combustivel
            filiais.append(kpis)

        # Ordena pela métrica (nulls por último, preço: menor = melhor)
        filiais.sort(
            key=lambda x: (x[metrica] is None, x[metrica] if x[metrica] is not None else 0),
            reverse=(metrica != "preco_medio_l"),
        )

        for i, f in enumerate(filiais, 1):
            f["ranking"] = i

        return {
            "filiais":            filiais,
            "metrica":            metrica,
            "grupo_combustivel":  grupo_combustivel,
            "periodo":            _periodo_str(mes, ano),
        }

    except Exception as e:
        logger.error(f"Filiais (comparativo): {e}")
        return {"error": str(e)}
