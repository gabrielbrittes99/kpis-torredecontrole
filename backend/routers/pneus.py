"""
Módulo Pneus — Gestão de Pneus da Frota
Fonte: planilha 'Controle de Pneus.xlsx', aba 'Planilha1'.
"""
import logging
from typing import Optional
from datetime import timedelta

import pandas as pd
from fastapi import APIRouter, Query

from db_pneus import get_pneus_df, refresh_pneus_cache
from db_sqlserver import get_manutencao_df, get_trocas_pneu_df

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pneus", tags=["pneus"])


def _enrich_with_km_troca(df_pneus: pd.DataFrame, dias_tolerancia: int = 10) -> pd.DataFrame:
    """
    Cruza dados da planilha de pneus com os registros do SQL Server para capturar
    o OdometroConfirmado no momento de cada troca.

    Regras de cruzamento:
      - Placa deve ser igual (normalizada sem hífen)
      - Campo de data do SQL: DataEmissao
      - Janela de busca: SOMENTE para frente  →  [data_envio, data_envio + dias_tolerancia]
      - Condições SQL já pré-filtradas em get_trocas_pneu_df():
          * DescricaoItem contém 'SUBSTITUIR - PNEU' OU 'MONTAGEM DE PNEU'
          * TipoItem = 'Serviço'
      - Se houver mais de um match, usa o registro com DataEmissao mais próxima de data_envio
    """
    try:
        df_trocas = get_trocas_pneu_df()
        if df_trocas.empty:
            logger.info("Pneus: sem dados de trocas no SQL Server")
            df_pneus["km_troca"] = 0
            df_pneus["km_troca_origem"] = "sem dados"
            return df_pneus

        logger.info(f"Pneus: cruzando {len(df_pneus)} registros com {len(df_trocas)} trocas SQL")

        # Garante conversão de datas
        df_pneus["data_envio"] = pd.to_datetime(df_pneus["data_envio"], errors="coerce")
        df_trocas = df_trocas.copy()

        res_km: list = []
        res_origem: list = []
        res_data_emissao: list = []

        for _, row in df_pneus.iterrows():
            placa = row.get("placa")
            data_envio = row.get("data_envio")

            if pd.isna(data_envio) or not placa or str(placa).upper() in ("NAN", "", "NONE"):
                res_km.append(0)
                res_origem.append("sem data/placa")
                res_data_emissao.append(None)
                continue

            data_limite = data_envio + timedelta(days=dias_tolerancia)

            # Janela SOMENTE para frente: [data_envio, data_envio + 10 dias]
            match = df_trocas[
                (df_trocas["Placa"] == placa)
                & (df_trocas["DataEmissao"] >= data_envio)
                & (df_trocas["DataEmissao"] <= data_limite)
            ].copy()

            if not match.empty:
                # Mais próximo da data_envio
                match["diff"] = (match["DataEmissao"] - data_envio).dt.total_seconds().abs()
                melhor = match.sort_values("diff").iloc[0]
                km = melhor["KmTroca"]
                if km > 0:
                    res_km.append(km)
                    res_origem.append("sql")
                    res_data_emissao.append(melhor["DataEmissao"])
                else:
                    res_km.append(0)
                    res_origem.append("km_zero")
                    res_data_emissao.append(melhor["DataEmissao"])
            else:
                res_km.append(0)
                res_origem.append("nao_encontrado")
                res_data_emissao.append(None)

        df_pneus["km_troca"] = res_km
        df_pneus["km_troca_origem"] = res_origem
        df_pneus["km_troca_data_emissao"] = res_data_emissao

        encontrados = sum(1 for x in res_origem if x == "sql")
        km_zero = sum(1 for x in res_origem if x == "km_zero")
        nao_enc = sum(1 for x in res_origem if x == "nao_encontrado")
        logger.info(
            f"Pneus: KM troca — encontrados={encontrados} | km_zero={km_zero} | não_encontrado={nao_enc}"
        )

        return df_pneus

    except Exception as e:
        logger.error(f"Pneus: falha ao cruzar com KM de troca: {e}")
        df_pneus["km_troca"] = 0
        df_pneus["km_troca_origem"] = "erro"
        df_pneus["km_troca_data_emissao"] = None
        return df_pneus


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
# Tabela simplificada de IPCA Acumulado 12 meses (final de cada ano)
# Fonte aproximada: IBGE / Banco Central
IPCA_HISTORICO = {
    "2021": 10.06,
    "2022": 5.79,
    "2023": 4.62,
    "2024": 4.50  # Estimativa/Projeção
}

