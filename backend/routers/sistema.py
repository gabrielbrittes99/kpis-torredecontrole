"""
Sistema — Legenda / Sumário do sistema de classificação.
Retorna as regras de categorização de veículos, combustíveis e filiais
com estatísticas reais da frota para exibição na página de referência.
"""
from datetime import datetime

from fastapi import APIRouter

from config import (
    FUEL_GROUPS, FUEL_GROUP_MAP,
    VEICULO_GROUPS, KML_REFERENCIA,
    FILIAIS_MAP, PALMAS_FILIAL, PALMAS_PLACAS,
    PLACAS_RENOMEADAS,
)
from data_cache import cache

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
            "total_veiculos":           int(df["placa"].nunique()),
            "total_postos":             int(df["razao_social_posto"].nunique()),
            "periodo_inicio":           data_min.strftime("%d/%m/%Y") if data_min is not pd.NaT else None,
            "periodo_fim":              data_max.strftime("%d/%m/%Y") if data_max is not pd.NaT else None,
            "filtro_base":              "litragem > 0 AND transacao_estornada = '0'",
            "calculo_kml":              "Δhodômetro entre abastecimentos consecutivos (1–2.000 km)",
            "fonte_filiais":            "SQL Server BlueFleet + hardcoded Palmas (TO)",
            "distribuicao_idade_frota": idade_counts,
        },
    }
