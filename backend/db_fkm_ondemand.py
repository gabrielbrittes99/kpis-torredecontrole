"""
FKM On-Demand — Fechamento de Custos das Filiais gerado a partir dos bancos reais.

Fontes:
  SQL Server (BlueFleet)               → manutenção com FILIAL calculada por CTEs
  PostgreSQL Railway (TruckPag)        → combustível, km rodado, motorista
  DW torre.abastecimentos_diretos      → abastecimentos fora TruckPag (upload gestor)
  DW torre.veiculo_contrato            → vínculo placa → contrato validado pelo gestor

Expõe as mesmas funções que db_fkm.py (get_fkm_df / refresh_fkm_cache)
para que routers/fkm.py funcione sem alterações.

Cache de 1h com stale-on-error.
"""
import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_fkm_cache: Optional[pd.DataFrame] = None
_fkm_cache_ts: Optional[datetime] = None
_FKM_TTL = timedelta(hours=1)

# Colunas mínimas garantidas na saída — compatível com routers/fkm.py
_COLUNAS_SAIDA = [
    "placa", "ano_mes", "filial", "grupo_veiculo", "modelo_simplificado",
    "tp_combustivel", "contrato", "motorista_principal",
    "total_km", "litros_comb", "valor_comb", "media_kml", "comb_por_km",
    "arla", "manutencao", "rodas_pneus", "lataria_pintura",
    "total_geral_manutencao", "total", "man_por_km",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_sql(filename: str) -> str:
    """Carrega arquivo SQL da pasta backend/sql/."""
    path = Path(__file__).parent / "sql" / filename
    return path.read_text(encoding="utf-8")


def _periodo_atual() -> tuple[str, str]:
    """Retorna (date_from, date_to) para o mês corrente como strings 'YYYY-MM-DD'."""
    hoje = date.today()
    date_from = date(hoje.year, hoje.month, 1).isoformat()
    # date_to = primeiro dia do próximo mês (exclusivo)
    if hoje.month == 12:
        date_to = date(hoje.year + 1, 1, 1).isoformat()
    else:
        date_to = date(hoje.year, hoje.month + 1, 1).isoformat()
    return date_from, date_to


def _norm_placa(placa) -> str:
    return str(placa or "").upper().replace("-", "").strip()


def _ano_mes_atual() -> str:
    hoje = date.today()
    return f"{hoje.year}-{hoje.month:02d}"


# ── Fetch: SQL Server — manutenção ───────────────────────────────────────────

def _fetch_manutencao(date_from: str, date_to: str) -> pd.DataFrame:
    """Executa query de manutenção no SQL Server e retorna DataFrame bruto."""
    from db_sqlserver import get_sqlserver_conn
    sql = _load_sql("fkm_manutencao.sql")
    sql = sql.replace("{DATE_FROM}", f"'{date_from}'").replace("{DATE_TO}", f"'{date_to}'")
    try:
        conn = get_sqlserver_conn()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"FKM ondemand: falha SQL Server manutenção: {e}")
        return pd.DataFrame(columns=["Placa", "ano_mes", "FILIAL", "Natureza_Correta", "ValorTotal", "contrato"])

    if not rows:
        return pd.DataFrame(columns=["Placa", "ano_mes", "FILIAL", "Natureza_Correta", "ValorTotal", "contrato"])

    df = pd.DataFrame(rows)
    df["Placa"] = df["Placa"].apply(_norm_placa)
    df["ValorTotal"] = pd.to_numeric(df["ValorTotal"], errors="coerce").fillna(0.0)
    df["contrato"] = df["contrato"].fillna("").astype(str).str.strip()
    logger.info(f"FKM ondemand: {len(df)} itens de manutenção carregados ({date_from} → {date_to})")
    return df


