"""
Visão Operacional — Diretor de Operações
5 Regras de negócio: custo/km diesel por filial, flags de ação, etanol×gasolina, ANP.
"""
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from anp_client import get_anp_df
from data_cache import cache
from db_sqlserver import get_veiculos_df

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/operacional", tags=["operacional"])

META_CUSTO_KM = 0.52  # R$/km — meta padrão diesel

_DIESEL   = ["diesel s10", "diesel s-10", "diesel s500", "diesel"]
_GASOLINA = ["gasolina", "gasolina comum", "gasolina aditivada", "gasolina c", "gasolina podium", "gasolina v-power"]
_ETANOL   = ["etanol", "álcool", "alcool", "etanol hidratado"]


def _familia(nome: str) -> Optional[str]:
    n = nome.lower()
    if any(k in n for k in _DIESEL):
        return "diesel"
    if any(k in n for k in _GASOLINA):
        return "gasolina"
    if any(k in n for k in _ETANOL):
        return "etanol"
    return None


def _calcular_km(df: pd.DataFrame) -> pd.DataFrame:
    """km_rodado = diferença de hodômetro entre abastecimentos consecutivos por placa."""
    df = df.copy()
    if "hodometro" not in df.columns:
        df["km_rodado"] = None
        return df
    df = df.sort_values(["placa", "data_transacao"])
    df["km_rodado"] = df.groupby("placa")["hodometro"].diff()
    invalido = df["km_rodado"].isna() | (df["km_rodado"] <= 0) | (df["km_rodado"] > 2000)
    df.loc[invalido, "km_rodado"] = None
    return df


def _get_filial_map() -> dict:
    try:
        v = get_veiculos_df()
        return v.set_index("Placa")["FilialOperacional"].dropna().to_dict() if not v.empty else {}
    except Exception as e:
        logger.warning(f"BlueFleet indisponível: {e}")
        return {}


def _add_filial(df: pd.DataFrame, filial_map: dict) -> pd.DataFrame:
    df = df.copy()
    df["placa_norm"] = df["placa"].str.upper().str.replace("-", "", regex=False).str.strip()
    df["filial"] = df["placa_norm"].map(filial_map).fillna("Sem filial")
    return df


def _agg_km(grupo: pd.DataFrame):
    """Agrega total_km e custo_km de um grupo que já tem km_rodado calculado."""
    km_valido = grupo[grupo["km_rodado"].notna()]
    total_km = float(km_valido["km_rodado"].sum()) if not km_valido.empty else None
    total_valor = float(grupo["valor"].sum())
    total_litros = float(grupo["litragem"].sum())
    custo_km = round(total_valor / total_km, 4) if total_km else None
    km_litro = round(total_km / float(km_valido["litragem"].sum()), 2) if total_km and km_valido["litragem"].sum() > 0 else None
    preco_litro = round(total_valor / total_litros, 4) if total_litros > 0 else None
    return total_valor, total_litros, total_km, custo_km, km_litro, preco_litro


# ---------------------------------------------------------------------------
# REGRA 2/5: KPIs Diesel — 4 cartões do diretor
# ---------------------------------------------------------------------------

@router.get("/kpis-diesel")
def get_kpis_diesel(meta_custo_km: float = Query(default=META_CUSTO_KM)):
    """Custo total diesel | custo/km | km/L | economia vs ANP."""
    df = cache.get_df().copy()
    df["familia"] = df["nome_combustivel"].apply(_familia)
    df_d = df[df["familia"] == "diesel"].copy()

    if df_d.empty:
        return {}

    df_d = _calcular_km(df_d)
    tv, tl, tk, ck, kl, pl = _agg_km(df_d)

    # Economia vs ANP Diesel
    economia_anp = None
    preco_anp = None
    try:
        anp = get_anp_df()
        if not anp.empty:
            d_anp = anp[anp["produto"].str.contains("DIESEL", case=False, na=False)]
            if not d_anp.empty:
                preco_anp = float(d_anp["preco"].mean())
                economia_anp = round((preco_anp - pl) * tl, 2) if pl else None
    except Exception:
        pass

    pct_meta = round((ck - meta_custo_km) / meta_custo_km * 100, 1) if ck else None

    return {
        "total_valor_diesel": round(tv, 2),
        "total_litros_diesel": round(tl, 0),
        "total_km": round(tk, 0) if tk else None,
        "custo_km": ck,
        "km_litro": kl,
        "preco_litro": pl,
        "meta_custo_km": meta_custo_km,
        "pct_vs_meta": pct_meta,
        "status_meta": "OK" if ck and ck <= meta_custo_km else "ACIMA" if ck else "SEM_KM",
        "economia_anp": economia_anp,
        "preco_anp_referencia": round(preco_anp, 4) if preco_anp else None,
        "tem_km": tk is not None,
    }


