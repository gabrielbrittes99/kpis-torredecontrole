"""
Sistema — Legenda / Sumário do sistema de classificação.
Retorna as regras de categorização de veículos, combustíveis e filiais
com estatísticas reais da frota para exibição na página de referência.
"""
from datetime import datetime

import pandas as pd
from fastapi import APIRouter

from config import (
    FUEL_GROUPS, FUEL_GROUP_MAP,
    VEICULO_GROUPS, KML_REFERENCIA,
    FILIAIS_MAP, PALMAS_FILIAL, PALMAS_PLACAS,
    PLACAS_RENOMEADAS,
)
from data_cache import cache
from db_fkm import get_fkm_df

router = APIRouter(prefix="/api/sistema", tags=["sistema"])

# Modelos de exemplo por grupo (para exibição humana)
_GRUPO_EXEMPLOS: dict[str, list[str]] = {
    "Caminhão17Ton":  ["30-330", "30-280", "VM 330", "26-260"],
    "Caminhão12Ton":  ["20.480 Constellation", "Atego 2429/2430", "VM 290", "24-280"],
    "Caminhão10.5Ton":["17-230", "17-210", "Atego 1719"],
    "Caminhão9Ton":   ["13-180", "Atego 1419"],
    "Caminhão7.5Ton": ["14-190", "14-210"],
    "Caminhão6Ton":   ["11-180"],
    "Caminhão5.5Ton": ["Accelo 1016", "Accelo 1017", "10-160"],
    "Caminhão5Ton":   ["9-170"],
    "Caminhão4.2Ton": ["Cargo 816", "8-160", "HD80", "Accelo 815/817"],
    "Pesado":         ["Sprinter", "Master", "Transit", "Ducato", "S10"],
    "Médio":          ["Strada", "Saveiro", "Fiorino", "Duster", "Oroch"],
    "Leve":           ["Gol", "Polo", "Virtus", "Onix", "208", "Argo"],
    "Kombi":          ["Kombi"],
    "Moto":           ["CG 160"],
}

_FUEL_VARIACOES: dict[str, list[str]] = {
    "Diesel":   ["Diesel S10", "Diesel S500", "Diesel Aditivado", "Biodiesel", "B10", "B12", "B13"],
    "Gasolina": ["Gasolina Comum", "Gasolina Aditivada", "Gasolina Premium", "V-Power", "Podium"],
    "Álcool":   ["Álcool Comum", "Álcool Aditivado", "Etanol Hidratado"],
    "Arla":     ["Arla 32"],
}

_FUEL_CORES: dict[str, str] = {
    "Diesel": "#f97316", "Gasolina": "#3b82f6",
    "Álcool": "#10b981", "Arla": "#8b5cf6",
}


@router.get("/cache-status")
def get_cache_status():
    """Status de todos os caches — útil para verificar se o warmup completou."""
    from datetime import datetime as _dt
    agora = _dt.now()

    # 1. Cache principal (transações, pedágios, estornos)
    caches_truckpag = {}
    for key in ["transacoes", "pedagios", "estornos"]:
        entry = cache._cache.get(key, {})
        ts = entry.get("ts")
        df = entry.get("df")
        caches_truckpag[key] = {
            "carregado": df is not None,
            "registros": len(df) if df is not None else 0,
            "atualizado_em": ts.isoformat() if ts else None,
            "idade_minutos": round((agora - ts).total_seconds() / 60, 1) if ts else None,
        }

    # 2. SQL Server (veículos + manutenção)
    try:
        from db_sqlserver import (
            _veiculos_cache, _veiculos_cache_ts,
            _manutencao_cache, _manutencao_cache_ts,
        )
        sqlserver = {
            "veiculos": {
                "carregado": _veiculos_cache is not None,
                "registros": len(_veiculos_cache) if _veiculos_cache is not None else 0,
                "atualizado_em": _veiculos_cache_ts.isoformat() if _veiculos_cache_ts else None,
            },
            "manutencao": {
                "carregado": _manutencao_cache is not None,
                "registros": len(_manutencao_cache) if _manutencao_cache is not None else 0,
                "atualizado_em": _manutencao_cache_ts.isoformat() if _manutencao_cache_ts else None,
            },
        }
    except Exception:
        sqlserver = {"status": "indisponível"}

    # 3. FKM
    try:
        from db_fkm import _fkm_cache, _fkm_cache_ts
        fkm = {
            "carregado": _fkm_cache is not None,
            "registros": len(_fkm_cache) if _fkm_cache is not None else 0,
            "atualizado_em": _fkm_cache_ts.isoformat() if _fkm_cache_ts else None,
        }
    except Exception:
        fkm = {"status": "indisponível"}

    todos_ok = (
        all(v["carregado"] for v in caches_truckpag.values())
        and (isinstance(sqlserver, dict) and sqlserver.get("veiculos", {}).get("carregado", False))
        and (isinstance(fkm, dict) and fkm.get("carregado", False))
    )

    return {
        "status": "ok" if todos_ok else "parcial",
        "truckpag": caches_truckpag,
        "sqlserver": sqlserver,
        "fkm": fkm,
    }


