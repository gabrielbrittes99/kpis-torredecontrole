"""
Visão Operacional — Acompanhamento de Frota
Custo/KM por grupo de veículo, filial e região.
Alertas comparando cada veículo com os pares do seu grupo.
"""
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from anp_client import get_anp_df
from config import get_kml_referencia, KML_REFERENCIA
from data_cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/operacional", tags=["operacional"])

# ── Famílias de combustível ──────────────────────────────────────────────────
_DIESEL   = ["diesel s10", "diesel s-10", "diesel s500", "diesel"]
_GASOLINA = ["gasolina", "gasolina comum", "gasolina aditivada", "gasolina c",
             "gasolina podium", "gasolina v-power"]
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


# ── Cálculo de KM rodado ────────────────────────────────────────────────────
def _calcular_km(df: pd.DataFrame) -> pd.DataFrame:
    """km_rodado = diff hodômetro entre abastecimentos consecutivos por placa."""
    df = df.copy()
    if "hodometro" not in df.columns:
        df["km_rodado"] = None
        return df
    df = df.sort_values(["placa", "data_transacao"])
    df["km_rodado"] = df.groupby("placa")["hodometro"].diff()
    invalido = df["km_rodado"].isna() | (df["km_rodado"] <= 0) | (df["km_rodado"] > 2000)
    df.loc[invalido, "km_rodado"] = None
    return df


# ── Agregação de métricas ───────────────────────────────────────────────────
def _agg_km(grupo: pd.DataFrame):
    """
    Retorna: total_valor, total_litros, total_km, custo_km, km_litro, preco_litro
    custo_km e km_litro só consideram registros com hodômetro válido.
    """
    total_valor = float(grupo["valor"].sum())
    total_litros = float(grupo["litragem"].sum())

    km_valido = grupo[grupo["km_rodado"].notna()].copy()
    total_km = float(km_valido["km_rodado"].sum()) if not km_valido.empty else None

    if total_km and total_km > 0:
        valor_para_km = float(km_valido["valor"].sum())
        litros_para_km = float(km_valido["litragem"].sum())
        custo_km = round(valor_para_km / total_km, 4)
        km_litro = round(total_km / litros_para_km, 2) if litros_para_km > 0 else None
    else:
        custo_km = None
        km_litro = None

    preco_litro = round(total_valor / total_litros, 4) if total_litros > 0 else None
    return total_valor, total_litros, total_km, custo_km, km_litro, preco_litro


# ── Filtros (usa colunas já enriquecidas pelo cache) ────────────────────────
def _apply_filters(
    df: pd.DataFrame,
    modo_tempo: str = "mes",
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    grupo: Optional[str] = None,
    filial: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
) -> pd.DataFrame:
    df = df.copy()

    # 1. Temporais
    if modo_tempo == "mes" and mes and ano:
        df = df[(df["data_transacao"].dt.month == mes) & (df["data_transacao"].dt.year == ano)]
    elif modo_tempo == "bimestre" and bimestre and ano:
        months = [bimestre * 2 - 1, bimestre * 2]
        df = df[(df["data_transacao"].dt.month.isin(months)) & (df["data_transacao"].dt.year == ano)]
    elif modo_tempo == "semestre" and semestre and ano:
        months = list(range(1, 7)) if semestre == 1 else list(range(7, 13))
        df = df[(df["data_transacao"].dt.month.isin(months)) & (df["data_transacao"].dt.year == ano)]
    elif modo_tempo == "ano" and ano:
        df = df[df["data_transacao"].dt.year == ano]
    elif modo_tempo == "personalizado" and data_inicio and data_fim:
        df = df[(df["data_transacao"] >= data_inicio) & (df["data_transacao"] <= data_fim)]
    elif ano:
        df = df[df["data_transacao"].dt.year == ano]

    # 2. Atributos (colunas vindas do cache enriquecido)
    if grupo:
        df = df[df["grupo_veiculo"] == grupo]
    if filial:
        df = df[df["filial_nome"] == filial]
    if estado:
        df = df[df["filial_estado"] == estado]
    if regiao:
        df = df[df["filial_regiao"] == regiao]

    return df


def _filter_familia(df: pd.DataFrame, familia: str) -> pd.DataFrame:
    """Aplica filtro de família de combustível."""
    df["familia"] = df["nome_combustivel"].apply(_familia)
    if familia != "todos":
        return df[df["familia"] == familia].copy()
    return df.copy()