# ---------------------------------------------------------------------------
# REGRA 1/5: Custo/km por filial — gráfico de barras
# ---------------------------------------------------------------------------

@router.get("/custo-por-filial")
def get_custo_por_filial(
    familia: str = Query(default="diesel"),
    meta_custo_km: float = Query(default=META_CUSTO_KM),
):
    """Custo/km e km/L por filial. Flag: ACAO se >10% acima da média."""
    df = cache.get_df().copy()
    df["familia"] = df["nome_combustivel"].apply(_familia)
    df = df[df["familia"] == familia].copy()

    if df.empty:
        return []

    filial_map = _get_filial_map()
    df = _add_filial(df, filial_map)
    df = _calcular_km(df)

    resultado = []
    for filial, g in df.groupby("filial"):
        tv, tl, tk, ck, kl, pl = _agg_km(g)
        resultado.append({
            "filial": filial,
            "total_valor": round(tv, 2),
            "total_litros": round(tl, 0),
            "total_km": round(tk, 0) if tk else None,
            "custo_km": ck,
            "km_litro": kl,
            "preco_litro": pl,
            "qtd_veiculos": int(g["placa"].nunique()),
            "qtd_abastecimentos": int(len(g)),
        })

    resultado.sort(key=lambda x: x["custo_km"] or 0, reverse=True)

    custo_kms = [r["custo_km"] for r in resultado if r["custo_km"]]
    media = sum(custo_kms) / len(custo_kms) if custo_kms else 0

    for r in resultado:
        ck = r["custo_km"]
        if ck is None:
            r["flag"] = "SEM_KM"
            r["pct_vs_media"] = None
            r["pct_vs_meta"] = None
        else:
            r["pct_vs_media"] = round((ck - media) / media * 100, 1) if media else 0
            r["pct_vs_meta"] = round((ck - meta_custo_km) / meta_custo_km * 100, 1)
            r["flag"] = "ACAO" if ck > media * 1.10 else "ATENCAO" if ck > meta_custo_km else "OK"

    return resultado


# ---------------------------------------------------------------------------
# REGRA 2/5: Evolução mensal custo/km — gráfico de linha
# ---------------------------------------------------------------------------

@router.get("/evolucao-mensal")
def get_evolucao_mensal(familia: str = Query(default="diesel")):
    """Evolução mensal de custo/km e km/L para gráfico de tendência."""
    df = cache.get_df().copy()
    df["familia"] = df["nome_combustivel"].apply(_familia)
    df = df[df["familia"] == familia].copy()

    if df.empty:
        return []

    df = _calcular_km(df)
    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    resultado = []
    for mes in sorted(df["ano_mes"].unique()):
        g = df[df["ano_mes"] == mes]
        tv, tl, tk, ck, kl, pl = _agg_km(g)
        resultado.append({
            "ano_mes": mes,
            "total_valor": round(tv, 2),
            "total_litros": round(tl, 0),
            "total_km": round(tk, 0) if tk else None,
            "custo_km": ck,
            "km_litro": kl,
            "preco_litro": pl,
        })

    return resultado


# ---------------------------------------------------------------------------
# REGRA 4/5: Veículos para ação urgente
# ---------------------------------------------------------------------------