@router.get("/legenda")
def get_legenda():
    df = cache.get_df()

    # ── Stats reais por grupo de veículo ─────────────────────────────────────
    grupos_stats: dict[str, dict] = {}
    for grp, g in df.groupby("grupo_veiculo"):
        if grp in ("Outros", ""):
            continue
        grupos_stats[grp] = {
            "qtd_veiculos":       int(g["placa"].nunique()),
            "qtd_abastecimentos": int(len(g)),
            "gasto_total":        round(float(g["valor"].sum()), 0),
        }

    grupos_veiculo = []
    for grp in VEICULO_GROUPS:
        refs = KML_REFERENCIA.get(grp, {})
        # Combustível padrão do grupo
        comb_padrao = "Diesel" if refs.get("Diesel") else (
            "Gasolina" if refs.get("Gasolina") else None
        )
        ref_tuple = refs.get(comb_padrao) if comb_padrao else None
        kml_meta   = round(ref_tuple[0], 2) if ref_tuple and ref_tuple[0] else None
        kml_alerta = round(ref_tuple[1], 2) if ref_tuple and ref_tuple[1] else None

        stats = grupos_stats.get(grp, {})
        grupos_veiculo.append({
            "grupo":              grp,
            "modelos_exemplo":    _GRUPO_EXEMPLOS.get(grp, []),
            "combustivel_padrao": comb_padrao,
            "kml_meta":           kml_meta,
            "kml_alerta":         kml_alerta,
            "qtd_veiculos":       stats.get("qtd_veiculos", 0),
            "qtd_abastecimentos": stats.get("qtd_abastecimentos", 0),
            "gasto_total":        stats.get("gasto_total", 0),
        })

    # ── Grupos de combustível ─────────────────────────────────────────────────
    grupos_combustivel = []
    for grp in FUEL_GROUPS:
        comb_df = df[df["grupo_combustivel"] == grp]
        grupos_combustivel.append({
            "grupo":    grp,
            "cor":      _FUEL_CORES.get(grp, "#6b7280"),
            "variacoes": _FUEL_VARIACOES.get(grp, []),
            "qtd_abastecimentos": int(len(comb_df)),
            "litros_total":       round(float(comb_df["litragem"].sum()), 0),
            "gasto_total":        round(float(comb_df["valor"].sum()), 0),
            "preco_medio":        round(
                float(comb_df["valor"].sum()) / float(comb_df["litragem"].sum()), 3
            ) if float(comb_df["litragem"].sum()) > 0 else None,
        })

    # ── Filiais cadastradas ───────────────────────────────────────────────────
    filiais_map_resumo = {}
    for sigla, info in FILIAIS_MAP.items():
        r = info["regiao"]
        if r not in filiais_map_resumo:
            filiais_map_resumo[r] = []
        filiais_map_resumo[r].append(info["nome"])

    # Deduplica
    por_regiao = [
        {"regiao": r, "filiais": sorted(set(nomes))}
        for r, nomes in sorted(filiais_map_resumo.items())
    ]
    # Adiciona Palmas (hardcoded)
    for entry in por_regiao:
        if entry["regiao"] == PALMAS_FILIAL["regiao"]:
            if PALMAS_FILIAL["nome"] not in entry["filiais"]:
                entry["filiais"].append(PALMAS_FILIAL["nome"])

    # ── Estatísticas gerais do banco ─────────────────────────────────────────
    data_min = df["data_transacao"].min()
    data_max = df["data_transacao"].max()
    ano_atual = datetime.now().year

    # Placas com ano_modelo → distribuição de idade
    idade_counts = {}
    if "ano_modelo" in df.columns:
        placas_ano = df[df["ano_modelo"].notna()][["placa", "ano_modelo"]].drop_duplicates("placa")
        placas_ano["idade"] = ano_atual - placas_ano["ano_modelo"].astype(int)
        for _, row in placas_ano.iterrows():
            faixa = (
                "0–2 anos" if row["idade"] <= 2 else
                "3–5 anos" if row["idade"] <= 5 else
                "6–10 anos" if row["idade"] <= 10 else
                "> 10 anos"
            )
            idade_counts[faixa] = idade_counts.get(faixa, 0) + 1

    return {
        "grupos_veiculo":    grupos_veiculo,
        "grupos_combustivel": grupos_combustivel,
        "por_regiao":        por_regiao,
        "placas_renomeadas": [
            {"antiga": k, "nova": v} for k, v in PLACAS_RENOMEADAS.items()
        ],
        "palmas_placas":     sorted(PALMAS_PLACAS),
        "estatisticas": {
            "total_registros":          int(len(df)),
            "total_abastecimentos":     int(len(df)),
            "total_pedagios":           int(len(cache.get_df("pedagios"))),
            "total_estornos":           int(len(cache.get_df("estornos"))),
            "total_veiculos":           int(df["placa"].nunique()),
            "total_postos":             int(df["razao_social_posto"].nunique()),
            "periodo_inicio":           data_min.strftime("%d/%m/%Y") if data_min is not pd.NaT else None,
            "periodo_fim":              data_max.strftime("%d/%m/%Y") if data_max is not pd.NaT else None,
            "filtro_base":              "Separação lógica por tipo_abastecimento (Combustível vs Pedágio vs Estorno)",
            "calculo_kml":              "Δhodômetro entre abastecimentos consecutivos (1–2.000 km)",
            "fonte_filiais":            "SQL Server BlueFleet + hardcoded Palmas (TO)",
            "distribuicao_idade_frota": idade_counts,
        },
    }


