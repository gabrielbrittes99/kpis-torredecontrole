"""
Seção 3 — Eficiência de Frota
Análise de km/L, custo por placa, ranking de motoristas e alertas.
"""
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Query

from data_cache import cache
from db_sqlserver import get_veiculos_df

router = APIRouter(prefix="/api/frota", tags=["frota"])


def _apply_filters(
    df: pd.DataFrame,
    combustivel: Optional[str],
    placa: Optional[str],
) -> pd.DataFrame:
    if combustivel:
        df = df[df["nome_combustivel"] == combustivel]
    if placa:
        df = df[df["placa"] == placa.upper()]
    return df


# ---------------------------------------------------------------------------
# Eficiência km/L por veículo
# ---------------------------------------------------------------------------

@router.get("/eficiencia-km-litro")
def get_eficiencia_km_litro(
    combustivel: Optional[str] = Query(None),
    limit: int = Query(default=20, le=100),
):
    """
    Calcula km/L por veículo usando a diferença de hodômetro entre abastecimentos.
    Requer campo hodometro preenchido.
    """
    df = cache.get_df().copy()
    if combustivel:
        df = df[df["nome_combustivel"] == combustivel]

    # Só registros com hodômetro
    df = df[df["hodometro"].notna() & (df["hodometro"] > 0)]

    if df.empty:
        return []

    df = df.sort_values(["placa", "data_transacao"])

    resultados = []
    for placa, grupo in df.groupby("placa"):
        grupo = grupo.reset_index(drop=True)
        if len(grupo) < 2:
            continue

        # Diferença de hodômetro entre abastecimentos consecutivos
        grupo["km_percorrido"] = grupo["hodometro"].diff()

        # Filtra km válidos: positivo e razoável (até 2000km entre abastecimentos)
        validos = grupo[(grupo["km_percorrido"] > 0) & (grupo["km_percorrido"] <= 2000)].copy()

        if validos.empty:
            continue

        total_km = float(validos["km_percorrido"].sum())
        total_litros = float(validos["litragem"].sum())
        total_valor = float(grupo["valor"].sum())
        km_litro = round(total_km / total_litros, 2) if total_litros > 0 else None

        modelo = grupo["modelo_veiculo"].dropna().mode()
        marca = grupo["marca_veiculo"].dropna().mode()
        motorista = grupo["motorista"].dropna().mode()

        resultados.append({
            "placa": placa,
            "modelo": modelo.iloc[0] if not modelo.empty else "",
            "marca": marca.iloc[0] if not marca.empty else "",
            "motorista_principal": motorista.iloc[0] if not motorista.empty else "",
            "km_litro": km_litro,
            "total_km": round(total_km, 0),
            "total_litros": round(total_litros, 0),
            "total_valor": round(total_valor, 2),
            "qtd_abastecimentos": int(len(grupo)),
            "custo_por_km": round(total_valor / total_km, 4) if total_km > 0 else None,
        })

    if not resultados:
        return []

    resultados.sort(key=lambda x: x["km_litro"] or 0, reverse=True)
    return resultados[:limit]


# ---------------------------------------------------------------------------
# Custo por placa
# ---------------------------------------------------------------------------

@router.get("/custo-por-placa")
def get_custo_por_placa(
    combustivel: Optional[str] = Query(None),
    limit: int = Query(default=20, le=100),
):
    """Custo total e litros por veículo (placa)."""
    df = _apply_filters(cache.get_df(), combustivel, None)
    if df.empty:
        return []

    agg = (
        df.groupby("placa")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
            modelo=("modelo_veiculo", lambda x: x.mode().iloc[0] if not x.mode().empty else ""),
            marca=("marca_veiculo", lambda x: x.mode().iloc[0] if not x.mode().empty else ""),
        )
        .reset_index()
        .sort_values("total_valor", ascending=False)
        .head(limit)
    )
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)

    return [
        {
            "placa": row["placa"],
            "modelo": row["modelo"],
            "marca": row["marca"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 0),
            "preco_medio": float(row["preco_medio"]),
            "qtd_abastecimentos": int(row["qtd"]),
        }
        for _, row in agg.iterrows()
    ]


# ---------------------------------------------------------------------------
# Ranking de motoristas
# ---------------------------------------------------------------------------