def _aggregate_manutencao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivota os itens de manutenção para uma linha por (placa, ano_mes).
    Natureza_Correta mapeada para colunas: manutencao, rodas_pneus, lataria_pintura.
    FILIAL e contrato: valor mais frequente por (placa, ano_mes).
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "placa", "ano_mes", "filial", "contrato",
            "manutencao", "rodas_pneus", "lataria_pintura",
        ])

    NATUREZA_COL = {
        "03.03 - MANUTENÇÃO DE VEÍCULOS": "manutencao",
        "03.05 - RODAS E PNEUS":          "rodas_pneus",
        "03.02 - LATARIA E PINTURA":      "lataria_pintura",
    }

    df["_col"] = df["Natureza_Correta"].map(NATUREZA_COL).fillna("manutencao")

    # Pivot: soma ValorTotal por (placa, ano_mes, _col)
    pivot = (
        df.groupby(["Placa", "ano_mes", "_col"])["ValorTotal"]
        .sum()
        .unstack(fill_value=0.0)
        .reset_index()
    )
    pivot.columns.name = None
    pivot = pivot.rename(columns={"Placa": "placa"})

    # Garante que todas as colunas existam mesmo se nenhum item tiver aquela natureza
    for col in ["manutencao", "rodas_pneus", "lataria_pintura"]:
        if col not in pivot.columns:
            pivot[col] = 0.0

    # FILIAL e contrato: moda por (placa, ano_mes)
    meta = (
        df.groupby(["Placa", "ano_mes"])
        .agg(
            filial=("FILIAL", lambda x: x.mode().iloc[0] if not x.mode().empty else ""),
            contrato=("contrato", lambda x: x[x != ""].mode().iloc[0] if not x[x != ""].empty else ""),
        )
        .reset_index()
        .rename(columns={"Placa": "placa"})
    )

    result = pivot.merge(meta, on=["placa", "ano_mes"], how="left")
    result["filial"] = result["filial"].fillna("")
    result["contrato"] = result["contrato"].fillna("")
    return result


# ── Fetch: PostgreSQL — combustível TruckPag ─────────────────────────────────

def _fetch_tp_fuel(date_from: str, date_to: str) -> pd.DataFrame:
    """Executa query de combustível no PostgreSQL (TruckPag) e retorna por placa/mês."""
    from db import get_engine
    from sqlalchemy import text as sa_text
    sql = _load_sql("fkm_combustivel.sql")
    sql = sql.replace("{DATE_FROM}", f"'{date_from}'").replace("{DATE_TO}", f"'{date_to}'")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            df = pd.read_sql(sa_text(sql), conn)
    except Exception as e:
        logger.error(f"FKM ondemand: falha PostgreSQL combustível: {e}")
        return pd.DataFrame(columns=[
            "ano_mes", "placa", "km_rodado_no_mes", "litros_total",
            "media_km_l", "vlr_diesel", "vlr_arla",
            "litros_diesel", "litros_arla", "valor_total",
            "motorista_principal", "nome_combustivel_principal",
        ])

    df["placa"] = df["placa"].apply(_norm_placa)
    for col in ["km_rodado_no_mes", "litros_total", "media_km_l",
                "vlr_diesel", "vlr_arla", "litros_diesel", "litros_arla", "valor_total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    logger.info(f"FKM ondemand: {len(df)} linhas TruckPag ({date_from} → {date_to})")
    return df


# ── Fetch: DW torre — abastecimento direto ────────────────────────────────────

def _fetch_direto(ano_mes: str) -> pd.DataFrame:
    """
    Lê abastecimentos fora TruckPag de torre.abastecimentos_diretos.
    Retorna por placa/mês — mesma estrutura que _fetch_tp_fuel para merge fácil.
    """
    try:
        from db_dw import get_dw_engine
        engine = get_dw_engine()
        sql = """
            SELECT
                placa,
                ano_mes,
                SUM(litros)                                                       AS litros_total,
                SUM(valor)                                                        AS valor_total,
                SUM(valor)  FILTER (WHERE nome_combustivel ILIKE '%%ARLA%%')      AS vlr_arla,
                SUM(litros) FILTER (WHERE nome_combustivel ILIKE '%%ARLA%%')      AS litros_arla,
                SUM(valor)  FILTER (WHERE nome_combustivel NOT ILIKE '%%ARLA%%')  AS vlr_diesel,
                SUM(litros) FILTER (WHERE nome_combustivel NOT ILIKE '%%ARLA%%')  AS litros_diesel,
                MODE() WITHIN GROUP (ORDER BY motorista)                          AS motorista_principal
            FROM torre.abastecimentos_diretos
            WHERE ano_mes = %(ano_mes)s
            GROUP BY placa, ano_mes
        """
        df = pd.read_sql(sql, engine, params={"ano_mes": ano_mes})
        df["placa"] = df["placa"].apply(_norm_placa)
        for col in ["litros_total", "valor_total", "vlr_arla", "litros_arla", "vlr_diesel", "litros_diesel"]:
            df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0.0)
        logger.info(f"FKM ondemand: {len(df)} linhas abastecimento direto ({ano_mes})")
        return df
    except Exception as e:
        logger.warning(f"FKM ondemand: falha abastecimento direto ({ano_mes}): {e}")
        return pd.DataFrame(columns=[
            "placa", "ano_mes", "litros_total", "valor_total",
            "vlr_arla", "litros_arla", "vlr_diesel", "litros_diesel",
            "motorista_principal",
        ])


