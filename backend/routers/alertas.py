import logging
from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter

from data_cache import cache
from anp_client import get_anp_df
from config import FUEL_GROUP_MAP

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alertas", tags=["alertas"])

# Mapeamento grupo_combustivel → produto ANP para benchmark
_GRUPO_ANP = {
    "Diesel":   ["DIESEL S10", "DIESEL"],
    "Gasolina": ["GASOLINA COMUM", "GASOLINA ADITIVADA"],
    "Álcool":   ["ETANOL HIDRATADO"],
    "Arla":     [],  # ANP não publica preço de Arla
}


def _preco_anp_por_uf(df_anp: pd.DataFrame, uf: str, grupo: str) -> float | None:
    """Preço médio ANP para um grupo de combustível em uma UF."""
    produtos = _GRUPO_ANP.get(grupo, [])
    if not produtos or df_anp.empty:
        return None
    sub = df_anp[(df_anp["uf"] == uf) & (df_anp["produto"].isin(produtos))]
    if sub.empty:
        sub = df_anp[df_anp["produto"].isin(produtos)]
    return float(sub["preco"].mean()) if not sub.empty else None


@router.get("")
def get_alertas():
    """Gera alertas automáticos baseados em anomalias reais de preço, consumo e duplicidade."""
    try:
        df = cache.get_df("transacoes")
        if df.empty:
            return []

        hoje = datetime.now()
        alertas = []

        # ── 1. Preço Acima da ANP (últimos 15 dias) ───────────────────────
        try:
            df_anp = get_anp_df()
            if not df_anp.empty:
                janela = hoje - timedelta(days=15)
                df_rec = df[df["data_transacao"] >= janela].copy()
                df_rec = df_rec[df_rec["litragem"] > 0].copy()
                df_rec["preco_unit"] = df_rec["valor"] / df_rec["litragem"]
                df_rec["grupo"] = df_rec["nome_combustivel"].str.lower().map(FUEL_GROUP_MAP).fillna("Outros")

                # Constrói lookup vetorizado: (uf, grupo) → preço médio ANP
                lookup_frames = []
                for grupo, produtos in _GRUPO_ANP.items():
                    if not produtos:
                        continue
                    sub = df_anp[df_anp["produto"].isin(produtos)]
                    if sub.empty:
                        continue
                    # Preço por UF
                    por_uf = sub.groupby("uf")["preco"].mean().reset_index()
                    por_uf["grupo"] = grupo
                    lookup_frames.append(por_uf)
                    # Fallback nacional (uf="_nacional")
                    nacional = pd.DataFrame([{"uf": "_nacional", "preco": float(sub["preco"].mean()), "grupo": grupo}])
                    lookup_frames.append(nacional)

                if lookup_frames:
                    lookup = pd.concat(lookup_frames, ignore_index=True).rename(columns={"preco": "anp_ref", "uf": "uf_posto"})

                    # Merge por UF+grupo; quem não casar usa fallback nacional
                    df_merged = df_rec.merge(lookup[lookup["uf_posto"] != "_nacional"], on=["uf_posto", "grupo"], how="left")
                    nac = lookup[lookup["uf_posto"] == "_nacional"].rename(columns={"uf_posto": "_uf_nac"}).drop(columns=["_uf_nac"])
                    sem_ref = df_merged["anp_ref"].isna()
                    if sem_ref.any():
                        nac_map = nac.set_index("grupo")["anp_ref"].to_dict()
                        df_merged.loc[sem_ref, "anp_ref"] = df_merged.loc[sem_ref, "grupo"].map(nac_map)

                    df_caros = df_merged[
                        df_merged["anp_ref"].notna() & (df_merged["preco_unit"] > df_merged["anp_ref"] * 1.08)
                    ].copy()
                    df_caros["desvio_pct"] = ((df_caros["preco_unit"] / df_caros["anp_ref"]) - 1) * 100

                    if not df_caros.empty:
                        df_caros = df_caros.sort_values("desvio_pct", ascending=False)
                        caros_ord = [
                            {
                                "posto": r["razao_social_posto"],
                                "placa": r["placa"],
                                "preco_pago": round(r["preco_unit"], 3),
                                "preco_anp": round(r["anp_ref"], 3),
                                "desvio_pct": round(r["desvio_pct"], 1),
                                "grupo": r["grupo"],
                                "uf": r["uf_posto"],
                            }
                            for _, r in df_caros.head(5).iterrows()
                        ]
                        total = len(df_caros)
                        alertas.append({
                            "id": "preco_elevado",
                            "tipo": "preco",
                            "nivel": "critico",
                            "titulo": f"Preços Acima do Mercado ({total} abastecimentos)",
                            "descricao": (
                                f"{total} abastecimentos nos últimos 15 dias com preço > 8% acima da ANP. "
                                f"Maior desvio: {caros_ord[0]['posto']} — {caros_ord[0]['desvio_pct']:+.1f}% "
                                f"(pago R${caros_ord[0]['preco_pago']:.3f} vs ANP R${caros_ord[0]['preco_anp']:.3f})."
                            ),
                            "detalhes": caros_ord,
                        })
        except Exception as e:
            logger.error(f"Alertas (preço): {e}")

        # ── 2. Consumo Anormal — KM/L < 70% da média histórica do veículo ──
        try:
            df_mes = df[
                (df["data_transacao"].dt.month == hoje.month) &
                (df["data_transacao"].dt.year == hoje.year)
            ]
            placas_ativas = df_mes["placa"].unique()
            anomalias_kml = []

            for placa in placas_ativas:
                df_v = df[df["placa"] == placa].sort_values("data_transacao")
                df_v = df_v[df_v["hodometro"] > 0].copy()
                if len(df_v) < 5:
                    continue
                df_v["km_diff"] = df_v["hodometro"].diff()
                validos = df_v[
                    (df_v["km_diff"] > 0) & (df_v["km_diff"] < 2000) & (df_v["litragem"] > 0)
                ].copy()
                if len(validos) < 4:
                    continue
                validos["kml"] = validos["km_diff"] / validos["litragem"]
                media_hist = float(validos.iloc[:-1]["kml"].mean())
                kml_recente = float(validos.iloc[-1]["kml"])
                if media_hist > 0 and kml_recente < media_hist * 0.70:
                    anomalias_kml.append({
                        "placa": placa,
                        "kml_atual": round(kml_recente, 2),
                        "kml_medio": round(media_hist, 2),
                        "desvio_pct": round((kml_recente / media_hist - 1) * 100, 1),
                    })

            if anomalias_kml:
                anomalias_kml.sort(key=lambda x: x["desvio_pct"])
                alertas.append({
                    "id": "consumo_anormal",
                    "tipo": "frota",
                    "nivel": "atencao",
                    "titulo": f"{len(anomalias_kml)} Veículo(s) com Queda de Eficiência",
                    "descricao": (
                        f"KM/L ≥ 30% abaixo da média histórica do veículo. "
                        f"Pior caso: {anomalias_kml[0]['placa']} — "
                        f"{anomalias_kml[0]['kml_atual']} km/L (média: {anomalias_kml[0]['kml_medio']} km/L)."
                    ),
                    "detalhes": anomalias_kml[:5],
                })
        except Exception as e:
            logger.error(f"Alertas (consumo): {e}")

        # ── 3. Abastecimento Duplicado (mesma placa, mesmo dia, mesmo grupo) ──
        try:
            janela_dup = hoje - timedelta(days=7)
            df_rec2 = df[df["data_transacao"] >= janela_dup].copy()
            df_rec2["grupo"] = df_rec2["nome_combustivel"].str.lower().map(FUEL_GROUP_MAP).fillna("Outros")
            df_rec2 = df_rec2[df_rec2["grupo"].isin(["Diesel", "Gasolina", "Álcool"])]
            df_rec2["data"] = df_rec2["data_transacao"].dt.date
            duplicados = df_rec2.groupby(["placa", "data", "grupo"]).size().reset_index(name="count")
            duplicados = duplicados[duplicados["count"] >= 2]
            if not duplicados.empty:
                casos = duplicados.to_dict(orient="records")
                alertas.append({
                    "id": "abastecimento_duplicado",
                    "tipo": "frota",
                    "nivel": "atencao",
                    "titulo": f"{len(casos)} Caso(s) de Abastecimento Duplo (7 dias)",
                    "descricao": (
                        f"Mesma placa abasteceu o mesmo tipo de combustível 2x no mesmo dia. "
                        f"Exemplo: {casos[0]['placa']} — {casos[0]['grupo']} em {casos[0]['data']}."
                    ),
                    "detalhes": casos[:5],
                })
        except Exception as e:
            logger.error(f"Alertas (duplicado): {e}")

        # ── 4. Projeção de gasto acima da média histórica (> 10%) ─────────
        try:
            df_mes2 = df[
                (df["data_transacao"].dt.month == hoje.month) &
                (df["data_transacao"].dt.year == hoje.year)
            ]
            inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            passado = df[df["data_transacao"] < inicio_mes]
            if not df_mes2.empty and not passado.empty:
                mensal = passado.groupby(passado["data_transacao"].dt.to_period("M"))["valor"].sum()
                media_hist = float(mensal.tail(3).mean())
                # Projeção simples por run-rate
                dias_corridos = max(1, hoje.day)
                dias_mes = pd.Period(hoje.strftime("%Y-%m"), freq="D").days_in_month
                run_rate = float(df_mes2["valor"].sum()) / dias_corridos * dias_mes
                if media_hist > 0 and run_rate > media_hist * 1.10:
                    desvio = round((run_rate / media_hist - 1) * 100, 1)
                    alertas.append({
                        "id": "projecao_alta",
                        "tipo": "financeiro",
                        "nivel": "atencao",
                        "titulo": f"Projeção do Mês +{desvio}% vs Média Histórica",
                        "descricao": (
                            f"Run-rate atual projeta R$ {run_rate:,.0f} vs média de "
                            f"R$ {media_hist:,.0f} dos últimos 3 meses."
                        ),
                        "detalhes": {
                            "projecao_run_rate": round(run_rate, 0),
                            "media_3_meses": round(media_hist, 0),
                            "desvio_pct": desvio,
                        },
                    })
        except Exception as e:
            logger.error(f"Alertas (projeção): {e}")

        if not alertas:
            alertas.append({
                "id": "ok",
                "tipo": "info",
                "nivel": "info",
                "titulo": "Operação Normal",
                "descricao": "Nenhuma anomalia relevante detectada nos últimos 15 dias.",
                "detalhes": [],
            })

        return alertas

    except Exception as e:
        logger.error(f"Alertas (geral): {e}")
        return [{"id": "erro", "tipo": "erro", "nivel": "critico",
                 "titulo": "Erro no Monitoramento", "descricao": str(e), "detalhes": []}]