@router.get("/veiculos-acao")
def get_veiculos_acao(limit: int = Query(default=20, le=100)):
    """
    FLAG VERMELHO: custo/km > média+10% OU km/L < média-15%.
    Retorna lista ordenada por urgência com economia possível.
    """
    df = cache.get_df().copy()
    df["familia"] = df["nome_combustivel"].apply(_familia)
    df = df[df["familia"] == "diesel"].copy()

    if df.empty:
        return {"veiculos": [], "resumo": {}}

    filial_map = _get_filial_map()
    df = _add_filial(df, filial_map)
    df = _calcular_km(df)

    veiculos = []
    for placa, g in df.groupby("placa"):
        tv, tl, tk, ck, kl, pl = _agg_km(g)
        if tk is None:
            continue

        filial = g["filial"].mode().iloc[0] if not g["filial"].mode().empty else "Sem filial"
        motorista = g["motorista"].dropna().mode()
        modelo = g["modelo_veiculo"].dropna().mode()

        veiculos.append({
            "placa": placa,
            "filial": filial,
            "motorista": motorista.iloc[0] if not motorista.empty else "",
            "modelo": modelo.iloc[0] if not modelo.empty else "",
            "custo_km": ck,
            "km_litro": kl,
            "total_valor": round(tv, 2),
            "total_km": round(tk, 0),
            "total_litros": round(tl, 0),
            "qtd_abastecimentos": int(len(g)),
        })

    if not veiculos:
        return {"veiculos": [], "resumo": {}}

    custo_kms = [v["custo_km"] for v in veiculos]
    km_litros = [v["km_litro"] for v in veiculos if v["km_litro"]]
    media_ck = sum(custo_kms) / len(custo_kms)
    media_kl = sum(km_litros) / len(km_litros) if km_litros else None

    for v in veiculos:
        flags = []
        if v["custo_km"] > media_ck * 1.10:
            flags.append("ALTO_CUSTO")
        if v["km_litro"] and media_kl and v["km_litro"] < media_kl * 0.85:
            flags.append("BAIXO_RENDIMENTO")
        v["flag"] = "CRITICO" if len(flags) > 1 else flags[0] if flags else "OK"
        v["pct_vs_media"] = round((v["custo_km"] - media_ck) / media_ck * 100, 1)
        v["economia_possivel"] = round((v["custo_km"] - media_ck) * v["total_km"], 2) if v["flag"] != "OK" else 0

    acao = [v for v in veiculos if v["flag"] != "OK"]
    acao.sort(key=lambda x: abs(x["pct_vs_media"]), reverse=True)

    return {
        "veiculos": acao[:limit],
        "resumo": {
            "total_frota": len(veiculos),
            "total_acao": len(acao),
            "media_custo_km": round(media_ck, 4),
            "media_km_litro": round(media_kl, 2) if media_kl else None,
            "meta_custo_km": META_CUSTO_KM,
            "economia_total_possivel": round(sum(v["economia_possivel"] for v in acao), 2),
        },
    }


# ---------------------------------------------------------------------------
# REGRA 3/5: Etanol vs Gasolina por filial — decisão inteligente
# ---------------------------------------------------------------------------

@router.get("/etanol-gasolina-filial")
def get_etanol_gasolina_filial():
    """
    Por filial: custo/km (ou preço/L) de gasolina vs etanol.
    Recomenda melhor opção e calcula economia potencial.
    Fallback: regra 70% (etanol < 70% gasolina → etanol vale).
    """
    df = cache.get_df().copy()
    df["familia"] = df["nome_combustivel"].apply(_familia)
    df = df[df["familia"].isin(["gasolina", "etanol"])].copy()

    if df.empty:
        return []

    filial_map = _get_filial_map()
    df = _add_filial(df, filial_map)
    df = _calcular_km(df)

    resultado = []
    for filial, gf in df.groupby("filial"):
        row: dict = {"filial": filial}
        for fam in ["gasolina", "etanol"]:
            g = gf[gf["familia"] == fam]
            if g.empty:
                row[f"custo_km_{fam}"] = None
                row[f"km_litro_{fam}"] = None
                row[f"preco_litro_{fam}"] = None
                row[f"total_litros_{fam}"] = 0
                continue
            tv, tl, tk, ck, kl, pl = _agg_km(g)
            row[f"custo_km_{fam}"] = ck
            row[f"km_litro_{fam}"] = kl
            row[f"preco_litro_{fam}"] = pl
            row[f"total_litros_{fam}"] = round(tl, 0)

        # Decisão
        ck_g = row.get("custo_km_gasolina")
        ck_e = row.get("custo_km_etanol")
        pl_g = row.get("preco_litro_gasolina")
        pl_e = row.get("preco_litro_etanol")

        if ck_g is not None and ck_e is not None:
            row["melhor_opcao"] = "ETANOL" if ck_e < ck_g else "GASOLINA"
            row["economia_km"] = round(abs(ck_g - ck_e), 4)
            row["metodo"] = "custo_km"
        elif pl_g is not None and pl_e is not None:
            row["melhor_opcao"] = "ETANOL" if pl_e < pl_g * 0.70 else "GASOLINA"
            row["economia_km"] = None
            row["metodo"] = "preco_litro_70pct"
        else:
            row["melhor_opcao"] = None
            row["economia_km"] = None
            row["metodo"] = "insuficiente"

        resultado.append(row)

    resultado.sort(key=lambda x: x["filial"])
    return resultado