@router.get("/integridade")
def get_integridade():
    """
    Relatório de integridade cross-source:
    - Placas no TruckPag sem cadastro no BlueFleet
    - Placas no FKM sem cadastro no BlueFleet
    - Cobertura temporal do FKM vs TruckPag
    - Taxa de estorno e pedágio
    """
    df_tx     = cache.get_df("transacoes")
    df_pedag  = cache.get_df("pedagios")
    df_estorn = cache.get_df("estornos")
    df_fkm    = get_fkm_df()

    placas_tx    = set(df_tx["placa"].unique())
    placas_pedag = set(df_pedag["placa"].unique()) if not df_pedag.empty else set()
    placas_fkm   = set(df_fkm["placa"].unique()) if not df_fkm.empty else set()

    try:
        from db_sqlserver import get_veiculos_df
        veic = get_veiculos_df()
        from utils import norm_placa
        placas_bluefleet = set(veic["Placa"].apply(norm_placa).unique()) if not veic.empty else set()
    except Exception:
        placas_bluefleet = set()

    # Placas TruckPag sem BlueFleet
    tx_sem_bluefleet = sorted(placas_tx - placas_bluefleet) if placas_bluefleet else []
    # Placas FKM sem BlueFleet
    fkm_sem_bluefleet = sorted(placas_fkm - placas_bluefleet) if placas_bluefleet else []
    # Placas TruckPag sem FKM (sem fechamento mensal)
    tx_sem_fkm = sorted(placas_tx - placas_fkm)

    # Cobertura temporal
    meses_tx  = sorted(df_tx["data_transacao"].dt.to_period("M").astype(str).unique().tolist()) if not df_tx.empty else []
    meses_fkm = sorted(df_fkm["ano_mes"].dropna().unique().tolist()) if not df_fkm.empty else []

    # Taxas
    total_all = len(df_tx) + len(df_estorn)
    taxa_estorno = round(len(df_estorn) / total_all * 100, 2) if total_all > 0 else 0
    total_comb_pedag = len(df_tx) + len(df_pedag)
    taxa_pedagio = round(len(df_pedag) / total_comb_pedag * 100, 2) if total_comb_pedag > 0 else 0

    return {
        "placas_tx_sem_bluefleet":  {"qtd": len(tx_sem_bluefleet),  "placas": tx_sem_bluefleet[:20]},
        "placas_fkm_sem_bluefleet": {"qtd": len(fkm_sem_bluefleet), "placas": fkm_sem_bluefleet[:20]},
        "placas_tx_sem_fkm":        {"qtd": len(tx_sem_fkm),        "placas": tx_sem_fkm[:20]},
        "cobertura_temporal": {
            "truckpag": {"primeiro": meses_tx[0] if meses_tx else None,  "ultimo": meses_tx[-1] if meses_tx else None,  "meses": len(meses_tx)},
            "fkm":      {"primeiro": meses_fkm[0] if meses_fkm else None, "ultimo": meses_fkm[-1] if meses_fkm else None, "meses": len(meses_fkm)},
        },
        "taxas": {
            "taxa_estorno_pct": taxa_estorno,
            "taxa_pedagio_pct": taxa_pedagio,
            "total_abastecimentos": len(df_tx),
            "total_pedagios":       len(df_pedag),
            "total_estornos":       len(df_estorn),
        },
    }