# IPP - Indústria de Fabricação de Produtos de Borracha e Plástico (IBGE)
# Valores aproximados para benchmark de mercado
IPP_BORRACHA = {
    "2021": 28.50,
    "2022": 11.20,
    "2023": -3.80, # Teve queda em alguns períodos de 2023
    "2024": 2.10
}


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

    # Enriquecer com KM de troca do SQL Server
    df = _enrich_with_km_troca(df)

    # Cálculo dos KPIs de Volume
    total_pneus = int(df["quan"].sum()) if "quan" in df.columns else 0
    total_valor = float(df["total"].sum()) if "total" in df.columns else 0
    placas = int(df["placa"].nunique()) if "placa" in df.columns else 0
    valor_medio = total_valor / total_pneus if total_pneus > 0 else 0
    ticket_medio_veiculo = total_valor / placas if placas > 0 else 0
    pneus_por_veiculo = total_pneus / placas if placas > 0 else 0

    # KPIs de KM (usando km_troca do SQL quando disponível)
    km_encontrados = df[df["km_troca_origem"] == "sql"]
    if not km_encontrados.empty and "km_troca" in km_encontrados.columns:
        km_media = km_encontrados["km_troca"].mean()
        km_min = km_encontrados["km_troca"].min()
        km_max = km_encontrados["km_troca"].max()
        km_mediano = km_encontrados["km_troca"].median()
        km_total_encontrados = len(km_encontrados)
    else:
        km_media = 0
        km_min = 0
        km_max = 0
        km_mediano = 0
        km_total_encontrados = 0

    # Contagem por estado (NOVO, RECAPADO, MEIA VIDA)
    novos = int(df[df["estado_pneu"].str.upper() == "NOVO"]["quan"].sum()) if "estado_pneu" in df.columns else 0
    recapados = int(df[df["estado_pneu"].str.upper() == "RECAPADO"]["quan"].sum()) if "estado_pneu" in df.columns else 0
    meia_vida = int(df[df["estado_pneu"].str.upper() == "MEIA VIDA"]["quan"].sum()) if "estado_pneu" in df.columns else 0

    # LÓGICA DE EVENTOS (Regra para todos os anos)
    df_eventos = df.groupby(["data_envio", "placa", "filial"]).agg(
        total_pneus_evento=("quan", "sum")
    ).reset_index()
    total_eventos = len(df_eventos)
    eventos_emerg = len(df_eventos[df_eventos["total_pneus_evento"] == 1])
    emergencia_pct = (eventos_emerg / total_eventos * 100) if total_eventos > 0 else 0

    return {
        "total_pneus": total_pneus,
        "total_valor": total_valor,
        "valor_medio": valor_medio,
        "ticket_medio_pneu": valor_medio,
        "ticket_medio_veiculo": ticket_medio_veiculo,
        "pneus_por_veiculo": round(pneus_por_veiculo, 1),
        "placas": placas,
        "km_media": round(km_media, 0),
        "km_min": round(km_min, 0),
        "km_max": round(km_max, 0),
        "km_mediano": round(km_mediano, 0),
        "km_encontrados": km_total_encontrados,
        "km_disponivel": km_total_encontrados > 0,
        "fornecedores": int(df["fornecedor"].nunique()) if "fornecedor" in df.columns else 0,
        "marcas": int(df["marca"].nunique()) if "marca" in df.columns else 0,
        "filiais": int(df["filial"].nunique()) if "filial" in df.columns else 0,
        "novos": novos,
        "recapados": recapados,
        "meia_vida": meia_vida,
        "emergencia_pct": round(emergencia_pct, 1)
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
    filial: Optional[str] = Query(default=None),
    marca: Optional[str] = Query(default=None),
    fornecedor: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df = get_pneus_df()
    if df.empty:
        return []
    df = _apply_filters(df, filial=filial, marca=marca, fornecedor=fornecedor, ano=ano, aro=aro, medida=medida)
    
    # Primeiro agrupamos por EVENTO DE COMPRA (Mesmo dia, mesma placa, mesma filial)
    eventos = df.groupby(["data_envio", "placa", "filial"]).agg(
        total_pneus=("quan", "sum"),
        valor_evento=("total", "sum")
    ).reset_index()
    
    # Um evento é emergência se apenas 1 pneu foi trocado naquele dia para aquele caminhão
    eventos["is_emergencia"] = eventos["total_pneus"] == 1
    
    # Agora consolidamos por FILIAL para o dashboard
    g = eventos.groupby("filial").agg(
        quantidade=("total_pneus", "sum"),
        valor=("valor_evento", "sum"),
        placas=("placa", "nunique"),
        eventos_emergencia=("is_emergencia", "sum"),
        total_eventos=("is_emergencia", "count")
    ).reset_index()
    
    # Cálculos de performance por filial
    g["valor_medio"] = (g["valor"] / g["quantidade"]).round(2)
    g["pneus_por_veiculo"] = (g["quantidade"] / g["placas"]).round(1)
    g["emergencia_pct"] = ((g["eventos_emergencia"] / g["total_eventos"]) * 100).round(1)
    
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
    return g.sort_values("valor", ascending=False).head(limit).to_dict(orient="records")


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: análise trimestral (Spend, Placas e Variação YoY)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/trimestres")
def get_trimestres(
    ano: Optional[str] = Query(default=None),
    filial: Optional[str] = Query(default=None),
    marca: Optional[str] = Query(default=None),
    fornecedor: Optional[str] = Query(default=None),
    aro: Optional[str] = Query(default=None),
    medida: Optional[str] = Query(default=None),
):
    df_raw = get_pneus_df()
    if df_raw.empty or not ano:
        return []

    try:
        ano_val = float(ano)
    except:
        return []

    # Mapeamento de meses para trimestres
    Q_MAP = {
        "JANEIRO": 1, "FEVEREIRO": 1, "MARÇO": 1,
        "ABRIL": 2, "MAIO": 2, "JUNHO": 2,
        "JULHO": 3, "AGOSTO": 3, "SETEMBRO": 3,
        "OUTUBRO": 4, "NOVEMBRO": 4, "DEZEMBRO": 4
    }

    def process_ano(target_ano):
        df = _apply_filters(df_raw, filial=filial, marca=marca, fornecedor=fornecedor, aro=aro, medida=medida)
        df = df[df["ano"] == target_ano].copy()
        if df.empty:
            return {q: {"valor": 0, "placas": 0} for q in [1, 2, 3, 4]}
        
        df["q"] = df["mes"].map(Q_MAP)
        res = df.groupby("q").agg(
            valor=("total", "sum"),
            placas=("placa", "nunique")
        ).to_dict(orient="index")
        
        # Garante que todos os trimestres existam
        for q in [1, 2, 3, 4]:
            if q not in res:
                res[q] = {"valor": 0, "placas": 0}
        return res

    try:
        ano_val = int(float(ano))
        ano_ant = str(ano_val - 1)
        taxa_inflacao = IPCA_HISTORICO.get(ano_ant, 4.50) / 100.0
        taxa_ipp = IPP_BORRACHA.get(ano_ant, 3.00) / 100.0
    except:
        taxa_inflacao = 0.045
        taxa_ipp = 0.03

    dados_atual = process_ano(ano_val)
    dados_anterior = process_ano(ano_val - 1)

    resultado = []
    for q in [1, 2, 3, 4]:
        val_at = dados_atual[q]["valor"]
        val_ant = dados_anterior[q]["valor"]
        plc_at = dados_atual[q]["placas"]
        plc_ant = dados_anterior[q]["placas"]
        
        # Variação Nominal (Mercado)
        diff_val_pct = 0
        if val_ant > 0:
            diff_val_pct = ((val_at - val_ant) / val_ant) * 100
        elif val_at > 0:
            diff_val_pct = 100

        # Variação Real (Descontando a Inflação do período)
        val_ant_ajustado = val_ant * (1 + taxa_inflacao)
        diff_real_pct = 0
        if val_ant_ajustado > 0:
            diff_real_pct = ((val_at - val_ant_ajustado) / val_ant_ajustado) * 100
        elif val_at > 0:
            diff_real_pct = 100

        # Eficiência vs Matéria Prima (IPP Borracha)
        val_ant_ipp = val_ant * (1 + taxa_ipp)
        diff_ipp_pct = 0
        if val_ant_ipp > 0:
            diff_ipp_pct = ((val_at - val_ant_ipp) / val_ant_ipp) * 100
        elif val_at > 0:
            diff_ipp_pct = 100

        diff_plc_pct = 0
        if plc_ant > 0:
            diff_plc_pct = ((plc_at - plc_ant) / plc_ant) * 100
        elif plc_at > 0:
            diff_plc_pct = 100

        resultado.append({
            "trimestre": f"{q}º Trimestre",
            "valor": _safe_round(val_at, 2),
            "placas": int(plc_at),
            "variacao_pct": _safe_round(diff_val_pct, 1),
            "variacao_real_pct": _safe_round(diff_real_pct, 1),
            "variacao_industria_pct": _safe_round(diff_ipp_pct, 1),
            "variacao_placas_pct": _safe_round(diff_plc_pct, 1),
            "ipca_periodo": _safe_round(taxa_inflacao * 100, 2),
            "ipp_periodo": _safe_round(taxa_ipp * 100, 2)
        })

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: Dashboard de Anomalias (Foco em Custo e Tempo no Eixo)
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/anomalias")
def anomalias_pneus(
    filial: Optional[str] = Query(default=None),
    ano: Optional[str] = Query(default=None),
):
    df_raw = get_pneus_df()
    if df_raw.empty:
        return {"destruidores": [], "prematuras": [], "resumo": {}}

    df = _apply_filters(df_raw, filial=filial)
    
    if ano:
        try:
            df_ano = df[df["ano"] == float(ano)].copy()
        except:
            df_ano = df.copy()
    else:
        df_ano = df.copy()

    # ── 1. RANKING DESTRUIDORES (EXCESSO DE PNEUS NO ANO) ───────────
    g_dest = df_ano.groupby(["placa", "veiculo", "filial"]).agg(
        total_pneus=("quan", "sum"),
        valor_total=("total", "sum")
    ).reset_index()
    
    def classificar_alarme(qtd):
        if qtd >= 12: return "CRÍTICO (>12 pneus)"
        if qtd >= 8: return "ALERTA (8 a 11 pneus)"
        return "NORMAL"

    g_dest["alerta_consumo"] = g_dest["total_pneus"].apply(classificar_alarme)
    destruidores = g_dest[g_dest["total_pneus"] >= 4].sort_values("total_pneus", ascending=False).head(30)
    
    destruidores_list = []
    for _, r in destruidores.iterrows():
        destruidores_list.append({
            "placa": str(r["placa"]),
            "veiculo": str(r["veiculo"]),
            "filial": str(r["filial"]),
            "total_pneus": int(r["total_pneus"]),
            "valor_total": _safe_round(r["valor_total"], 2),
            "alerta_consumo": r["alerta_consumo"]
        })

    # ── 2. TROCAS PREMATURAS (MESMO EIXO EM < 180 DIAS NA MESMA PLACA) ──
    # Ignoramos o filtro de ano inicial para ver a data da compra anterior
    df_hist = df.copy()
    df_hist["data_envio"] = pd.to_datetime(df_hist["data_envio"], errors="coerce")
    
    # Preencher eixos em branco para não perder o registro, mas agrupar separadamente
    df_hist["eixo"] = df_hist["eixo"].fillna("NÃO INFORMADO").astype(str)
    df_hist["eixo"] = df_hist["eixo"].replace(["nan", "", "None"], "NÃO INFORMADO")
    
    df_hist = df_hist.dropna(subset=["data_envio", "placa"])
    df_hist = df_hist.sort_values(["placa", "eixo", "data_envio"])
    
    trocas_suspeitas = []
    
    for (placa_id, eixo_id), grupo in df_hist.groupby(["placa", "eixo"]):
        # Ignorar se o eixo não foi informado (para não dar falso positivo)
        if eixo_id == "NÃO INFORMADO":
            continue
            
        if len(grupo) < 2:
            continue
            
        grupo = grupo.sort_values("data_envio").reset_index(drop=True)
        datas = grupo["data_envio"].tolist()
        
        for i in range(1, len(grupo)):
            d_atual = datas[i]
            d_ant = datas[i-1]
            diff_dias = (d_atual - d_ant).days
            
            # (15 a 180 dias PARA O MESMO EIXO = indício forte de morte prematura)
            if 15 <= diff_dias <= 180:
                row = grupo.iloc[i]
                trocas_suspeitas.append({
                    "placa": str(placa_id),
                    "data_anterior": str(d_ant)[:10],
                    "data_troca": str(d_atual)[:10],
                    "intervalo_dias": diff_dias,
                    "qtd_pneus_agora": int(row["quan"]),
                    "veiculo": str(row["veiculo"]),
                    "filial": str(row["filial"]),
                    "eixo": str(eixo_id),
                    "valor_perdido": _safe_round(row["total"], 2),
                    "motivo_suspeito": f"Morte Prematura ({eixo_id})" if diff_dias < 120 else f"Desgaste Acelerado ({eixo_id})"
                })
    
    # Se o ano foi filtrado, exibir o aviso apenas se a data_troca ocorrer no ano avaliado
    if ano:
        suspeitas_filtradas = [t for t in trocas_suspeitas if t["data_troca"].startswith(ano)]
    else:
        suspeitas_filtradas = trocas_suspeitas
        
    suspeitas_filtradas.sort(key=lambda x: x["intervalo_dias"])
    
    resumo = {
        "total_acima_media": len([d for d in destruidores_list if d["alerta_consumo"] != "NORMAL"]),
        "total_trocas_prematuras": len(suspeitas_filtradas),
        "valor_potencial_desperdicio": sum(t["valor_perdido"] for t in suspeitas_filtradas)
    }

    return {
        "destruidores": destruidores_list,
        "prematuras": suspeitas_filtradas[:100], # Top 100 mais críticas
        "resumo": resumo
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT: refresh cache
# ═══════════════════════════════════════════════════════════════════════════
@router.post("/cache/refresh")
def refresh_cache():
    return refresh_pneus_cache()
