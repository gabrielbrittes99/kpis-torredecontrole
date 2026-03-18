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

# TTLs fixos
TTL_TRANSACOES = timedelta(minutes=int(os.getenv("CACHE_TTL_MINUTES", "10")))
TTL_ANP = timedelta(hours=24)
TTL_VEICULOS = timedelta(hours=4)

# SQL principal
_QUERY_TRANSACOES = """
    SELECT
        data_transacao,
        valor,
        litragem,
        nome_combustivel,
        tipo_abastecimento,
        placa,
        hodometro,
        modelo_veiculo,
        marca_veiculo,
        motorista,
        razao_social_posto,
        nome_fantasia_posto,
        cidade_posto,
        uf_posto,
        transacao_estornada,
        cnpj_cliente,
        transacao,
        id
    FROM integration_truckpag_transacoes
    WHERE litragem > 0
      AND transacao_estornada = '0'
    ORDER BY data_transacao
"""


class DataCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {
            "transacoes": {"df": None, "kml_df": None, "ts": None, "ttl": TTL_TRANSACOES},
            "anp": {"df": None, "ts": None, "ttl": TTL_ANP},
            "veiculos": {"df": None, "ts": None, "ttl": TTL_VEICULOS},
        }

    def _is_stale(self, key: str) -> bool:
        entry = self._cache.get(key)
        if not entry or entry["df"] is None or entry["ts"] is None:
            return True
        return datetime.now() - entry["ts"] > entry["ttl"]

    def _fetch_transacoes(self) -> pd.DataFrame:
        logger.info("Cache: Carregando transações do PostgreSQL...")
        with get_engine().connect() as conn:
            df = pd.read_sql_query(_QUERY_TRANSACOES, conn)

        # Garante tipos corretos
        df["data_transacao"] = pd.to_datetime(df["data_transacao"], utc=True).dt.tz_localize(None)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        df["litragem"] = pd.to_numeric(df["litragem"], errors="coerce").fillna(0)
        df["hodometro"] = pd.to_numeric(df["hodometro"], errors="coerce")

        # Normaliza texto
        text_cols = [
            "nome_combustivel", "tipo_abastecimento", "placa",
            "razao_social_posto", "nome_fantasia_posto", "cidade_posto", "uf_posto", "motorista"
        ]
        for col in text_cols:
            df[col] = df[col].fillna("").astype(str).str.strip()

        # ── Grupo de combustível (4 grupos: Diesel, Gasolina, Álcool, Arla) ──
        df["grupo_combustivel"] = (
            df["nome_combustivel"]
            .str.lower()
            .map(FUEL_GROUP_MAP)
            .fillna("Outros")
        )

        # ── Filial Gritsch via SQL Server (enriquecido pelo cache de veículos) ──
        placa_upper = df["placa"].str.upper().str.replace("-", "").str.strip()

        # Renomeia placas antigas → novas (ex: TBI2068 → UBO0E91)
        # Mantém o histórico mas usa a nova placa para lookup de filial/grupo
        if PLACAS_RENOMEADAS:
            df["placa"] = placa_upper.map(
                lambda p: PLACAS_RENOMEADAS.get(p, p)
            )
            placa_upper = df["placa"]

        # Filtra placas ignoradas
        ignore_mask = placa_upper.isin(IGNORAR_PLACAS)
        if ignore_mask.any():
            df = df[~ignore_mask]
            placa_upper = placa_upper[~ignore_mask]

        df["filial_nome"] = ""
        df["filial_estado"] = ""
        df["filial_regiao"] = ""
        df["flag_venda"] = False
        df["flag_combustivel_indevido"] = False

        palmas_mask = placa_upper.isin(PALMAS_PLACAS)
        df.loc[palmas_mask, "filial_nome"]   = PALMAS_FILIAL["nome"]
        df.loc[palmas_mask, "filial_estado"] = PALMAS_FILIAL["estado"]
        df.loc[palmas_mask, "filial_regiao"] = PALMAS_FILIAL["regiao"]

        cwb_mask = placa_upper.isin(CWB_BASE_PLACAS)
        df.loc[cwb_mask, "filial_nome"]   = CWB_BASE_FILIAL["nome"]
        df.loc[cwb_mask, "filial_estado"] = CWB_BASE_FILIAL["estado"]
        df.loc[cwb_mask, "filial_regiao"] = CWB_BASE_FILIAL["regiao"]

        logger.info(
            f"Cache: {len(df)} transações carregadas | "
            f"grupos: {df['grupo_combustivel'].value_counts().to_dict()} | "
            f"Palmas: {palmas_mask.sum()} registros | CWB Base: {cwb_mask.sum()} registros"
        )
        return df

    def _enrich_filiais(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cruza as transações com o cache de veículos do BlueFleet para preencher:
        - filial_nome, filial_estado, filial_regiao
        - ano_modelo, idade_anos (para análise de custo x idade do veículo)
        Placas Palmas já vêm preenchidas do _fetch_transacoes.
        """
        try:
            from db_sqlserver import get_veiculos_df
            veiculos_raw = get_veiculos_df()[
                ["Placa", "FilialOperacional", "AnoModelo"]
            ].copy()
            veiculos_raw["Placa"] = veiculos_raw["Placa"].str.upper().str.replace("-", "").str.strip()
            veiculos = veiculos_raw.drop_duplicates("Placa")

            # Constrói lookup: placa → {nome, estado, regiao, original_sigla}
            filial_lookup = {}
            for _, row in veiculos.iterrows():
                filial_op = row["FilialOperacional"]
                info = FILIAIS_MAP.get(filial_op)
                if info:
                    # Cópia para não mutar o dict original do FILIAIS_MAP
                    filial_lookup[row["Placa"]] = {**info, "original_sigla": filial_op}
                elif filial_op:
                    # Filial não mapeada — usa o nome bruto do SQL Server
                    filial_lookup[row["Placa"]] = {
                        "nome": filial_op, "estado": "?", "regiao": "?",
                        "original_sigla": filial_op,
                    }

            # Overrides de Filial Manual
            from config import FILIAL_PLATE_OVERRIDES
            for p, sigla in FILIAL_PLATE_OVERRIDES.items():
                info = FILIAIS_MAP.get(sigla)
                if info:
                    filial_lookup[p.upper().replace("-","").strip()] = {**info, "original_sigla": sigla}

            # Aplica onde ainda não foi preenchido (Palmas já têm)
            mask_vazio = (df["filial_nome"] == "") | df["filial_nome"].isna()
            placa_upper = df["placa"].str.upper().str.replace("-", "").str.strip()

            df.loc[mask_vazio, "filial_nome"] = placa_upper[mask_vazio].map(
                lambda p: filial_lookup.get(p, {}).get("nome", "")
            )
            df.loc[mask_vazio, "filial_estado"] = placa_upper[mask_vazio].map(
                lambda p: filial_lookup.get(p, {}).get("estado", "")
            )
            df.loc[mask_vazio, "filial_regiao"] = placa_upper[mask_vazio].map(
                lambda p: filial_lookup.get(p, {}).get("regiao", "")
            )

            # Flag de Venda
            def check_venda(p):
                sigla = filial_lookup.get(p, {}).get("original_sigla", "").upper()
                return "VENDA" in sigla or "VENDIDO" in sigla

            df["flag_venda"] = placa_upper.map(check_venda)

            # ── Enriquece ano do modelo e idade do veículo ──────────────────
            ano_map = veiculos.set_index("Placa")["AnoModelo"].to_dict()
            ano_atual = datetime.now().year
            df["ano_modelo"] = placa_upper.map(ano_map).astype("Int64")
            df["idade_anos"] = df["ano_modelo"].apply(
                lambda a: (ano_atual - int(a)) if pd.notna(a) else None
            )

            preenchidos = (df["filial_nome"] != "").sum()
            logger.info(f"Cache: {preenchidos}/{len(df)} transações com filial | "
                        f"ano_modelo preenchido: {df['ano_modelo'].notna().sum()}")
        except Exception as e:
            logger.warning(f"Cache: não foi possível enriquecer filiais/veículos: {e}")
            # Garante que as colunas existam mesmo sem SQL Server
            if "ano_modelo" not in df.columns:
                df["ano_modelo"] = None
                df["idade_anos"] = None
        return df

    def _add_grupo(self, df: pd.DataFrame) -> pd.DataFrame:
        df["grupo_veiculo"] = [
            get_veiculo_group(str(m or ""), str(b or ""), str(p or ""))
            for m, b, p in zip(df["modelo_veiculo"], df["marca_veiculo"], df["placa"])
        ]
        
        # --- NOVO: Flag de Abastecimento Indevido ---
        from config import is_fuel_incompatible
        df["flag_combustivel_indevido"] = [
            is_fuel_incompatible(gv, gc)
            for gv, gc in zip(df["grupo_veiculo"], df["grupo_combustivel"])
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
                if key == "transacoes":
                    df = self._fetch_transacoes()
                    df = self._enrich_filiais(df)
                    df = self._add_grupo(df)
                    kml_df = self._calc_kml(df)
                    self._cache[key]["df"] = df
                    self._cache[key]["kml_df"] = kml_df
                elif key == "anp":
                    # Integrado via anp_client, mas mantido aqui para centralizar
                    from anp_client import get_anp_df
                    df = get_anp_df()
                    self._cache[key]["df"] = df
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
        """Força a limpeza do timestamp para obrigar atualização na próxima chamada."""
        if key in self._cache:
            self._cache[key]["ts"] = None
            self.get_df(key)

    @property
    def last_updated(self) -> Optional[datetime]:
        return self._cache["transacoes"]["ts"]


cache = DataCache()