@router.get("/ranking-motoristas")
def get_ranking_motoristas(
    combustivel: Optional[str] = Query(None),
    limite: int = Query(default=15, le=50),
):
    """Ranking de motoristas por preço médio pago e gasto total."""
    df = _apply_filters(cache.get_df(), combustivel, None)
    df = df[df["motorista"] != ""].copy()

    if df.empty:
        return []

    agg = (
        df.groupby("motorista")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd=("valor", "count"),
        )
        .reset_index()
    )
    agg = agg[agg["qtd"] >= 3]  # Mínimo 3 abastecimentos
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)
    agg = agg.sort_values("preco_medio").head(limite)

    preco_min = float(agg["preco_medio"].min()) if not agg.empty else 0

    return [
        {
            "motorista": row["motorista"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 0),
            "preco_medio": float(row["preco_medio"]),
            "qtd_abastecimentos": int(row["qtd"]),
            "desvio_do_minimo": round((float(row["preco_medio"]) - preco_min), 4),
        }
        for _, row in agg.iterrows()
    ]


# ---------------------------------------------------------------------------
# Abastecimentos suspeitos
# ---------------------------------------------------------------------------

def _familia_combustivel(nome: str) -> str:
    """Agrupa combustíveis em famílias para evitar falso-positivo diesel+arla."""
    n = nome.lower()
    if "arla" in n:
        return "arla"
    if "diesel" in n or "s10" in n or "s-10" in n or "s500" in n:
        return "diesel"
    if "gasolina" in n:
        return "gasolina"
    if "etanol" in n or "álcool" in n or "alcool" in n:
        return "etanol"
    if "gnv" in n or "gás natural" in n:
        return "gnv"
    return nome.lower().strip()


@router.get("/abastecimentos-suspeitos")
def get_abastecimentos_suspeitos(
    placa: Optional[str] = Query(None),
):
    """
    Detecta abastecimentos potencialmente suspeitos:
    - Volume acima da capacidade do tanque (cruzado com BlueFleet)
    - Litros muito acima da média da placa (> 2.5x desvio padrão)
    - Preço por litro anormalmente alto (> 2.5x desvio padrão do tipo)
    - Mesmo combustível abastecido duas vezes no mesmo dia (diesel+arla é normal)
    """
    df = cache.get_df().copy()
    if placa:
        df = df[df["placa"] == placa.upper()]

    if df.empty:
        return []

    alertas = []

    # Normaliza placa do TruckPag para cruzar com BlueFleet (remove hífen)
    df["placa_norm"] = df["placa"].str.upper().str.replace("-", "").str.strip()

    # Carrega capacidade de tanque do SQL Server
    df_veiculos = get_veiculos_df()
    tanque_map = (
        df_veiculos.set_index("Placa")["TanqueLitros"].dropna().to_dict()
        if not df_veiculos.empty else {}
    )

    # 1. Volume acima da capacidade do tanque (BlueFleet)
    if tanque_map:
        df["tanque"] = df["placa_norm"].map(tanque_map)
        df_tank = df[df["tanque"].notna() & (df["litragem"] > df["tanque"])].copy()
        for _, row in df_tank.iterrows():
            alertas.append({
                "tipo": "acima_capacidade_tanque",
                "descricao": f"{row['litragem']:.0f}L abastecido supera capacidade do tanque ({row['tanque']:.0f}L)",
                "data": str(row["data_transacao"].date()),
                "placa": row["placa"],
                "motorista": row["motorista"],
                "valor": round(float(row["valor"]), 2),
                "litragem": round(float(row["litragem"]), 1),
                "posto": row["razao_social_posto"],
                "cidade": row["cidade_posto"],
            })

    # 2. Volume excessivo por placa (estatístico)
    stats_placa = df.groupby("placa")["litragem"].agg(["mean", "std"]).reset_index()
    stats_placa.columns = ["placa", "media_litros", "std_litros"]
    df_vol = df.merge(stats_placa, on="placa")
    df_vol = df_vol[
        df_vol["std_litros"].notna() &
        (df_vol["std_litros"] > 0) &
        (df_vol["litragem"] > df_vol["media_litros"] + 2.5 * df_vol["std_litros"])
    ]
    for _, row in df_vol.iterrows():
        alertas.append({
            "tipo": "volume_excessivo",
            "descricao": f"{row['litragem']:.0f}L muito acima da média da placa ({row['media_litros']:.0f}L)",
            "data": str(row["data_transacao"].date()),
            "placa": row["placa"],
            "motorista": row["motorista"],
            "valor": round(float(row["valor"]), 2),
            "litragem": round(float(row["litragem"]), 1),
            "posto": row["razao_social_posto"],
            "cidade": row["cidade_posto"],
        })

    # 3. Preço por litro alto por tipo de combustível
    df_preco = df.copy()
    df_preco["preco_litro"] = df_preco["valor"] / df_preco["litragem"]
    stats_tipo = df_preco.groupby("nome_combustivel")["preco_litro"].agg(["mean", "std"]).reset_index()
    stats_tipo.columns = ["nome_combustivel", "media_preco", "std_preco"]
    df_preco = df_preco.merge(stats_tipo, on="nome_combustivel")
    df_preco = df_preco[
        df_preco["std_preco"].notna() &
        (df_preco["std_preco"] > 0) &
        (df_preco["preco_litro"] > df_preco["media_preco"] + 2.5 * df_preco["std_preco"])
    ]
    for _, row in df_preco.iterrows():
        alertas.append({
            "tipo": "preco_alto",
            "descricao": f"R${row['preco_litro']:.3f}/L muito acima da média R${row['media_preco']:.3f}/L para {row['nome_combustivel']}",
            "data": str(row["data_transacao"].date()),
            "placa": row["placa"],
            "motorista": row["motorista"],
            "valor": round(float(row["valor"]), 2),
            "litragem": round(float(row["litragem"]), 1),
            "posto": row["razao_social_posto"],
            "cidade": row["cidade_posto"],
        })

    # 4. Mesmo combustível (mesma família) abastecido 2x no mesmo dia
    df_dup = df.copy()
    df_dup["dia"] = df_dup["data_transacao"].dt.date
    df_dup["familia"] = df_dup["nome_combustivel"].apply(_familia_combustivel)

    # Agrupa por placa + dia + família de combustível
    cnt = df_dup.groupby(["placa", "dia", "familia"]).size().reset_index(name="count")
    duplicados = cnt[cnt["count"] >= 2]

    for _, row in duplicados.iterrows():
        grupo = df_dup[
            (df_dup["placa"] == row["placa"]) &
            (df_dup["dia"] == row["dia"]) &
            (df_dup["familia"] == row["familia"])
        ]
        total_litros = float(grupo["litragem"].sum())
        combustiveis = ", ".join(grupo["nome_combustivel"].unique())
        alertas.append({
            "tipo": "abastecimento_duplo",
            "descricao": f"{int(row['count'])}x {row['familia']} no mesmo dia ({combustiveis}) — {total_litros:.0f}L total",
            "data": str(row["dia"]),
            "placa": row["placa"],
            "motorista": grupo["motorista"].iloc[0] if not grupo.empty else "",
            "valor": round(float(grupo["valor"].sum()), 2),
            "litragem": round(total_litros, 1),
            "posto": grupo["razao_social_posto"].iloc[0] if not grupo.empty else "",
            "cidade": grupo["cidade_posto"].iloc[0] if not grupo.empty else "",
        })

    alertas.sort(key=lambda x: x["data"], reverse=True)
    return alertas[:100]


