"""
Visão Operacional — Acompanhamento de Frota
Custo/KM por grupo de veículo, filial e região.
Alertas comparando cada veículo com os pares do seu grupo.
"""

import logging
from typing import Optional

import pandas as pd
from data_cache import cache
from db_dw import get_dw_engine
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/operacional", tags=["operacional"])

# ── Dados FKM reconciliados por placa/mês ────────────────────────────────────


def _load_fkm_overrides(
    ano_mes: str, grupo: str | None = None, filial: str | None = None
) -> dict:
    """
    Retorna dict {placa_norm: {litros, valor, total_km, fonte}} para o mês dado.
    Usa litros_efetivo e valor_efetivo (já corrigidos pelo ETL de reconciliação).
    Retorna {} se a tabela não existir ou o mês ainda não tiver sido processado.
    """
    try:
        from sqlalchemy import text

        engine = get_dw_engine()
        where = ["ano_mes = :ano_mes", "litros_efetivo > 0", "total_km > 0"]
        params: dict = {"ano_mes": ano_mes}
        if grupo:
            where.append("grupo_veiculo = :grupo")
            params["grupo"] = grupo
        if filial:
            where.append("filial = :filial")
            params["filial"] = filial

        sql = f"""
            SELECT
                UPPER(REPLACE(placa, '-', '')) AS placa_norm,
                litros_efetivo,
                valor_efetivo,
                total_km,
                corrigido_por_truckpag
            FROM torre.fkm_reconciliacao
            WHERE {" AND ".join(where)}
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()

        return {
            row.placa_norm: {
                "litros": float(row.litros_efetivo),
                "valor": float(row.valor_efetivo),
                "total_km": float(row.total_km),
                "corrigido": bool(row.corrigido_por_truckpag),
                "fonte": "fkm_reconciliado",
            }
            for row in rows
        }
    except Exception:
        return {}


# ── Mapa família (frontend) → grupo_combustivel (cache) ─────────────────────
_FAMILIA_MAP = {
    "diesel": "Diesel",
    "gasolina": "Gasolina",
    "etanol": "Álcool",
}


# ── Agregação de métricas (range por veículo) ───────────────────────────────
def _agg_km(grupo: pd.DataFrame):
    # Logica: diff de hodometro entre abastecimentos consecutivos por placa.
    # Descarta diffs invalidos (<= 0 ou > 2000 km). Exclui Arla da performance.
    total_valor = float(grupo["valor"].sum())
    total_litros = float(grupo["litragem"].sum())
    preco_litro = round(total_valor / total_litros, 2) if total_litros > 0 else None
    if "hodometro" not in grupo.columns or grupo.empty:
        return total_valor, total_litros, None, None, None, preco_litro
    hodo = grupo[grupo["hodometro"].notna() & (grupo["hodometro"] > 0)].copy()
    if hodo.empty:
        return total_valor, total_litros, None, None, None, preco_litro
    res_valor_km = res_litros_km = res_total_km = 0.0
    for placa, g_veh in hodo.groupby("placa"):
        g_veh = g_veh.sort_values("data_transacao").reset_index(drop=True)
        g_perf = g_veh[
            ~g_veh["grupo_combustivel"].str.contains("Arla", case=False, na=False)
        ].copy()
        if g_perf.empty:
            continue
        g_perf = g_perf.sort_values("data_transacao").reset_index(drop=True)
        g_perf["km_percorrido"] = g_perf["hodometro"].diff()
        validos = g_perf[
            (g_perf["km_percorrido"] > 0) & (g_perf["km_percorrido"] <= 2000)
        ]
        if validos.empty:
            continue
        res_total_km += float(validos["km_percorrido"].sum())
        res_valor_km += float(validos["valor"].sum())
        res_litros_km += float(validos["litragem"].sum())
    if res_total_km == 0:
        return total_valor, total_litros, None, None, None, preco_litro
    custo_km = round(res_valor_km / res_total_km, 2)
    km_litro = round(res_total_km / res_litros_km, 2) if res_litros_km > 0 else None
    return total_valor, total_litros, res_total_km, custo_km, km_litro, preco_litro


def _qtd_com_km(df: pd.DataFrame) -> int:
    """Veículos com ≥ 2 leituras válidas de hodômetro (conseguem calcular range)."""
    if "hodometro" not in df.columns:
        return 0
    hodo = df[df["hodometro"].notna() & (df["hodometro"] > 0)]
    if hodo.empty:
        return 0
    return int((hodo.groupby("placa")["hodometro"].count() >= 2).sum())


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
        df = df[
            (df["data_transacao"].dt.month == mes)
            & (df["data_transacao"].dt.year == ano)
        ]
    elif modo_tempo == "bimestre" and bimestre and ano:
        months = [bimestre * 2 - 1, bimestre * 2]
        df = df[
            (df["data_transacao"].dt.month.isin(months))
            & (df["data_transacao"].dt.year == ano)
        ]
    elif modo_tempo == "semestre" and semestre and ano:
        months = list(range(1, 7)) if semestre == 1 else list(range(7, 13))
        df = df[
            (df["data_transacao"].dt.month.isin(months))
            & (df["data_transacao"].dt.year == ano)
        ]
    elif modo_tempo == "ano" and ano:
        df = df[df["data_transacao"].dt.year == ano]
    elif modo_tempo == "personalizado" and data_inicio and data_fim:
        df = df[
            (df["data_transacao"] >= data_inicio) & (df["data_transacao"] <= data_fim)
        ]
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
    """Filtra pelo grupo_combustivel já normalizado no cache."""
    if familia == "todos":
        return df.copy()
    grupo = _FAMILIA_MAP.get(familia)
    if grupo:
        return df[df["grupo_combustivel"] == grupo].copy()
    return df.copy()


# ── Parâmetros comuns ───────────────────────────────────────────────────────
# (reusados em todos os endpoints)
_COMMON_DOC = "Filtros temporais e de atributo"


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Evolução mensal
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
    df = _apply_filters(
        raw_df,
        m_temp,
        ano,
        None,
        bimestre,
        semestre,
        data_inicio,
        data_fim,
        grupo,
        filial,
        estado,
        regiao,
    )
    df = _filter_familia(df, familia)

    if df.empty:
        return []

    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    resultado = []
    for am in sorted(df["ano_mes"].unique()):
        g = df[df["ano_mes"] == am]
        tv, tl, tk, ck, kl, pl = _agg_km(g)
        resultado.append(
            {
                "ano_mes": am,
                "total_valor": round(tv, 2),
                "total_litros": round(tl, 0),
                "total_km": round(tk, 0) if tk else None,
                "custo_km": ck,
                "km_litro": kl,
                "preco_litro": pl,
            }
        )

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
    df = _apply_filters(
        raw_df,
        modo_tempo,
        ano,
        mes,
        bimestre,
        semestre,
        data_inicio,
        data_fim,
        grupo,
        filial,
        estado,
        regiao,
    )
    df = _filter_familia(df, familia)

    if df.empty:
        return {"veiculos": [], "resumo": {}}

    # Carrega FKM reconciliado (só para modo mês — FKM é granularidade mensal)
    fkm_map = {}
    if modo_tempo == "mes" and ano and mes:
        ano_mes_str = f"{ano:04d}-{mes:02d}"
        fkm_map = _load_fkm_overrides(ano_mes_str, grupo=grupo, filial=filial)

    # 1. Agrega por placa
    veiculos = []
    for placa, g in df.groupby("placa"):
        tv, tl, tk, ck, kl, pl = _agg_km(g)

        grp = g["grupo_veiculo"].iloc[0] if "grupo_veiculo" in g.columns else "Outros"
        f_name = g["filial_nome"].iloc[0] if "filial_nome" in g.columns else ""
        motorista = g["motorista"].dropna().mode()
        modelo = g["modelo_veiculo"].dropna().mode()

        # Enriquece com FKM reconciliado se disponível para esta placa
        placa_norm = placa.upper().replace("-", "").strip()
        fkm = fkm_map.get(placa_norm)
        if fkm and not fkm["corrigido"]:
            # FKM confiável (não corrigido): usa km e litros totais do FKM
            fkm_km = fkm["total_km"]
            fkm_lit = fkm["litros"]
            fkm_val = fkm["valor"]
            kl = round(fkm_km / fkm_lit, 2) if fkm_lit > 0 else kl
            ck = round(fkm_val / fkm_km, 2) if fkm_km > 0 else ck
            tk = fkm_km
            fonte = "fkm_reconciliado"
        else:
            # Sem FKM ou FKM corrigido pelo TruckPag: usa hodômetro TruckPag
            # (kl, ck, tk já calculados por _agg_km com diffs de hodômetro)
            fonte = "truckpag" if tk is not None else None

        # Sem km registrado em nenhuma fonte → não inclui no ranking
        if tk is None:
            continue

        # Veículo com km muito baixo no mês (parado, manutenção, etc.)
        # não tem base estatística para calcular eficiência
        if tk < 300:
            continue

        item = {
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
            "fonte_kml": fonte,
        }
        # Adiciona alerta de discrepância FKM vs TruckPag quando relevante
        if fkm:
            item["litros_fkm_reportado"] = round(fkm["litros"], 1)
            item["litros_truckpag"] = round(tl, 1)
            item["fkm_corrigido"] = fkm["corrigido"]
            discrepancia = (
                abs(fkm["litros"] - tl) / max(fkm["litros"], tl)
                if max(fkm["litros"], tl) > 0
                else 0
            )
            item["fkm_discrepancia_pct"] = round(discrepancia * 100, 1)
        veiculos.append(item)

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
        v["media_grupo_custo_km"] = round(media_ck, 2) if media_ck else None
        v["media_grupo_km_litro"] = round(media_kl, 2) if media_kl else None
        v["pct_vs_grupo"] = (
            round((v["custo_km"] - media_ck) / media_ck * 100, 1) if media_ck else 0
        )
        v["economia_possivel"] = (
            round((v["custo_km"] - media_ck) * v["total_km"], 2)
            if v["flag"] != "OK" and media_ck
            else 0
        )

    acao = [v for v in veiculos if v["flag"] != "OK"]
    acao.sort(key=lambda x: x.get("economia_possivel", 0), reverse=True)

    # Resumo geral
    all_ck = [v["custo_km"] for v in veiculos]
    all_kl = [v["km_litro"] for v in veiculos if v["km_litro"]]

    return {
        "veiculos": acao[:limit],
        "resumo": {
            "total_frota": len(veiculos),
            "total_acao": len(acao),
            "media_custo_km_geral": round(sum(all_ck) / len(all_ck), 2)
            if all_ck
            else None,
            "media_km_litro_geral": round(sum(all_kl) / len(all_kl), 2)
            if all_kl
            else None,
            "economia_total_possivel": round(
                sum(v["economia_possivel"] for v in acao), 2
            ),
            "grupos_monitorados": len(medias_grupo),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Hero Operacional (KPIs Gerais)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/hero")
def get_hero_operacional(
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
    raw_df = cache.get_df()
    df = _apply_filters(
        raw_df,
        modo_tempo,
        ano,
        mes,
        bimestre,
        semestre,
        data_inicio,
        data_fim,
        grupo,
        filial,
        estado,
        regiao,
    )
    df = _filter_familia(df, familia)

    if df.empty:
        return {
            "gasto_total": 0,
            "volume_total": 0,
            "preco_medio": 0,
            "custo_km": 0,
            "postos_ativos": 0,
        }

    tv, tl, tk, ck, kl, pl = _agg_km(df)

    postos = df["nome_fantasia_posto"].where(
        df["nome_fantasia_posto"].str.len() > 0, df["razao_social_posto"]
    )
    postos_ativos = int(postos.nunique())

    return {
        "gasto_total": round(tv, 2) if tv else 0,
        "volume_total": round(tl, 0) if tl else 0,
        "preco_medio": round(pl, 3) if pl else 0,
        "custo_km": ck if ck else 0,
        "postos_ativos": postos_ativos,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Top Consumidores (Maior Volume)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/top-consumidores")
def get_top_consumidores(
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
    raw_df = cache.get_df()
    df = _apply_filters(
        raw_df,
        modo_tempo,
        ano,
        mes,
        bimestre,
        semestre,
        data_inicio,
        data_fim,
        grupo,
        filial,
        estado,
        regiao,
    )
    df = _filter_familia(df, familia)

    if df.empty:
        return []

    veiculos = []
    for placa, g in df.groupby("placa"):
        tv, tl, tk, ck, kl, pl = _agg_km(g)

        grp = g["grupo_veiculo"].iloc[0] if "grupo_veiculo" in g.columns else "Outros"
        f_name = g["filial_nome"].iloc[0] if "filial_nome" in g.columns else ""
        cidade = "Não informada"
        if "cidade_posto" in g.columns:
            m = g["cidade_posto"].dropna().mode()
            if not m.empty:
                cidade = m.iloc[0]

        motorista = (
            g["motorista"].dropna().mode() if "motorista" in g.columns else pd.Series()
        )
        modelo = (
            g["modelo_veiculo"].dropna().mode()
            if "modelo_veiculo" in g.columns
            else pd.Series()
        )

        veiculos.append(
            {
                "placa": placa,
                "grupo": grp,
                "filial": f_name or "Sem filial",
                "cidade_principal": cidade,
                "motorista": motorista.iloc[0] if not motorista.empty else "",
                "modelo": modelo.iloc[0] if not modelo.empty else "",
                "total_valor": round(tv, 2),
                "total_litros": round(tl, 0),
                "preco_medio": round(pl, 3) if pl else 0,
                "total_km": round(tk, 0) if tk else None,
                "custo_km": ck,
                "km_litro": kl,
            }
        )

    veiculos.sort(key=lambda x: x["total_litros"], reverse=True)
    return veiculos[:limit]