# ── Fetch: DW torre — contrato por placa ─────────────────────────────────────

def _fetch_contratos(ano_mes: str) -> pd.DataFrame:
    """
    Lê torre.veiculo_contrato e retorna o contrato vigente no mês para cada placa.
    Vigente = vigencia_ini <= último dia do mês AND (vigencia_fim IS NULL OR vigencia_fim >= primeiro dia do mês)
    """
    try:
        from db_dw import get_dw_engine
        engine = get_dw_engine()
        ano, mes = int(ano_mes[:4]), int(ano_mes[5:7])
        import calendar
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        primeiro_dia = f"{ano_mes}-01"
        ult_dia_str = f"{ano_mes}-{ultimo_dia:02d}"

        sql = """
            SELECT DISTINCT ON (placa)
                placa,
                contrato,
                filial
            FROM torre.veiculo_contrato
            WHERE vigencia_ini <= %(ult_dia)s
              AND (vigencia_fim IS NULL OR vigencia_fim >= %(prim_dia)s)
            ORDER BY placa, vigencia_ini DESC
        """
        df = pd.read_sql(sql, engine, params={"ult_dia": ult_dia_str, "prim_dia": primeiro_dia})
        df["placa"] = df["placa"].apply(_norm_placa)
        df["contrato"] = df["contrato"].fillna("").astype(str).str.strip()
        df["filial_contrato"] = df["filial"].fillna("").astype(str).str.strip()
        logger.info(f"FKM ondemand: {len(df)} vínculos placa→contrato ({ano_mes})")
        return df[["placa", "contrato", "filial_contrato"]]
    except Exception as e:
        logger.warning(f"FKM ondemand: falha contrato por placa ({ano_mes}): {e}")
        return pd.DataFrame(columns=["placa", "contrato", "filial_contrato"])


# ── Merge: combina TruckPag + direto ─────────────────────────────────────────

def _merge_fuel(df_tp: pd.DataFrame, df_direto: pd.DataFrame, ano_mes: str) -> pd.DataFrame:
    """
    Soma TruckPag + abastecimento direto por placa.
    Retorna DataFrame com colunas normalizadas para o merge final.
    """
    # Garante que ambos têm ano_mes
    if not df_tp.empty and "ano_mes" not in df_tp.columns:
        df_tp["ano_mes"] = ano_mes
    if not df_direto.empty and "ano_mes" not in df_direto.columns:
        df_direto["ano_mes"] = ano_mes

    cols_num = ["litros_total", "valor_total", "vlr_diesel", "vlr_arla",
                "litros_diesel", "litros_arla"]

    def _ensure_cols(df, cols):
        for c in cols:
            if c not in df.columns:
                df[c] = 0.0
        return df

    df_tp = _ensure_cols(df_tp.copy(), cols_num)
    df_direto = _ensure_cols(df_direto.copy(), cols_num)

    # Filtra só o mês corrente nas duas fontes
    if not df_tp.empty:
        df_tp = df_tp[df_tp["ano_mes"] == ano_mes].copy()
    if not df_direto.empty:
        df_direto = df_direto[df_direto["ano_mes"] == ano_mes].copy()

    # km_rodado vem só do TruckPag (calculado via hodômetro LAG); direto não tem km.
    # Preserva antes do concat para não perder no agrupamento.
    km_tp: dict = {}
    if not df_tp.empty and "km_rodado_no_mes" in df_tp.columns:
        km_tp = df_tp.set_index("placa")["km_rodado_no_mes"].to_dict()

    # Garante que df_direto não polui km_rodado_no_mes
    df_direto["km_rodado_no_mes"] = 0.0
    if "km_rodado_no_mes" not in df_tp.columns:
        df_tp["km_rodado_no_mes"] = 0.0

    # Garante nome_combustivel_principal em ambos
    if "nome_combustivel_principal" not in df_tp.columns:
        df_tp["nome_combustivel_principal"] = ""
    if "nome_combustivel_principal" not in df_direto.columns:
        df_direto["nome_combustivel_principal"] = ""
    if "motorista_principal" not in df_direto.columns:
        df_direto["motorista_principal"] = ""

    combined = pd.concat([df_tp, df_direto], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=[
            "placa", "ano_mes", "km_rodado_no_mes", "litros_comb",
            "valor_comb", "arla", "litros_diesel", "litros_arla",
            "motorista_principal", "nome_combustivel_principal",
        ])

    def _mode_str(s):
        vals = s.dropna().replace("", pd.NA).dropna()
        return vals.mode().iloc[0] if not vals.empty else ""

    agg = (
        combined.groupby(["placa", "ano_mes"])
        .agg(
            litros_comb=("litros_total", "sum"),
            valor_comb=("vlr_diesel", "sum"),
            arla=("vlr_arla", "sum"),
            litros_diesel=("litros_diesel", "sum"),
            litros_arla=("litros_arla", "sum"),
            motorista_principal=("motorista_principal", _mode_str),
            nome_combustivel_principal=("nome_combustivel_principal", _mode_str),
        )
        .reset_index()
    )

    # Restaura km do TruckPag (não somado para não duplicar)
    agg["km_rodado_no_mes"] = agg["placa"].map(km_tp).fillna(0.0)

    return agg