# ---------------------------------------------------------------------------
# Evolução mensal de custo da frota
# ---------------------------------------------------------------------------

@router.get("/custo-mensal-frota")
def get_custo_mensal_frota(
    combustivel: Optional[str] = Query(None),
):
    """Custo total e litros por mês para visão da frota."""
    df = _apply_filters(cache.get_df(), combustivel, None)
    if df.empty:
        return []

    df = df.copy()
    df["ano_mes"] = df["data_transacao"].dt.to_period("M").astype(str)

    agg = (
        df.groupby("ano_mes")
        .agg(
            total_valor=("valor", "sum"),
            total_litros=("litragem", "sum"),
            qtd_veiculos=("placa", "nunique"),
            qtd_abastecimentos=("valor", "count"),
        )
        .reset_index()
        .sort_values("ano_mes")
    )
    agg["preco_medio"] = (agg["total_valor"] / agg["total_litros"]).round(4)

    return [
        {
            "ano_mes": row["ano_mes"],
            "total_valor": round(float(row["total_valor"]), 2),
            "total_litros": round(float(row["total_litros"]), 0),
            "preco_medio": float(row["preco_medio"]),
            "qtd_veiculos": int(row["qtd_veiculos"]),
            "qtd_abastecimentos": int(row["qtd_abastecimentos"]),
            "custo_medio_por_veiculo": round(float(row["total_valor"]) / int(row["qtd_veiculos"]), 2) if row["qtd_veiculos"] > 0 else 0,
        }
        for _, row in agg.iterrows()
    ]
