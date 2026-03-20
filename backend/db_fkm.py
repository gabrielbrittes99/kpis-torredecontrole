"""
Leitura da planilha FKM (Evolução FKM 2026.xlsb).
Fonte de dados: aba 'BANCO DE DADOS' — uma linha por veículo por mês.

Colunas principais usadas:
  Placa, Filial, Modelo Simplificado, Grupo Veículo, TP.Comb, TP.Rota
  Km Inicial, Km Final, Total de Km
  Litros Comb., Valor Comb., Média Km/l, Comb / Km
  Arla, Lataria e Pintura, Manutenção, Rodas / Pneus
  Man / Km, Total, Total Geral Manutenção
  Motorista Principal, Contrato, Dias Úteis, Mês
  Rastreador, Regiao

O arquivo é atualizado mensalmente pelo usuário, sempre no mesmo caminho.
Cache de 24h (refresh automático no próximo acesso após vencimento).
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from pyxlsb import open_workbook

load_dotenv()

logger = logging.getLogger(__name__)

_fkm_cache: Optional[pd.DataFrame] = None
_fkm_cache_ts: Optional[datetime] = None
_FKM_TTL = timedelta(hours=24)

# Mapeamento exato das colunas da aba BANCO DE DADOS
_COLUNAS = [
    "modelo", "grupo_veiculo", "placa", "marca", "tp_combustivel", "tp_rota",
    "contrato", "roteiro_principal", "motorista_principal",
    "km_inicial", "km_final", "total_km",
    "litros_comb", "valor_comb", "media_kml", "comb_por_km",
    "arla", "lataria_pintura", "manutencao", "rodas_pneus",
    "man_por_km", "total", "rastreador", "filial", "mes",
    "total_geral_manutencao", "grupo_fkm", "grupo_correto",
    "status_grupo", "modelo_fkm", "modelo_correto",
    "modelo_padrao", "modelo_simplificado",
    "dias_uteis", "duc", "duk", "dul",
    "id_filial", "regiao", "id_tipo_combustivel",
]

# Colunas numéricas para conversão
_NUMERICAS = [
    "km_inicial", "km_final", "total_km",
    "litros_comb", "valor_comb", "media_kml", "comb_por_km",
    "arla", "lataria_pintura", "manutencao", "rodas_pneus",
    "man_por_km", "total", "total_geral_manutencao",
    "dias_uteis", "duc", "duk", "dul",
]


def _excel_date_to_str(val) -> Optional[str]:
    """Converte número serial do Excel (ex: 45658.0) para 'YYYY-MM'."""
    if val is None:
        return None
    try:
        n = int(float(val))
        # Excel epoch: 1899-12-30
        dt = datetime(1899, 12, 30) + timedelta(days=n)
        return dt.strftime("%Y-%m")
    except Exception:
        return str(val) if val else None


def _get_fkm_path() -> str:
    path = os.getenv("FKM_FILE_PATH")
    if not path:
        # fallback: caminho relativo ao db_fkm.py
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(
            base, "..", "documentacao API - Truckpag", "Evolucao FKM 2026.xlsb"
        )
    return os.path.normpath(path)


def get_fkm_df() -> pd.DataFrame:
    """
    Retorna DataFrame da aba 'BANCO DE DADOS' do FKM.
    Cache de 24h. Em caso de falha retorna cache anterior (se existir).
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
        path = _get_fkm_path()
        logger.info(f"FKM: carregando arquivo {path}")

        rows = []
        with open_workbook(path) as wb:
            with wb.get_sheet("BANCO DE DADOS") as sheet:
                header_skipped = False
                for row in sheet.rows():
                    vals = [item.v for item in row]
                    # Pula linha de cabeçalho (primeira linha com dados)
                    if not header_skipped:
                        header_skipped = True
                        continue
                    # Pula linhas completamente vazias
                    if not any(v is not None for v in vals):
                        continue
                    rows.append(vals)

        if not rows:
            raise ValueError("Nenhuma linha encontrada na aba BANCO DE DADOS")

        # Monta DataFrame com as colunas mapeadas
        # Cada linha tem 40 colunas; trunca ou completa para o mapeamento
        n_cols = len(_COLUNAS)
        padded = [r[:n_cols] + [None] * max(0, n_cols - len(r)) for r in rows]
        df = pd.DataFrame(padded, columns=_COLUNAS)

        # Normaliza placa
        df["placa"] = df["placa"].astype(str).str.upper().str.replace("-", "", regex=False).str.strip()
        df = df[df["placa"].str.len() >= 7]  # descarta linhas sem placa válida

        # Converte numéricos
        for col in _NUMERICAS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # Converte mês (serial Excel → "YYYY-MM")
        df["ano_mes"] = df["mes"].apply(_excel_date_to_str)

        # Normaliza strings
        for col in ["filial", "grupo_veiculo", "tp_combustivel", "modelo_simplificado",
                    "motorista_principal", "regiao", "tp_rota"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace("None", "")

        # Normaliza capitalização do grupo (Leve / LEVE / leve → Leve)
        _GRUPO_NORM = {
            "leve": "Leve", "médio": "Médio", "medio": "Médio",
            "pesado": "Pesado", "kombi": "Kombi", "moto": "Moto",
        }
        df["grupo_veiculo"] = df["grupo_veiculo"].apply(
            lambda g: _GRUPO_NORM.get(g.lower(), g) if isinstance(g, str) else g
        )

        # Remove duplicatas exatas (mesma placa+mês pode aparecer 2x no xlsb por causa de pivôs)
        df = df.drop_duplicates(subset=["placa", "ano_mes", "filial", "contrato"])

        _fkm_cache = df
        _fkm_cache_ts = agora
        logger.info(f"FKM: {len(df)} linhas carregadas ({df['ano_mes'].nunique()} meses, {df['placa'].nunique()} placas)")
        return df

    except Exception as e:
        logger.error(f"FKM: falha ao carregar arquivo: {e}")
        if _fkm_cache is not None:
            logger.warning("FKM: retornando cache anterior")
            return _fkm_cache
        return pd.DataFrame(columns=_COLUNAS + ["ano_mes"])


def refresh_fkm_cache() -> dict:
    """Força recarregamento do arquivo. Chamado via endpoint de admin."""
    global _fkm_cache_ts
    _fkm_cache_ts = None
    df = get_fkm_df()
    return {
        "linhas": len(df),
        "meses": sorted(df["ano_mes"].dropna().unique().tolist()),
        "placas": int(df["placa"].nunique()),
        "filiais": sorted(df["filial"].dropna().unique().tolist()),
    }
