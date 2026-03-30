import pandas as pd
from typing import Optional, Any
from datetime import datetime, timedelta

def safe_round(val: Any, n: int = 2) -> Optional[float]:
    """Arredonda um valor de forma segura, retornando None se não for numérico."""
    try:
        f = float(val)
        return round(f, n) if f != 0 else 0.0
    except (ValueError, TypeError):
        return None

def norm_placa(placa: Any) -> str:
    """Normaliza a placa para o padrão TruckPag (maiúsculo, sem hífen, sem espaços)."""
    return str(placa or "").upper().replace("-", "").strip()

def apply_time_filters(
    df: pd.DataFrame,
    modo_tempo: str = "mes",
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    bimestre: Optional[int] = None,
    semestre: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fundo: Optional[str] = None, # Corrigido de data_fim para data_fundo se necessário, ou mantido como data_fim
    data_fim: Optional[str] = None,
) -> pd.DataFrame:
    """Aplica filtros temporais padronizados em um DataFrame com coluna 'data_transacao'."""
    df = df.copy()
    if "data_transacao" not in df.columns:
        return df

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
    
    return df

def apply_attribute_filters(
    df: pd.DataFrame,
    grupo: Optional[str] = None,
    filial: Optional[str] = None,
    estado: Optional[str] = None,
    regiao: Optional[str] = None,
    combustivel: Optional[str] = None,
    contrato: Optional[str] = None,
) -> pd.DataFrame:
    """Aplica filtros de atributos (grupo, filial, estado, região, combustível, contrato)."""
    df = df.copy()
    
    if grupo and "grupo_veiculo" in df.columns:
        df = df[df["grupo_veiculo"] == grupo]
    if filial and "filial_nome" in df.columns:
        df = df[df["filial_nome"] == filial]
    if filial and "filial" in df.columns and "filial_nome" not in df.columns: # Fallback para FKM
        df = df[df["filial"] == filial]
    if estado and "filial_estado" in df.columns:
        df = df[df["filial_estado"] == estado]
    if regiao and "filial_regiao" in df.columns:
        df = df[df["filial_regiao"] == regiao]
    if combustivel and "grupo_combustivel" in df.columns:
        df = df[df["grupo_combustivel"] == combustivel]
    if contrato and "contrato" in df.columns:
        df = df[df["contrato"] == contrato]
        
    return df
