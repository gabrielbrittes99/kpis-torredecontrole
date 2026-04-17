"""
Conexão com SQL Server (BlueFleet — dados de veículos, filiais e manutenção).
Usa pymssql — sem dependência de driver ODBC do sistema operacional.

Tabelas relevantes:
  Veiculos               — cadastro, odômetro, tanque, filial operacional
  OcorrenciasManutencao  — abertura de ocorrências de manutenção (42k+ registros)
  OrdensServico          — ordens de serviço com valor e fornecedor (267k+ registros)
  ItensOrdemServico      — itens detalhados por OS, com GrupoDespesa e ValorTotal (770k+)
  vw_CustosManutencaoConcluida — view de NFs concluídas com custo por placa/filial (84k+)

Nota: placas no SQL Server usam hífen (ex: "BCQ-7B53") — normalizamos para sem hífen.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import pymssql
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Cache de veículos ────────────────────────────────────────────────────────
_veiculos_cache: Optional[pd.DataFrame] = None
_veiculos_cache_ts: Optional[datetime] = None
_VEICULOS_TTL = timedelta(hours=6)

# ── Cache de manutenção ──────────────────────────────────────────────────────
_manutencao_cache: Optional[pd.DataFrame] = None
_manutencao_cache_ts: Optional[datetime] = None
_MANUTENCAO_TTL = timedelta(hours=1)


def get_sqlserver_conn() -> pymssql.Connection:
    host = os.getenv("SQLSERVER_HOST")
    port = int(os.getenv("SQLSERVER_PORT", "1433"))
    database = os.getenv("SQLSERVER_DB")
    user = os.getenv("SQLSERVER_USER")
    password = os.getenv("SQLSERVER_PASSWORD")

    if not all([host, database, user, password]):
        raise RuntimeError(
            "Credenciais SQL Server não configuradas. "
            "Preencha SQLSERVER_HOST, SQLSERVER_DB, SQLSERVER_USER e SQLSERVER_PASSWORD no .env"
        )

    return pymssql.connect(
        server=host,
        port=port,
        database=database,
        user=user,
        password=password,
        timeout=15,
        login_timeout=10,
    )


def _norm_placa(placa: str) -> str:
    """Remove hífen e normaliza para maiúsculo (padrão TruckPag)."""
    return str(placa or "").upper().replace("-", "").strip()


def get_veiculos_df() -> pd.DataFrame:
    """
    Retorna DataFrame com dados de veículos do SQL Server.
    Cache de 6h. Campos principais: Placa, TanqueLitros, FilialOperacional,
    Modelo, Montadora, AnoModelo, SituacaoVeiculo, OdometroConfirmado,
    UltimaManutencao, UltimaManutencaoPreventiva, GrupoVeiculo.
    """
    global _veiculos_cache, _veiculos_cache_ts
    agora = datetime.now()
    if (
        _veiculos_cache is None
        or _veiculos_cache_ts is None
        or (agora - _veiculos_cache_ts) > _VEICULOS_TTL
    ):
        try:
            conn = get_sqlserver_conn()
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT
                    Placa,
                    Modelo,
                    Montadora,
                    AnoModelo,
                    AnoFabricacao,
                    TanqueLitros,
                    FilialOperacional,
                    IdFilialOperacional,
                    SituacaoVeiculo,
                    GrupoVeiculo,
                    OdometroConfirmado,
                    OdometroInformado,
                    UltimaManutencao,
                    UltimaManutencaoPreventiva,
                    CustoTotalPorKmRodado,
                    KmUltimaManutencaoPreventiva
                FROM Veiculos
            """)
            rows = cursor.fetchall()
            conn.close()
            df = pd.DataFrame(rows)
            df["Placa"] = df["Placa"].apply(_norm_placa)
            df["TanqueLitros"] = pd.to_numeric(df["TanqueLitros"], errors="coerce")
            df["OdometroConfirmado"] = pd.to_numeric(df["OdometroConfirmado"], errors="coerce")
            _veiculos_cache = df
            _veiculos_cache_ts = agora
            logger.info(f"SQL Server: {len(df)} veículos carregados")
        except Exception as e:
            logger.warning(f"SQL Server: falha ao carregar veículos: {e}")
            if _veiculos_cache is not None:
                return _veiculos_cache
            return pd.DataFrame(columns=[
                "Placa", "Modelo", "Montadora", "AnoModelo", "TanqueLitros",
                "FilialOperacional", "IdFilialOperacional", "SituacaoVeiculo",
                "GrupoVeiculo", "OdometroConfirmado",
            ])
    return _veiculos_cache


