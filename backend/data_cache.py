import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pandas as pd
from db import get_engine
from dotenv import load_dotenv
from config import (
    FUEL_GROUP_MAP, PALMAS_PLACAS, PALMAS_FILIAL, FILIAIS_MAP, get_veiculo_group,
    CWB_BASE_PLACAS, CWB_BASE_FILIAL, IGNORAR_PLACAS, PLACAS_RENOMEADAS
)

load_dotenv()

logger = logging.getLogger(__name__)

from utils import norm_placa

# TTLs fixos
TTL_TRANSACOES = timedelta(minutes=int(os.getenv("CACHE_TTL_MINUTES", "10")))
TTL_ANP = timedelta(hours=24)
TTL_VEICULOS = timedelta(hours=4)

# SQLs de extração
_QUERY_COMBUSTIVEL = """
    SELECT
        data_transacao, valor, litragem, nome_combustivel, tipo_abastecimento,
        placa, hodometro, modelo_veiculo, marca_veiculo, motorista,
        razao_social_posto, nome_fantasia_posto, cidade_posto, uf_posto,
        transacao_estornada, cnpj_cliente, transacao, id
    FROM integration_truckpag_transacoes
    WHERE litragem > 0
      AND transacao_estornada = '0'
    ORDER BY data_transacao
"""

_QUERY_PEDAGIOS = """
    SELECT
        data_transacao, valor, litragem, nome_combustivel, tipo_abastecimento,
        placa, hodometro, modelo_veiculo, marca_veiculo, motorista,
        razao_social_posto, nome_fantasia_posto, cidade_posto, uf_posto,
        transacao_estornada, cnpj_cliente, transacao, id
    FROM integration_truckpag_transacoes
    WHERE (litragem = 0 OR litragem IS NULL)
      AND transacao_estornada = '0'
    ORDER BY data_transacao
"""

_QUERY_ESTORNOS = """
    SELECT
        data_transacao, valor, litragem, nome_combustivel, tipo_abastecimento,
        placa, hodometro, modelo_veiculo, marca_veiculo, motorista,
        razao_social_posto, nome_fantasia_posto, cidade_posto, uf_posto,
        transacao_estornada, cnpj_cliente, transacao, id
    FROM integration_truckpag_transacoes
    WHERE transacao_estornada != '0'
    ORDER BY data_transacao
"""


class DataCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {
            "transacoes": {"df": None, "kml_df": None, "ts": None, "ttl": TTL_TRANSACOES, "query": _QUERY_COMBUSTIVEL},
            "pedagios":   {"df": None, "ts": None, "ttl": TTL_TRANSACOES, "query": _QUERY_PEDAGIOS},
            "estornos":   {"df": None, "ts": None, "ttl": TTL_TRANSACOES, "query": _QUERY_ESTORNOS},
            "anp":        {"df": None, "ts": None, "ttl": TTL_ANP},
            "veiculos":   {"df": None, "ts": None, "ttl": TTL_VEICULOS},
        }

    def _is_stale(self, key: str) -> bool:
        entry = self._cache.get(key)
        if not entry or entry["df"] is None or entry["ts"] is None:
            return True
        return datetime.now() - entry["ts"] > entry["ttl"]

    def _fetch_generic(self, key: str) -> pd.DataFrame:
        """Busca genérica para tabelas do TruckPag no PostgreSQL."""
        logger.info(f"Cache: Carregando {key} do PostgreSQL...")
        query = self._cache[key]["query"]
        from sqlalchemy import text
        with get_engine().connect() as conn:
            result = conn.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

        # Garante tipos corretos
        df["data_transacao"] = pd.to_datetime(df["data_transacao"], utc=True).dt.tz_localize(None)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        if "litragem" in df.columns:
            df["litragem"] = pd.to_numeric(df["litragem"], errors="coerce").fillna(0)
        if "hodometro" in df.columns:
            df["hodometro"] = pd.to_numeric(df["hodometro"], errors="coerce")

        # Normaliza texto (apenas colunas que existem na query)
        text_cols = [
            "nome_combustivel", "tipo_abastecimento", "placa",
            "razao_social_posto", "nome_fantasia_posto", "cidade_posto", "uf_posto", "motorista"
        ]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # ── Grupo de combustível (4 grupos: Diesel, Gasolina, Álcool, Arla) ──
        if "nome_combustivel" in df.columns:
            df["grupo_combustivel"] = (
                df["nome_combustivel"]
                .str.lower()
                .map(FUEL_GROUP_MAP)
                .fillna("Outros")
            )

        # ── Normalização de Placa e Filtros Iniciais ──
        df["placa"] = df["placa"].apply(norm_placa)
        
        # Renomeia placas antigas → novas
        if PLACAS_RENOMEADAS:
            df["placa"] = df["placa"].map(lambda p: PLACAS_RENOMEADAS.get(p, p))

        # Filtra placas ignoradas
        if IGNORAR_PLACAS:
            df = df[~df["placa"].isin(IGNORAR_PLACAS)]

        # Inicializa colunas de filial para evitar erros antes do enriquecimento
        df["filial_nome"] = ""
        df["filial_estado"] = ""
        df["filial_regiao"] = ""
        df["flag_venda"] = False
        df["flag_combustivel_indevido"] = False

        # Palmas e CWB Base (Hardcoded em config.py)
        palmas_mask = df["placa"].isin(PALMAS_PLACAS)
        df.loc[palmas_mask, "filial_nome"]   = PALMAS_FILIAL["nome"]
        df.loc[palmas_mask, "filial_estado"] = PALMAS_FILIAL["estado"]
        df.loc[palmas_mask, "filial_regiao"] = PALMAS_FILIAL["regiao"]

        cwb_mask = df["placa"].isin(CWB_BASE_PLACAS)
        df.loc[cwb_mask, "filial_nome"]   = CWB_BASE_FILIAL["nome"]
        df.loc[cwb_mask, "filial_estado"] = CWB_BASE_FILIAL["estado"]
        df.loc[cwb_mask, "filial_regiao"] = CWB_BASE_FILIAL["regiao"]

        logger.info(
            f"Cache: {len(df)} transações carregadas | "
            f"grupos: {df['grupo_combustivel'].value_counts().to_dict()} | "
            f"Palmas: {palmas_mask.sum()} registros"
        )
        return df

    def _enrich_filiais(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cruza as transações com o cache de veículos do BlueFleet para preencher filial e idade.
        """
        try:
            from db_sqlserver import get_veiculos_df
            veiculos_raw = get_veiculos_df()[
                ["Placa", "FilialOperacional", "AnoModelo"]
            ].copy()
            veiculos_raw["Placa"] = veiculos_raw["Placa"].apply(norm_placa)
            veiculos = veiculos_raw.drop_duplicates("Placa")

            # Lookup: placa → {nome, estado, regiao, original_sigla}
            filial_lookup = {}
            for _, row in veiculos.iterrows():
                filial_op = row["FilialOperacional"]
                info = FILIAIS_MAP.get(filial_op)
                if info:
                    filial_lookup[row["Placa"]] = {**info, "original_sigla": filial_op}
                elif filial_op:
                    filial_lookup[row["Placa"]] = {
                        "nome": filial_op, "estado": "?", "regiao": "?",
                        "original_sigla": filial_op,
                    }

            # Overrides Manuais
            from config import FILIAL_PLATE_OVERRIDES
            for p, sigla in FILIAL_PLATE_OVERRIDES.items():
                info = FILIAIS_MAP.get(sigla)
                if info:
                    filial_lookup[norm_placa(p)] = {**info, "original_sigla": sigla}

            # Aplica onde ainda não foi preenchido
            mask_vazio = (df["filial_nome"] == "") | df["filial_nome"].isna()
            df.loc[mask_vazio, "filial_nome"] = df.loc[mask_vazio, "placa"].map(
                lambda p: filial_lookup.get(p, {}).get("nome", "")
            )
            df.loc[mask_vazio, "filial_estado"] = df.loc[mask_vazio, "placa"].map(
                lambda p: filial_lookup.get(p, {}).get("estado", "")
            )
            df.loc[mask_vazio, "filial_regiao"] = df.loc[mask_vazio, "placa"].map(
                lambda p: filial_lookup.get(p, {}).get("regiao", "")
            )

            # Flag de Venda
            df["flag_venda"] = df["placa"].map(
                lambda p: "VENDA" in filial_lookup.get(p, {}).get("original_sigla", "").upper()
            )

            # Idade do veículo
            ano_map = veiculos.set_index("Placa")["AnoModelo"].to_dict()
            ano_atual = datetime.now().year
            df["ano_modelo"] = df["placa"].map(ano_map).astype("Int64")
            df["idade_anos"] = df["ano_modelo"].apply(
                lambda a: (ano_atual - int(a)) if pd.notna(a) else None
            )

        except Exception as e:
            logger.warning(f"Cache: não foi possível enriquecer filiais: {e}")
            if "ano_modelo" not in df.columns:
                df["ano_modelo"] = None
                df["idade_anos"] = None
        return df

    def _add_grupo(self, df: pd.DataFrame) -> pd.DataFrame:
        modelos = df["modelo_veiculo"].tolist() if "modelo_veiculo" in df.columns else [""] * len(df)
        marcas  = df["marca_veiculo"].tolist()  if "marca_veiculo"  in df.columns else [""] * len(df)
        df["grupo_veiculo"] = [
            get_veiculo_group(str(m or ""), str(b or ""), str(p or ""))
            for m, b, p in zip(modelos, marcas, df["placa"])
        ]
        from config import is_fuel_incompatible
        grupos_comb = df["grupo_combustivel"].tolist() if "grupo_combustivel" in df.columns else [""] * len(df)
        df["flag_combustivel_indevido"] = [
            is_fuel_incompatible(gv, gc)
            for gv, gc in zip(df["grupo_veiculo"], grupos_comb)
        ]
        return df

    def _calc_kml(self, df: pd.DataFrame) -> pd.DataFrame:
        hodo = df[df["hodometro"].notna() & (df["hodometro"] > 0)].copy()
        if hodo.empty:
            return hodo
        hodo = hodo.sort_values(["placa", "data_transacao"])
        hodo["km_percorrido"] = hodo.groupby("placa")["hodometro"].diff()
        hodo = hodo[(hodo["km_percorrido"] > 0) & (hodo["km_percorrido"] <= 2000)]
        return hodo

    def get_df(self, key: str = "transacoes") -> pd.DataFrame:
        """Retorna o DataFrame do cache, atualizando-o se necessário."""
        if self._is_stale(key):
            try:
                if key in ["transacoes", "pedagios", "estornos"]:
                    df = self._fetch_generic(key)
                    df = self._enrich_filiais(df)
                    df = self._add_grupo(df)
                    
                    if key == "transacoes":
                        self._cache[key]["kml_df"] = self._calc_kml(df)
                        
                    self._cache[key]["df"] = df
                elif key == "anp":
                    from anp_client import get_anp_df
                    self._cache[key]["df"] = get_anp_df()
                else:
                    return pd.DataFrame()

                self._cache[key]["ts"] = datetime.now()
            except Exception as e:
                logger.error(f"Falha ao atualizar cache '{key}': {e}")
                if self._cache[key]["df"] is None:
                    raise
        return self._cache[key]["df"]

    def get_kml_df(self) -> pd.DataFrame:
        self.get_df("transacoes")
        return self._cache["transacoes"]["kml_df"]

    def force_refresh(self, key: str = "transacoes") -> None:
        if key in self._cache:
            self._cache[key]["ts"] = None
            self.get_df(key)

    @property
    def last_updated(self) -> Optional[datetime]:
        return self._cache["transacoes"]["ts"]


cache = DataCache()
