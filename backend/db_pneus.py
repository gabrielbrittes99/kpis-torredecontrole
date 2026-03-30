"""
Leitura da planilha Controle de Pneus (Controle de Pneus.xlsx).
Fonte de dados: aba 'Planilha1'.

Colunas:
  N.FOGO, DOT, ANO, DATA ENVIO, DATA ALOCADO, MÊS, EMPRESA, ESTADO,
  FILIAL, QUAN, 22.5, EIXO, MEDIDA, MARCA, MODELO, ESTADO PNEU,
  VEÍCULO, PLACA, KM SOLICITADO, KM ALOCADO, KM FINAL, Km Rodado,
  STATUS, FORNECEDOR, NF, VALOR/UN, TOTAL, CPK
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_pneus_cache: Optional[pd.DataFrame] = None
_pneus_cache_ts: Optional[datetime] = None
_PNEUS_TTL = timedelta(hours=24)

_COLUNAS = [
    "n_fogo", "dot", "ano", "data_envio", "data_alocado", "mes",
    "empresa", "estado", "filial", "quan", "p22_5", "eixo",
    "medida", "marca", "modelo", "estado_pneu", "veiculo", "placa",
    "km_solicitado", "km_alocado", "km_final", "km_rodado",
    "status", "fornecedor", "nf", "valor_un", "total", "cpk",
]

_NUMERICAS = [
    "quan", "p22_5", "km_solicitado", "km_alocado", "km_final",
    "km_rodado", "valor_un", "total", "cpk", "ano",
]


_ONLINE_URL = "https://1drv.ms/x/c/04e048f7cdc9d79d/IQCd18nN90jgIIAEgQoAAAAAAZN_DUfB6Nt26HgqvHRe8Cg?download=1"

def _fetch_online() -> Optional[bytes]:
    import httpx
    try:
        r = httpx.get(_ONLINE_URL, follow_redirects=True, timeout=60)
        r.raise_for_status()
        logger.info(f"Pneus: Download online concluído ({len(r.content)} bytes)")
        return r.content
    except Exception as e:
        logger.error(f"Pneus: Falha ao baixar url online: {e}")
        return None

def _get_pneus_path() -> str:
    path = os.getenv("PNEUS_FILE_PATH")
    if not path:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(
            base, "..", "documentacao API - Truckpag", "Controle de Pneus.xlsx"
        )
    return os.path.normpath(path)


def get_pneus_df() -> pd.DataFrame:
    """
    Retorna DataFrame da aba 'enviados' da planilha Controle de Pneus.
    Cache de 24h.
    """
    global _pneus_cache, _pneus_cache_ts
    agora = datetime.now()

    if (
        _pneus_cache is not None
        and _pneus_cache_ts is not None
        and (agora - _pneus_cache_ts) < _PNEUS_TTL
    ):
        return _pneus_cache

    try:
        path = _get_pneus_path()
        content = _fetch_online()
        if content:
            from io import BytesIO
            logger.info("Pneus: lendo do conteúdo online")
            df = pd.read_excel(BytesIO(content), sheet_name="Enviados", header=1, engine="openpyxl")
            try:
                with open(path, "wb") as f:
                    f.write(content)
            except Exception:
                pass
        else:
            logger.info(f"Pneus: fallback carregando arquivo {path}")
            try:
                df = pd.read_excel(path, sheet_name="Enviados", header=1, engine="openpyxl")
            except Exception:
                df = pd.read_excel(path, sheet_name="Planilha1", engine="openpyxl")

        # Renomeia colunas para snake_case
        rename_map = {
            "N.FOGO": "n_fogo",
            "DOT": "dot",
            "ANO": "ano",
            "DATA ENVIO": "data_envio",
            "DATA ALOCADO": "data_alocado",
            "MÊS": "mes",
            "EMPRESA": "empresa",
            "ESTADO": "estado",
            "FILIAL": "filial",
            "QUAN": "quan",
            "22.5": "p22_5",
            "EIXO": "eixo",
            "MEDIDA": "medida",
            "MARCA": "marca",
            "MODELO": "modelo",
            "ESTADO PNEU": "estado_pneu",
            "VEÍCULO": "veiculo",
            "PLACA": "placa",
            "KM SOLICITADO": "km_solicitado",
            "KM ALOCADO": "km_alocado",
            "KM FINAL": "km_final",
            "Km Rodado": "km_rodado",
            "STATUS": "status",
            "FORNECEDOR": "fornecedor",
            "NF": "nf",
            "VALOR/UN": "valor_un",
            "TOTAL": "total",
            "CPK": "cpk",
        }
        df = df.rename(columns=rename_map)

        # Normaliza placa
        if "placa" in df.columns:
            df["placa"] = (
                df["placa"]
                .astype(str)
                .str.upper()
                .str.replace("-", "", regex=False)
                .str.strip()
            )

        # Converte numéricas
        for col in _NUMERICAS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # Converte datas
        for col in ["data_envio", "data_alocado"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Normaliza strings
        for col in ["filial", "empresa", "estado", "marca", "modelo",
                     "estado_pneu", "veiculo", "status", "fornecedor",
                     "medida", "eixo", "mes"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace("None", "").replace("nan", "")

        _pneus_cache = df
        _pneus_cache_ts = agora
        logger.info(f"Pneus: {len(df)} linhas carregadas")
        return df

    except Exception as e:
        logger.error(f"Pneus: falha ao carregar arquivo: {e}")
        if _pneus_cache is not None:
            logger.warning("Pneus: retornando cache anterior")
            return _pneus_cache
        return pd.DataFrame(columns=_COLUNAS)


def refresh_pneus_cache() -> dict:
    """Força recarregamento do arquivo."""
    global _pneus_cache_ts
    _pneus_cache_ts = None
    df = get_pneus_df()
    return {
        "linhas": len(df),
        "placas": int(df["placa"].nunique()) if "placa" in df.columns else 0,
        "filiais": sorted(df["filial"].dropna().unique().tolist()) if "filial" in df.columns else [],
    }