def get_manutencao_df() -> pd.DataFrame:
    """
    Retorna DataFrame de itens de manutenção de veículos Gritsch.
    Fonte: ItensOrdemServico filtrado por FilialOperacional GRITSCH.
    Cache de 1h.

    Campos principais:
      Placa, Tipo, Motivo, GrupoDespesa, DescricaoItem, TipoItem,
      Fornecedor, ValorTotal, Quantidade, ValorUnitario,
      DataCriacaoOcorrencia, DataConclusaoOcorrencia, SituacaoOcorrencia,
      FilialOperacional, IdFilialOperacional, SituacaoOrdemServico,
      OrdemServico, Ocorrencia
    """
    global _manutencao_cache, _manutencao_cache_ts
    agora = datetime.now()
    if (
        _manutencao_cache is None
        or _manutencao_cache_ts is None
        or (agora - _manutencao_cache_ts) > _MANUTENCAO_TTL
    ):
        try:
            conn = get_sqlserver_conn()
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT
                    ios.Placa,
                    ios.Tipo,
                    ios.Motivo,
                    ios.GrupoDespesa,
                    ios.IdGrupoDespesa,
                    ios.Categoria,
                    ios.Despesa,
                    ios.DescricaoItem,
                    ios.TipoItem,
                    ios.Quantidade,
                    ios.ValorUnitario,
                    ios.ValorTotal,
                    ios.ValorReembolsavel,
                    ios.Fornecedor,
                    ios.OrdemServico,
                    ios.Ocorrencia,
                    ios.DataCriacaoOcorrencia,
                    ios.DataConclusaoOcorrencia,
                    ios.SituacaoOcorrencia,
                    ios.SituacaoOrdemServico,
                    ios.FilialOperacional,
                    ios.IdUnidadeDeFaturamento  AS IdFilialOperacional,
                    ios.ModeloVeiculo
                FROM ItensOrdemServico ios
                WHERE ios.FilialOperacional LIKE '%GRITSCH%'
                  AND ios.Tipo NOT IN ('Despesa', 'Devolução')
                  AND ios.ValorTotal > 0
            """)
            rows = cursor.fetchall()
            conn.close()
            df = pd.DataFrame(rows)
            if not df.empty:
                df["Placa"] = df["Placa"].apply(_norm_placa)
                df["ValorTotal"] = pd.to_numeric(df["ValorTotal"], errors="coerce").fillna(0)
                df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0)
                df["ValorUnitario"] = pd.to_numeric(df["ValorUnitario"], errors="coerce").fillna(0)
            _manutencao_cache = df
            _manutencao_cache_ts = agora
            logger.info(f"SQL Server: {len(df)} itens de manutenção carregados")
        except Exception as e:
            logger.warning(f"SQL Server: falha ao carregar manutenção: {e}")
            if _manutencao_cache is not None:
                return _manutencao_cache
            return pd.DataFrame(columns=[
                "Placa", "Tipo", "Motivo", "GrupoDespesa", "DescricaoItem",
                "ValorTotal", "DataCriacaoOcorrencia", "DataConclusaoOcorrencia",
                "SituacaoOcorrencia", "FilialOperacional",
            ])
    return _manutencao_cache


def get_custos_matriz_df(ano_mes: str) -> pd.DataFrame:
    """
    Retorna custos alocados a GRITSCH - MATRIZ (A DEFINIR no BlueFleet) para um mês.
    Reutiliza o cache de get_manutencao_df() — sem nova query ao SQL Server.

    Categoriza os itens em:
      manutencao  — manutenção geral
      combustivel — itens com 'COMBUSTÍVEL' no GrupoDespesa
      arla        — itens com 'ARLA' no GrupoDespesa

    Parâmetro: ano_mes = "2026-03"
    """
    df = get_manutencao_df()
    if df.empty:
        return pd.DataFrame()

    # Filtra filiais "A DEFINIR" — são as que virariam GRITSCH - MATRIZ no FKM
    mask = df["FilialOperacional"].str.contains("DEFINIR", case=False, na=False)
    df_mat = df[mask].copy()
    if df_mat.empty:
        return df_mat

    # Filtra pelo mês usando DataCriacaoOcorrencia
    ano, mes = int(ano_mes.split("-")[0]), int(ano_mes.split("-")[1])
    df_mat["DataCriacaoOcorrencia"] = pd.to_datetime(df_mat["DataCriacaoOcorrencia"], errors="coerce")
    df_mat = df_mat[
        (df_mat["DataCriacaoOcorrencia"].dt.year == ano) &
        (df_mat["DataCriacaoOcorrencia"].dt.month == mes)
    ].copy()

    # Categoria de custo
    def _cat(grp: str) -> str:
        g = str(grp).upper()
        if "COMBUSTÍVEL" in g or "COMBUSTIVEL" in g:
            return "combustivel"
        if "ARLA" in g:
            return "arla"
        return "manutencao"

    df_mat["_categoria"] = df_mat["GrupoDespesa"].apply(_cat)
    return df_mat


# ── Cache de trocas de pneu ─────────────────────────────────────────────────
_trocas_pneu_cache: Optional[pd.DataFrame] = None
_trocas_pneu_cache_ts: Optional[datetime] = None
_TROCAS_PNEU_TTL = timedelta(hours=6)


def get_filiais_no_mes(ano_mes: str) -> pd.DataFrame:
    """
    Retorna a filial de cada veículo no final do mês indicado,
    usando a tabela de movimentações do SQL Server.

    Para cada placa, pega o último movimento cuja Data_da_movimentacao
    seja <= último dia do mês → Unidade_de_Destino é a filial do veículo
    naquele mês.

    Placas sem nenhum movimento até o fim do mês não aparecem
    no resultado — para essas, o chamador deve usar FilialOperacional
    da tabela Veiculos como fallback.

    Parâmetro: ano_mes = "2026-03"
    Retorna DataFrame com colunas: Placa, FilialNoMes
    """
    import calendar
    ano, mes = int(ano_mes.split("-")[0]), int(ano_mes.split("-")[1])
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    data_limite = f"{ano}-{mes:02d}-{ultimo_dia} 23:59:59"

    try:
        conn = get_sqlserver_conn()
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT placa, Unidade_de_Destino AS FilialNoMes
            FROM (
                SELECT
                    placa,
                    Unidade_de_Destino,
                    ROW_NUMBER() OVER (
                        PARTITION BY placa
                        ORDER BY Data_da_movimentação DESC
                    ) AS rn
                FROM movimentos
                WHERE Data_da_movimentação <= %s
                  AND unidade_movimentada = 'OPERAÇÃO'
            ) t
            WHERE rn = 1
        """, (data_limite,))
        rows = cursor.fetchall()
        conn.close()
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["Placa", "FilialNoMes"])
        # Normaliza nomes de coluna (pymssql retorna como estão no SQL)
        df.columns = [c if c != "placa" else "Placa" for c in df.columns]
        # A coluna do alias pode vir como "FilialNoMes" ou "FilialNoMes"
        placa_col = next((c for c in df.columns if c.lower() == "placa"), None)
        if placa_col and placa_col != "Placa":
            df = df.rename(columns={placa_col: "Placa"})
        df["Placa"] = df["Placa"].apply(_norm_placa)
        return df
    except Exception as e:
        logger.warning(f"SQL Server: falha ao buscar movimentações do mês {ano_mes}: {e}")
        return pd.DataFrame(columns=["Placa", "FilialNoMes"])