@router.get("/cobertura-dados")
def get_cobertura_dados():
    """
    Matriz de cobertura por placa: quais fontes têm dados para cada veículo.
    Útil para identificar veículos com dados incompletos.
    """
    df_tx  = cache.get_df("transacoes")
    df_fkm = get_fkm_df()

    try:
        from db_sqlserver import get_veiculos_df
        from utils import norm_placa
        veic = get_veiculos_df()
        placas_bluefleet = set(veic["Placa"].apply(norm_placa).unique()) if not veic.empty else set()
    except Exception:
        placas_bluefleet = set()

    placas_tx  = set(df_tx["placa"].unique())
    placas_fkm = set(df_fkm["placa"].unique()) if not df_fkm.empty else set()
    todas      = sorted(placas_tx | placas_fkm | placas_bluefleet)

    # Meses TruckPag por placa
    meses_tx_por_placa: dict = {}
    if not df_tx.empty:
        df_tx2 = df_tx.copy()
        df_tx2["ano_mes"] = df_tx2["data_transacao"].dt.to_period("M").astype(str)
        meses_tx_por_placa = df_tx2.groupby("placa")["ano_mes"].nunique().to_dict()

    # Meses FKM por placa
    meses_fkm_por_placa: dict = {}
    if not df_fkm.empty:
        meses_fkm_por_placa = df_fkm.groupby("placa")["ano_mes"].nunique().to_dict()

    resultado = []
    for placa in todas:
        resultado.append({
            "placa":          placa,
            "has_truckpag":   placa in placas_tx,
            "has_fkm":        placa in placas_fkm,
            "has_bluefleet":  placa in placas_bluefleet,
            "meses_truckpag": int(meses_tx_por_placa.get(placa, 0)),
            "meses_fkm":      int(meses_fkm_por_placa.get(placa, 0)),
            "cobertura_completa": (placa in placas_tx) and (placa in placas_fkm) and (placa in placas_bluefleet),
        })

    # Ordena: sem cobertura completa primeiro
    resultado.sort(key=lambda x: (x["cobertura_completa"], x["placa"]))
    return resultado
