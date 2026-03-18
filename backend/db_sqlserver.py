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