def get_trocas_pneu_df() -> pd.DataFrame:
    """
    Retorna DataFrame de trocas de pneu (Ordens de Serviço cujo item
    contém 'SUBSTITUIR - PNEU' ou 'MONTAGEM DE PNEU', tipo Serviço).
    Usado para cruzar km de troca com a planilha de controle de pneus.
    Cache de 6h.
    """
    global _trocas_pneu_cache, _trocas_pneu_cache_ts
    agora = datetime.now()
    if (
        _trocas_pneu_cache is not None
        and _trocas_pneu_cache_ts is not None
        and (agora - _trocas_pneu_cache_ts) <= _TROCAS_PNEU_TTL
    ):
        return _trocas_pneu_cache

    try:
        conn = get_sqlserver_conn()
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT
                ios.Placa,
                ios.DataConclusaoOcorrencia AS DataEmissao,
                v.OdometroConfirmado       AS KmTroca,
                ios.DescricaoItem,
                ios.OrdemServico
            FROM ItensOrdemServico ios
            LEFT JOIN Veiculos v ON v.Placa = ios.Placa
            WHERE ios.FilialOperacional LIKE '%GRITSCH%'
              AND ios.TipoItem = N'Serviço'
              AND (
                  ios.DescricaoItem LIKE '%SUBSTITUIR - PNEU%'
                  OR ios.DescricaoItem LIKE '%MONTAGEM DE PNEU%'
              )
              AND ios.DataConclusaoOcorrencia IS NOT NULL
        """)
        rows = cursor.fetchall()
        conn.close()
        df = pd.DataFrame(rows)
        if not df.empty:
            df["Placa"] = df["Placa"].apply(_norm_placa)
            df["DataEmissao"] = pd.to_datetime(df["DataEmissao"], errors="coerce")
            df["KmTroca"] = pd.to_numeric(df["KmTroca"], errors="coerce").fillna(0)
        _trocas_pneu_cache = df
        _trocas_pneu_cache_ts = agora
        logger.info(f"SQL Server: {len(df)} registros de trocas de pneu carregados")
    except Exception as e:
        logger.warning(f"SQL Server: falha ao carregar trocas de pneu: {e}")
        if _trocas_pneu_cache is not None:
            return _trocas_pneu_cache
        return pd.DataFrame(columns=["Placa", "DataEmissao", "KmTroca", "DescricaoItem", "OrdemServico"])
    return _trocas_pneu_cache