# ── Enriquecimento de metadados ───────────────────────────────────────────────

def _enrich_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preenche grupo_veiculo, modelo_simplificado e tp_combustivel
    usando get_veiculos_df() (SQL Server) e funções de config.
    """
    from db_sqlserver import get_veiculos_df
    from config import get_veiculo_group, get_fkm_grupo_display, get_fuel_group, IGNORAR_PLACAS, PLACAS_RENOMEADAS

    # Aplica renomeações e ignora placas fictícias
    df["placa"] = df["placa"].replace(PLACAS_RENOMEADAS)
    if IGNORAR_PLACAS:
        df = df[~df["placa"].isin(IGNORAR_PLACAS)].copy()

    veiculos = get_veiculos_df()
    if not veiculos.empty:
        v = veiculos[["Placa", "Modelo", "Montadora", "GrupoVeiculo"]].copy()
        v = v.drop_duplicates(subset=["Placa"], keep="first")
        v.columns = ["placa", "_modelo", "_marca", "_grupo_ss"]
        df = df.merge(v, on="placa", how="left")
        df = df.reset_index(drop=True)
    else:
        df["_modelo"] = ""
        df["_marca"] = ""
        df["_grupo_ss"] = ""

    # modelo_simplificado: prioriza SQL Server; fallback string vazia
    if "modelo_simplificado" not in df.columns:
        df["modelo_simplificado"] = ""
    mask_sem_modelo = df["modelo_simplificado"].str.strip() == ""
    df.loc[mask_sem_modelo, "modelo_simplificado"] = df.loc[mask_sem_modelo, "_modelo"].fillna("")

    # grupo_veiculo: prioriza SQL Server GrupoVeiculo → get_veiculo_group → ""
    if "grupo_veiculo" not in df.columns:
        df["grupo_veiculo"] = ""

    def _resolve_grupo(row):
        if row.get("grupo_veiculo", "").strip():
            return get_fkm_grupo_display(row["grupo_veiculo"])
        g_ss = str(row.get("_grupo_ss", "") or "").strip()
        if g_ss:
            return get_fkm_grupo_display(g_ss)
        return get_veiculo_group(
            str(row.get("_modelo", "") or ""),
            str(row.get("_marca", "") or ""),
            row["placa"],
        )

    df["grupo_veiculo"] = df.apply(_resolve_grupo, axis=1)

    # tp_combustivel: moda do nome_combustivel via get_fuel_group
    if "nome_combustivel_principal" in df.columns:
        df["tp_combustivel"] = df["nome_combustivel_principal"].fillna("").apply(
            lambda n: get_fuel_group(n) if n else ""
        )
    else:
        df["tp_combustivel"] = ""

    df = df.drop(columns=["_modelo", "_marca", "_grupo_ss", "nome_combustivel_principal"], errors="ignore")
    return df


# ── Merge final: manutenção + combustível ─────────────────────────────────────

def _merge_fkm(
    df_man: pd.DataFrame,
    df_fuel: pd.DataFrame,
    df_contratos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Outer join entre manutenção e combustível por (placa, ano_mes).
    Resolve filial e contrato, calcula métricas derivadas.
    """
    # Outer join
    df = pd.merge(df_man, df_fuel, on=["placa", "ano_mes"], how="outer")

    # Preenche nulos nas colunas de custo
    for col in ["manutencao", "rodas_pneus", "lataria_pintura",
                "km_rodado_no_mes", "litros_comb", "valor_comb", "arla"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Colunas de texto — garante existência
    for col in ["filial", "contrato", "motorista_principal"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    # Aplica contrato da tabela veiculo_contrato (fonte autoritativa)
    if not df_contratos.empty:
        df = df.merge(df_contratos[["placa", "contrato", "filial_contrato"]],
                      on="placa", how="left", suffixes=("", "_vc"))
        # Sobrescreve contrato se veiculo_contrato tiver vínculo
        mask_vc = df["contrato_vc"].fillna("").str.strip() != ""
        df.loc[mask_vc, "contrato"] = df.loc[mask_vc, "contrato_vc"]
        # Fallback de filial: SQL Server → veiculo_contrato → ""
        mask_sem_filial = df["filial"].str.strip() == ""
        df.loc[mask_sem_filial, "filial"] = df.loc[mask_sem_filial, "filial_contrato"].fillna("")
        df = df.drop(columns=["contrato_vc", "filial_contrato"], errors="ignore")

    # Enriquece modelo, grupo, tp_combustivel
    df = _enrich_metadata(df)

    # Renomeia colunas de fuel para padrão FKM
    df = df.rename(columns={
        "km_rodado_no_mes": "total_km",
        "litros_comb":      "litros_comb",  # já correto
    })

    if "litros_comb" not in df.columns and "litros_total" in df.columns:
        df = df.rename(columns={"litros_total": "litros_comb"})

    # Métricas derivadas
    df["total_km"] = pd.to_numeric(df.get("total_km", 0), errors="coerce").fillna(0.0)
    df["litros_comb"] = pd.to_numeric(df.get("litros_comb", 0), errors="coerce").fillna(0.0)
    df["valor_comb"] = pd.to_numeric(df.get("valor_comb", 0), errors="coerce").fillna(0.0)
    df["arla"] = pd.to_numeric(df.get("arla", 0), errors="coerce").fillna(0.0)
    df["manutencao"] = pd.to_numeric(df.get("manutencao", 0), errors="coerce").fillna(0.0)
    df["rodas_pneus"] = pd.to_numeric(df.get("rodas_pneus", 0), errors="coerce").fillna(0.0)
    df["lataria_pintura"] = pd.to_numeric(df.get("lataria_pintura", 0), errors="coerce").fillna(0.0)

    df["total_geral_manutencao"] = df["manutencao"] + df["rodas_pneus"] + df["lataria_pintura"]
    df["total"] = df["valor_comb"] + df["arla"] + df["total_geral_manutencao"]

    df["media_kml"] = df.apply(
        lambda r: round(r["total_km"] / r["litros_comb"], 2)
        if r["litros_comb"] > 0 and r["total_km"] > 0 else 0.0,
        axis=1,
    )
    df["comb_por_km"] = df.apply(
        lambda r: round(r["valor_comb"] / r["total_km"], 4)
        if r["total_km"] > 0 else 0.0,
        axis=1,
    )
    df["man_por_km"] = df.apply(
        lambda r: round(r["total_geral_manutencao"] / r["total_km"], 4)
        if r["total_km"] > 0 else 0.0,
        axis=1,
    )

    # Remove placas com placa vazia ou inválida
    df = df[df["placa"].str.len() >= 7].copy()

    # Exclui filiais fora do escopo Gritsch
    df = df[~df["filial"].str.upper().str.startswith("REFERÊNCIA")].copy()
    df = df[df["filial"].str.upper() != "VEÍCULOS VENDIDOS"].copy()

    # Garante todas as colunas de saída
    for col in _COLUNAS_SAIDA:
        if col not in df.columns:
            df[col] = "" if col in ["filial", "grupo_veiculo", "modelo_simplificado",
                                     "tp_combustivel", "contrato", "motorista_principal",
                                     "ano_mes"] else 0.0

    return df[_COLUNAS_SAIDA].reset_index(drop=True)


# ── Função pública: get_fkm_df ────────────────────────────────────────────────

def get_fkm_df() -> pd.DataFrame:
    """
    Retorna DataFrame FKM do mês corrente combinando SQL Server + TruckPag + Direto.
    Cache de 1h. Em caso de falha retorna cache anterior (se existir).
    """
    global _fkm_cache, _fkm_cache_ts
    agora = datetime.now()

    if (
        _fkm_cache is not None
        and _fkm_cache_ts is not None
        and (agora - _fkm_cache_ts) < _FKM_TTL
    ):
        return _fkm_cache

    try:
        date_from, date_to = _periodo_atual()
        ano_mes = _ano_mes_atual()

        logger.info(f"FKM ondemand: carregando dados {date_from} → {date_to}")

        # Busca paralela não é necessária — pymssql não é thread-safe por conexão;
        # executamos sequencialmente mas cada fetch tem timeout próprio.
        df_man_raw = _fetch_manutencao(date_from, date_to)
        df_man = _aggregate_manutencao(df_man_raw)

        df_tp = _fetch_tp_fuel(date_from, date_to)
        df_direto = _fetch_direto(ano_mes)
        df_fuel = _merge_fuel(df_tp, df_direto, ano_mes)

        df_contratos = _fetch_contratos(ano_mes)

        df = _merge_fkm(df_man, df_fuel, df_contratos)

        _fkm_cache = df
        _fkm_cache_ts = agora
        logger.info(
            f"FKM ondemand: {len(df)} linhas — "
            f"{df['placa'].nunique()} placas, {df['filial'].nunique()} filiais"
        )
        return df

    except Exception as e:
        logger.error(f"FKM ondemand: falha ao gerar fechamento: {e}", exc_info=True)
        if _fkm_cache is not None:
            logger.warning("FKM ondemand: retornando cache anterior")
            return _fkm_cache
        return pd.DataFrame(columns=_COLUNAS_SAIDA)


def get_fkm_df_completo() -> pd.DataFrame:
    """
    FKM completo: mês corrente (on-demand) + histórico (Excel xlsb).
    Usado por routers que precisam de tendência/evolução (manutencao, contratos, tco).
    Deduplica por (placa, ano_mes) priorizando on-demand.
    """
    df_atual = get_fkm_df()

    try:
        from db_fkm import get_fkm_df as get_fkm_historico
        df_hist = get_fkm_historico()
    except Exception as e:
        logger.warning(f"FKM completo: falha ao carregar histórico Excel: {e}")
        return df_atual

    if df_hist.empty:
        return df_atual

    # Remove do histórico os meses que já estão no on-demand
    meses_atuais = set(df_atual["ano_mes"].unique()) if not df_atual.empty else set()
    df_hist = df_hist[~df_hist["ano_mes"].isin(meses_atuais)].copy()

    # Aplica mesmos filtros de escopo Gritsch
    df_hist = df_hist[~df_hist["filial"].str.upper().str.startswith("REFERÊNCIA")]
    df_hist = df_hist[df_hist["filial"].str.upper() != "VEÍCULOS VENDIDOS"]

    # Garante colunas compatíveis
    for col in _COLUNAS_SAIDA:
        if col not in df_hist.columns:
            df_hist[col] = "" if col in [
                "filial", "grupo_veiculo", "modelo_simplificado",
                "tp_combustivel", "contrato", "motorista_principal", "ano_mes",
            ] else 0.0

    df_completo = pd.concat([df_hist[_COLUNAS_SAIDA], df_atual], ignore_index=True)

    # Deduplica: prioriza on-demand (está no final do concat)
    df_completo = df_completo.drop_duplicates(subset=["placa", "ano_mes"], keep="last")

    logger.info(
        f"FKM completo: {len(df_completo)} linhas — "
        f"{df_completo['ano_mes'].nunique()} meses, "
        f"{df_completo['placa'].nunique()} placas"
    )
    return df_completo.reset_index(drop=True)


def refresh_fkm_cache() -> dict:
    """Força recarregamento. Chamado via POST /api/fkm/cache/refresh."""
    global _fkm_cache_ts
    _fkm_cache_ts = None
    df = get_fkm_df()
    ano_mes = _ano_mes_atual()
    return {
        "linhas": len(df),
        "meses": [ano_mes] if not df.empty else [],
        "placas": int(df["placa"].nunique()),
        "filiais": sorted(df["filial"].dropna().unique().tolist()),
    }