# ── Parâmetros comuns ───────────────────────────────────────────────────────
# (reusados em todos os endpoints)
_COMMON_DOC = "Filtros temporais e de atributo"


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 1: KPIs gerais
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/kpis")
def get_kpis_operacional(
    familia: str = Query(default="todos"),
    modo_tempo: str = Query(default="mes"),
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    grupo: Optional[str] = None,
    filial: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
):
    """KPIs consolidados de frota. Sem meta — apenas acompanhamento."""
    raw_df = cache.get_df()
    df = _apply_filters(raw_df, modo_tempo, ano, mes, bimestre, semestre,
                        data_inicio, data_fim, grupo, filial, estado, regiao)
    df = _filter_familia(df, familia)

    if df.empty:
        return {}

    df = _calcular_km(df)
    tv, tl, tk, ck, kl, pl = _agg_km(df)

    qtd_veiculos = int(df["placa"].nunique())
    qtd_com_km = int(df[df["km_rodado"].notna()]["placa"].nunique()) if tk else 0

    # Economia vs ANP (só faz sentido para família específica)
    economia_anp = None
    preco_anp = None
    if familia != "todos":
        try:
            anp = get_anp_df()
            if not anp.empty:
                prod_map = {"diesel": "DIESEL", "etanol": "ETANOL", "gasolina": "GASOLINA"}
                f_anp = anp[anp["produto"].str.contains(prod_map.get(familia, ""), case=False, na=False)]
                if not f_anp.empty:
                    preco_anp = float(f_anp["preco"].mean())
                    economia_anp = round((preco_anp - pl) * tl, 2) if pl else None
        except Exception:
            pass

    return {
        "total_valor": round(tv, 2),
        "total_litros": round(tl, 0),
        "total_km": round(tk, 0) if tk else None,
        "custo_km": ck,
        "km_litro": kl,
        "preco_litro": pl,
        "qtd_veiculos": qtd_veiculos,
        "qtd_com_km": qtd_com_km,
        "economia_anp": economia_anp,
        "preco_anp_referencia": round(preco_anp, 4) if preco_anp else None,
        "tem_km": tk is not None,
        "familia": familia,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 2: Custo/KM por grupo de veículo
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/custo-por-grupo")
def get_custo_por_grupo(
    familia: str = Query(default="todos"),
    modo_tempo: str = Query(default="mes"),
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    filial: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
):
    """Custo/KM agrupado por tipo de veículo, com referência de km/L."""
    raw_df = cache.get_df()
    df = _apply_filters(raw_df, modo_tempo, ano, mes, bimestre, semestre,
                        data_inicio, data_fim, None, filial, estado, regiao)
    df = _filter_familia(df, familia)

    if df.empty:
        return []

    df = _calcular_km(df)

    resultado = []
    for grp, g in df.groupby("grupo_veiculo"):
        if grp in ("Outros", ""):
            continue
        tv, tl, tk, ck, kl, pl = _agg_km(g)

        # Referência km/L (média rodoviário + urbano)
        # Pega o combustível principal deste grupo
        gc_principal = g["grupo_combustivel"].mode().iloc[0] if not g["grupo_combustivel"].mode().empty else "Diesel"
        kml_ref = get_kml_referencia(grp, gc_principal)
        pct_vs_ref = round((kl - kml_ref) / kml_ref * 100, 1) if kl and kml_ref else None

        resultado.append({
            "grupo": grp,
            "total_valor": round(tv, 2),
            "total_litros": round(tl, 0),
            "total_km": round(tk, 0) if tk else None,
            "custo_km": ck,
            "km_litro": kl,
            "kml_referencia": kml_ref,
            "pct_vs_referencia": pct_vs_ref,
            "preco_litro": pl,
            "qtd_veiculos": int(g["placa"].nunique()),
            "qtd_abastecimentos": int(len(g)),
        })

    # Ordena por custo/km desc (quem gasta mais primeiro)
    resultado.sort(key=lambda x: x["custo_km"] or 0, reverse=True)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 3: Custo/KM por filial
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/custo-por-filial")
def get_custo_por_filial(
    familia: str = Query(default="todos"),
    modo_tempo: str = Query(default="mes"),
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    grupo: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
):
    """Custo/KM por filial. Flags baseadas em desvio da média (sem meta fixa)."""
    raw_df = cache.get_df()
    df = _apply_filters(raw_df, modo_tempo, ano, mes, bimestre, semestre,
                        data_inicio, data_fim, grupo, None, estado, regiao)
    df = _filter_familia(df, familia)

    if df.empty:
        return {"filiais": [], "media_geral": None}

    df = _calcular_km(df)

    # Agrupa por filial (usa filial_nome do cache enriquecido)
    resultado = []
    for f_name, g in df.groupby("filial_nome"):
        if not f_name or f_name == "":
            f_name = "Sem filial"
        tv, tl, tk, ck, kl, pl = _agg_km(g)

        f_estado = g["filial_estado"].mode().iloc[0] if not g["filial_estado"].mode().empty else ""
        f_regiao = g["filial_regiao"].mode().iloc[0] if not g["filial_regiao"].mode().empty else ""

        # Composição da frota: quais grupos de veículo formam o custo desta filial
        composicao = []
        for grp_v, gv in g.groupby("grupo_veiculo"):
            if not grp_v or grp_v == "Outros":
                continue
            tv_g, tl_g, tk_g, ck_g, kl_g, _ = _agg_km(gv)
            composicao.append({
                "grupo": grp_v,
                "custo_km": ck_g,
                "qtd_veiculos": int(gv["placa"].nunique()),
                "pct_valor": round(tv_g / tv * 100, 1) if tv > 0 else 0,
            })
        composicao.sort(key=lambda x: x["pct_valor"], reverse=True)

        resultado.append({
            "filial": f_name,
            "estado": f_estado,
            "regiao": f_regiao,
            "total_valor": round(tv, 2),
            "total_litros": round(tl, 0),
            "total_km": round(tk, 0) if tk else None,
            "custo_km": ck,
            "km_litro": kl,
            "preco_litro": pl,
            "qtd_veiculos": int(g["placa"].nunique()),
            "qtd_abastecimentos": int(len(g)),
            "composicao_grupos": composicao[:5],
        })

    resultado.sort(key=lambda x: x["custo_km"] or 0, reverse=True)

    return {"filiais": resultado}


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 4: Evolução mensal
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/evolucao-mensal")
def get_evolucao_mensal(
    familia: str = Query(default="todos"),
    modo_tempo: str = Query(default="mes"),
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    grupo: Optional[str] = None,
    filial: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
):
    """Evolução mensal. Força modo_tempo='ano' quando selecionado 'mes' para dar contexto."""
    raw_df = cache.get_df()
    m_temp = "ano" if modo_tempo == "mes" else modo_tempo
    df = _apply_filters(raw_df, m_temp, ano, None, bimestre, semestre,
                        data_inicio, data_fim, grupo, filial, estado, regiao)
    df = _filter_familia(df, familia)

    if df.empty:
        return []

    df = _calcular_km(df)
    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    resultado = []
    for am in sorted(df["ano_mes"].unique()):
        g = df[df["ano_mes"] == am]
        tv, tl, tk, ck, kl, pl = _agg_km(g)
        resultado.append({
            "ano_mes": am,
            "total_valor": round(tv, 2),
            "total_litros": round(tl, 0),
            "total_km": round(tk, 0) if tk else None,
            "custo_km": ck,
            "km_litro": kl,
            "preco_litro": pl,
        })

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 5: Veículos sob alerta (comparação DENTRO do grupo)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/veiculos-acao")
def get_veiculos_acao(
    limit: int = Query(default=30, le=100),
    familia: str = Query(default="todos"),
    modo_tempo: str = Query(default="mes"),
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    grupo: Optional[str] = None,
    filial: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
):
    """
    Veículos fora do padrão comparados com os PARES do seu grupo de veículo.
    Não mistura caminhão 17T com leve — cada grupo tem sua própria média.
    """
    raw_df = cache.get_df()
    df = _apply_filters(raw_df, modo_tempo, ano, mes, bimestre, semestre,
                        data_inicio, data_fim, grupo, filial, estado, regiao)
    df = _filter_familia(df, familia)

    if df.empty:
        return {"veiculos": [], "resumo": {}}

    df = _calcular_km(df)

    # 1. Agrega por placa
    veiculos = []
    for placa, g in df.groupby("placa"):
        tv, tl, tk, ck, kl, pl = _agg_km(g)
        if tk is None:
            continue

        grp = g["grupo_veiculo"].iloc[0] if "grupo_veiculo" in g.columns else "Outros"
        f_name = g["filial_nome"].iloc[0] if "filial_nome" in g.columns else ""
        motorista = g["motorista"].dropna().mode()
        modelo = g["modelo_veiculo"].dropna().mode()

        veiculos.append({
            "placa": placa,
            "grupo": grp,
            "filial": f_name or "Sem filial",
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

    # 2. Calcula média POR GRUPO
    from collections import defaultdict
    grupos_stats = defaultdict(lambda: {"custo_kms": [], "km_litros": []})
    for v in veiculos:
        grupos_stats[v["grupo"]]["custo_kms"].append(v["custo_km"])
        if v["km_litro"]:
            grupos_stats[v["grupo"]]["km_litros"].append(v["km_litro"])

    medias_grupo = {}
    for grp, stats in grupos_stats.items():
        cks = stats["custo_kms"]
        kls = stats["km_litros"]
        medias_grupo[grp] = {
            "media_custo_km": sum(cks) / len(cks) if cks else 0,
            "media_km_litro": sum(kls) / len(kls) if kls else None,
            "qtd": len(cks),
        }

    # 3. Flag cada veículo contra a média do SEU grupo
    for v in veiculos:
        grp_media = medias_grupo.get(v["grupo"], {})
        media_ck = grp_media.get("media_custo_km", 0)
        media_kl = grp_media.get("media_km_litro")
        qtd_pares = grp_media.get("qtd", 0)

        # Só flaggeia se o grupo tem pelo menos 3 veículos (amostra mínima)
        flags = []
        if qtd_pares >= 3:
            if media_ck and v["custo_km"] > media_ck * 1.15:
                flags.append("ALTO_CUSTO")
            if v["km_litro"] and media_kl and v["km_litro"] < media_kl * 0.80:
                flags.append("BAIXO_RENDIMENTO")

        v["flag"] = "CRITICO" if len(flags) > 1 else flags[0] if flags else "OK"
        v["media_grupo_custo_km"] = round(media_ck, 4) if media_ck else None
        v["media_grupo_km_litro"] = round(media_kl, 2) if media_kl else None
        v["pct_vs_grupo"] = round((v["custo_km"] - media_ck) / media_ck * 100, 1) if media_ck else 0
        v["economia_possivel"] = round((v["custo_km"] - media_ck) * v["total_km"], 2) if v["flag"] != "OK" and media_ck else 0

    acao = [v for v in veiculos if v["flag"] != "OK"]
    acao.sort(key=lambda x: abs(x.get("pct_vs_grupo", 0)), reverse=True)

    # Resumo geral
    all_ck = [v["custo_km"] for v in veiculos]
    all_kl = [v["km_litro"] for v in veiculos if v["km_litro"]]

    return {
        "veiculos": acao[:limit],
        "resumo": {
            "total_frota": len(veiculos),
            "total_acao": len(acao),
            "media_custo_km_geral": round(sum(all_ck) / len(all_ck), 4) if all_ck else None,
            "media_km_litro_geral": round(sum(all_kl) / len(all_kl), 2) if all_kl else None,
            "economia_total_possivel": round(sum(v["economia_possivel"] for v in acao), 2),
            "grupos_monitorados": len(medias_grupo),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT 6: Etanol vs Gasolina por filial (com filtros temporais)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/etanol-gasolina-filial")
def get_etanol_gasolina_filial(
    modo_tempo: str = Query(default="mes"),
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
):
    """
    Por filial: custo/km de gasolina vs etanol.
    Recomenda melhor opção. Fallback: regra 70%.
    Agora respeita filtros temporais.
    """
    raw_df = cache.get_df()
    df = _apply_filters(raw_df, modo_tempo, ano, mes, bimestre, semestre,
                        data_inicio, data_fim, None, None, estado, regiao)

    df["familia"] = df["nome_combustivel"].apply(_familia)
    df = df[df["familia"].isin(["gasolina", "etanol"])].copy()

    if df.empty:
        return []

    df = _calcular_km(df)

    resultado = []
    col_filial = "filial_nome" if "filial_nome" in df.columns else "placa"

    for filial, gf in df.groupby("filial_nome"):
        if not filial or filial == "":
            filial = "Sem filial"
        row = {"filial": filial}

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
