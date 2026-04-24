import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pandas as pd
from dotenv import load_dotenv
from config import (
    FUEL_GROUP_MAP, PALMAS_PLACAS, PALMAS_FILIAL, FILIAIS_MAP, get_veiculo_group,
    CWB_BASE_PLACAS, CWB_BASE_FILIAL, IGNORAR_PLACAS, PLACAS_RENOMEADAS, FILIAIS_EXCLUIR
)

load_dotenv()

logger = logging.getLogger(__name__)

from utils import norm_placa

# TTLs fixos
TTL_TRANSACOES = timedelta(minutes=int(os.getenv("CACHE_TTL_MINUTES", "30")))
TTL_ANP = timedelta(hours=24)
TTL_VEICULOS = timedelta(hours=4)

# ═══════════════════════════════════════════════════════════════════════════════
# Query principal — Data Warehouse (silver.truckpag_analitico_transacao)
# ═══════════════════════════════════════════════════════════════════════════════
_QUERY_DW_TRANSACOES = """
    SELECT *
    FROM silver.truckpag_analitico_transacao
    ORDER BY transacao_id ASC
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Fallback queries — PostgreSQL Railway (legado)
# ═══════════════════════════════════════════════════════════════════════════════
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


def _has_dw_config() -> bool:
    """Verifica se as credenciais do DW estão configuradas."""
    return bool(
        os.getenv("DW_HOST")
        and os.getenv("DW_USER")
        and os.getenv("DW_PASSWORD")
        and os.getenv("DW_PASSWORD") != "COLOQUE_SUA_SENHA_AQUI"
    )


class DataCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {
            "transacoes": {"df": None, "kml_df": None, "ts": None, "ttl": TTL_TRANSACOES, "query": _QUERY_COMBUSTIVEL},
            "pedagios":   {"df": None, "ts": None, "ttl": TTL_TRANSACOES, "query": _QUERY_PEDAGIOS},
            "estornos":   {"df": None, "ts": None, "ttl": TTL_TRANSACOES, "query": _QUERY_ESTORNOS},
            "anp":        {"df": None, "ts": None, "ttl": TTL_ANP},
            "veiculos":   {"df": None, "ts": None, "ttl": TTL_VEICULOS},
        }
        self._fuel_map: Optional[dict] = None        # Lookup combustivel_nome → grupo
        # DW é usado APENAS para tabelas torre.* (enriquecimento de filiais e combustíveis).
        # Transações/pedágios/estornos sempre vêm do PostgreSQL Railway
        # (integration_truckpag_transacoes — apenas aprovadas).
        # silver.truckpag_analitico_transacao inclui recusadas — reservado para painel RT futuro.
        self._use_dw = _has_dw_config()
        if self._use_dw:
            logger.info("✓ DW configurado — usado para enriquecimento (torre.*). Transações: PostgreSQL Railway")
        else:
            logger.info("⚠ DW não configurado — usando PostgreSQL Railway")

    def _is_stale(self, key: str) -> bool:
        entry = self._cache.get(key)
        if not entry or entry["df"] is None or entry["ts"] is None:
            return True
        return datetime.now() - entry["ts"] > entry["ttl"]

    def _is_dw_stale(self) -> bool:
        if self._dw_raw is None or self._dw_ts is None:
            return True
        return datetime.now() - self._dw_ts > TTL_TRANSACOES

    # ═══════════════════════════════════════════════════════════════════════════
    # Mapa de classificação de combustível (torre.combustivel_classificacao)
    # ═══════════════════════════════════════════════════════════════════════════
    def _get_fuel_map(self) -> dict:
        """
        Retorna dict {combustivel_nome_lower → grupo_combustivel} carregado de
        torre.combustivel_classificacao. Usa FUEL_GROUP_MAP como fallback se a
        tabela não existir ou o DW não estiver configurado.
        """
        if self._fuel_map is not None:
            return self._fuel_map

        if self._use_dw:
            try:
                from db_dw import get_dw_engine
                from sqlalchemy import text
                with get_dw_engine().connect() as conn:
                    result = conn.execute(text(
                        "SELECT combustivel_nome, grupo_combustivel FROM torre.combustivel_classificacao"
                    ))
                    self._fuel_map = {row[0].lower(): row[1] for row in result.fetchall()}
                logger.info(f"Cache: mapa de combustíveis carregado ({len(self._fuel_map)} entradas)")
                return self._fuel_map
            except Exception as e:
                logger.warning(f"Cache: falha ao carregar torre.combustivel_classificacao: {e} — usando FUEL_GROUP_MAP")

        self._fuel_map = FUEL_GROUP_MAP
        return self._fuel_map

    def invalidate_fuel_map(self):
        """Invalida o cache do mapa de combustíveis (chamar após ETL)."""
        self._fuel_map = None

    # ═══════════════════════════════════════════════════════════════════════════
    # FETCH do Data Warehouse (fonte primária)
    # ═══════════════════════════════════════════════════════════════════════════
    def _fetch_dw(self) -> pd.DataFrame:
        """Busca TODOS os dados do DW (silver.truckpag_analitico_transacao)."""
        logger.info("Cache DW: Carregando dados de silver.truckpag_analitico_transacao...")
        from db_dw import get_dw_engine
        from sqlalchemy import text

        with get_dw_engine().connect() as conn:
            result = conn.execute(text(_QUERY_DW_TRANSACOES))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

        logger.info(f"Cache DW: {len(df)} registros carregados. Colunas: {list(df.columns)}")
        return df

    def _normalize_dw_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza o DataFrame do DW para o formato esperado pelo sistema.
        Mapeia colunas do DW (silver) → colunas usadas nos routers.
        """
        # Mapeamento de colunas — se a coluna DW tiver nomes diferentes, mapeamos
        # As colunas podem variar, então tratamos de forma defensiva
        col_map = {}

        # Tentativa de descobrir e mapear colunas automaticamente
        existing = set(df.columns)

        # data_transacao
        for candidate in ["data_transacao", "transacao_data", "dt_transacao", "data"]:
            if candidate in existing:
                col_map[candidate] = "data_transacao"
                break

        # valor
        for candidate in ["valor", "transacao_valor", "valor_total", "vl_total"]:
            if candidate in existing:
                col_map[candidate] = "valor"
                break

        # litragem (já correto no DW)
        for candidate in ["litragem", "litros", "volume", "qtd_litros"]:
            if candidate in existing:
                col_map[candidate] = "litragem"
                break

        # nome_combustivel
        for candidate in ["nome_combustivel", "combustivel_nome", "combustivel", "ds_combustivel", "tipo_combustivel"]:
            if candidate in existing:
                col_map[candidate] = "nome_combustivel"
                break

        # placa
        for candidate in ["placa", "veiculo_placa", "ds_placa", "placa_veiculo"]:
            if candidate in existing:
                col_map[candidate] = "placa"
                break

        # hodometro
        for candidate in ["hodometro", "hodometro_anterior", "hodometro_atual", "km", "odometro"]:
            if candidate in existing:
                col_map[candidate] = "hodometro"
                break

        # modelo_veiculo
        for candidate in ["modelo_veiculo", "modelo", "ds_modelo"]:
            if candidate in existing:
                col_map[candidate] = "modelo_veiculo"
                break

        # marca_veiculo
        for candidate in ["marca_veiculo", "marca", "ds_marca"]:
            if candidate in existing:
                col_map[candidate] = "marca_veiculo"
                break

        # motorista
        for candidate in ["motorista", "motorista_nome", "nome_motorista", "ds_motorista"]:
            if candidate in existing:
                col_map[candidate] = "motorista"
                break

        # razao_social_posto
        for candidate in ["razao_social_posto", "razao_social", "estabelecimento_nome", "posto"]:
            if candidate in existing:
                col_map[candidate] = "razao_social_posto"
                break

        # nome_fantasia_posto
        for candidate in ["nome_fantasia_posto", "nome_fantasia", "fantasia_posto"]:
            if candidate in existing:
                col_map[candidate] = "nome_fantasia_posto"
                break

        # cidade / uf
        for candidate in ["cidade_posto", "cidade", "ds_cidade"]:
            if candidate in existing:
                col_map[candidate] = "cidade_posto"
                break
        for candidate in ["uf_posto", "uf", "ds_uf", "estado"]:
            if candidate in existing:
                col_map[candidate] = "uf_posto"
                break

        # transacao_estornada
        for candidate in ["transacao_estornada", "estornada", "fl_estornada"]:
            if candidate in existing:
                col_map[candidate] = "transacao_estornada"
                break

        # tipo_abastecimento
        for candidate in ["tipo_abastecimento", "transacao_tipo", "tipo", "ds_tipo"]:
            if candidate in existing:
                col_map[candidate] = "tipo_abastecimento"
                break

        # transacao / id
        for candidate in ["transacao", "nr_transacao", "transacao_id"]:
            if candidate in existing:
                col_map[candidate] = "transacao"
                break
        for candidate in ["id", "transacao_id", "pk_id"]:
            if candidate in existing and "id" not in col_map.values():
                col_map[candidate] = "id"
                break

        # cnpj_cliente
        for candidate in ["cnpj_cliente", "cliente_cnpj", "cnpj", "ds_cnpj"]:
            if candidate in existing:
                col_map[candidate] = "cnpj_cliente"
                break

        # Aplica rename (somente colunas que existem e cujo nome difere)
        rename_map = {k: v for k, v in col_map.items() if k != v and k in existing}
        if rename_map:
            df = df.rename(columns=rename_map)
            logger.info(f"Cache DW: Renomeadas colunas: {rename_map}")

        # Se DW não tem nome_fantasia_posto separado, usa razao_social_posto
        if "nome_fantasia_posto" not in df.columns and "razao_social_posto" in df.columns:
            df["nome_fantasia_posto"] = df["razao_social_posto"]

        return df

    def _split_dw_data(self, df: pd.DataFrame):
        """
        Divide o DataFrame do DW em transacoes, pedagios e estornos.
        Aplica normalização e enriquecimento em cada split.
        """
        df = self._normalize_dw_df(df)

        # Garante tipos corretos
        if "data_transacao" in df.columns:
            df["data_transacao"] = pd.to_datetime(df["data_transacao"], utc=True, errors="coerce").dt.tz_localize(None)
        if "valor" in df.columns:
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        if "litragem" in df.columns:
            df["litragem"] = pd.to_numeric(df["litragem"], errors="coerce").fillna(0)
        if "hodometro" in df.columns:
            df["hodometro"] = pd.to_numeric(df["hodometro"], errors="coerce")

        # Normaliza texto
        text_cols = [
            "nome_combustivel", "tipo_abastecimento", "placa",
            "razao_social_posto", "nome_fantasia_posto", "cidade_posto", "uf_posto", "motorista"
        ]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # Grupo de combustível — usa tabela torre.combustivel_classificacao (DW)
        if "nome_combustivel" in df.columns:
            fuel_map = self._get_fuel_map()
            df["grupo_combustivel"] = (
                df["nome_combustivel"]
                .str.lower()
                .map(fuel_map)
                .fillna("Outros")
            )

        # Normalização de Placa
        if "placa" in df.columns:
            df["placa"] = df["placa"].apply(norm_placa)
            if PLACAS_RENOMEADAS:
                df["placa"] = df["placa"].map(lambda p: PLACAS_RENOMEADAS.get(p, p))
            if IGNORAR_PLACAS:
                df = df[~df["placa"].isin(IGNORAR_PLACAS)]

        # Inicializa colunas de filial
        df["filial_nome"] = ""
        df["filial_estado"] = ""
        df["filial_regiao"] = ""
        df["flag_venda"] = False
        df["flag_combustivel_indevido"] = False

        # Palmas e CWB Base hardcoded
        if "placa" in df.columns:
            palmas_mask = df["placa"].isin(PALMAS_PLACAS)
            df.loc[palmas_mask, "filial_nome"]   = PALMAS_FILIAL["nome"]
            df.loc[palmas_mask, "filial_estado"] = PALMAS_FILIAL["estado"]
            df.loc[palmas_mask, "filial_regiao"] = PALMAS_FILIAL["regiao"]

            cwb_mask = df["placa"].isin(CWB_BASE_PLACAS)
            df.loc[cwb_mask, "filial_nome"]   = CWB_BASE_FILIAL["nome"]
            df.loc[cwb_mask, "filial_estado"] = CWB_BASE_FILIAL["estado"]
            df.loc[cwb_mask, "filial_regiao"] = CWB_BASE_FILIAL["regiao"]

        # Enriquece filiais e adiciona grupo de veículo
        df = self._enrich_filiais(df)
        df = self._add_grupo(df)

        # Garante coluna transacao_estornada
        if "transacao_estornada" not in df.columns:
            df["transacao_estornada"] = "0"

        # Split: combustível / pedágios / estornos
        estornos_mask = df["transacao_estornada"].astype(str) != "0"
        df_ok = df[~estornos_mask].copy()

        has_litragem = "litragem" in df_ok.columns
        if has_litragem:
            combustivel_mask = df_ok["litragem"] > 0
            df_combustivel = df_ok[combustivel_mask].copy()
            df_pedagios = df_ok[~combustivel_mask].copy()
        else:
            df_combustivel = df_ok.copy()
            df_pedagios = pd.DataFrame()

        df_estornos = df[estornos_mask].copy()

        # Filtra registros não operacionais (vendidos, referência, filiais desconhecidas, Outros)
        df_combustivel = self._filter_operational(df_combustivel, "transacoes")
        df_pedagios    = self._filter_operational(df_pedagios,    "pedagios")

        logger.info(
            f"Cache DW split: {len(df_combustivel)} combustível, "
            f"{len(df_pedagios)} pedágios, {len(df_estornos)} estornos"
        )

        return df_combustivel, df_pedagios, df_estornos

    # ═══════════════════════════════════════════════════════════════════════════
    # FETCH legado (PostgreSQL Railway)
    # ═══════════════════════════════════════════════════════════════════════════
    def _fetch_generic(self, key: str) -> pd.DataFrame:
        """Busca genérica para tabelas do TruckPag no PostgreSQL."""
        logger.info(f"Cache: Carregando {key} do PostgreSQL...")
        from db import get_engine
        from sqlalchemy import text

        query = self._cache[key]["query"]
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

        # Grupo de combustível (4 grupos: Diesel, Gasolina, Álcool, Arla)
        if "nome_combustivel" in df.columns:
            fuel_map = self._get_fuel_map()
            df["grupo_combustivel"] = (
                df["nome_combustivel"]
                .str.lower()
                .map(fuel_map)
                .fillna("Outros")
            )

        # Normalização de Placa e Filtros Iniciais
        df["placa"] = df["placa"].apply(norm_placa)
        if PLACAS_RENOMEADAS:
            df["placa"] = df["placa"].map(lambda p: PLACAS_RENOMEADAS.get(p, p))
        if IGNORAR_PLACAS:
            df = df[~df["placa"].isin(IGNORAR_PLACAS)]

        # Inicializa colunas de filial
        df["filial_nome"] = ""
        df["filial_estado"] = ""
        df["filial_regiao"] = ""
        df["flag_venda"] = False
        df["flag_combustivel_indevido"] = False

        # Palmas e CWB Base
        palmas_mask = df["placa"].isin(PALMAS_PLACAS)
        df.loc[palmas_mask, "filial_nome"]   = PALMAS_FILIAL["nome"]
        df.loc[palmas_mask, "filial_estado"] = PALMAS_FILIAL["estado"]
        df.loc[palmas_mask, "filial_regiao"] = PALMAS_FILIAL["regiao"]

        cwb_mask = df["placa"].isin(CWB_BASE_PLACAS)
        df.loc[cwb_mask, "filial_nome"]   = CWB_BASE_FILIAL["nome"]
        df.loc[cwb_mask, "filial_estado"] = CWB_BASE_FILIAL["estado"]
        df.loc[cwb_mask, "filial_regiao"] = CWB_BASE_FILIAL["regiao"]

        logger.info(f"Cache: {len(df)} registros de {key} carregados")
        return df

    def _enrich_filiais(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cruza as transações com torre.veiculo_classificacao (DW) para preencher
        filial, grupo_veiculo, modelo, marca e idade. A tabela é gerada pelo
        etl_veiculos.py — SQL Server + classificação Python pré-computada.
        """
        try:
            from db_dw import get_dw_engine
            from sqlalchemy import text

            with get_dw_engine().connect() as conn:
                result = conn.execute(text("""
                    SELECT placa, modelo, montadora, grupo_veiculo,
                           tanque_litros, ano_modelo, filial_operacional
                    FROM torre.veiculo_classificacao
                """))
                veiculos = pd.DataFrame(result.fetchall(), columns=result.keys())

            veiculos["placa"] = veiculos["placa"].apply(norm_placa)
            veiculos = veiculos.drop_duplicates("placa")

            # Lookup: placa → {nome, estado, regiao, original_sigla}
            filial_lookup = {}
            for _, row in veiculos.iterrows():
                filial_op = row["filial_operacional"]
                info = FILIAIS_MAP.get(filial_op)
                if info:
                    filial_lookup[row["placa"]] = {**info, "original_sigla": filial_op}
                elif filial_op:
                    filial_lookup[row["placa"]] = {
                        "nome": filial_op, "estado": "?", "regiao": "?",
                        "original_sigla": filial_op,
                    }

            # Overrides manuais de filial por placa
            from config import FILIAL_PLATE_OVERRIDES
            for p, sigla in FILIAL_PLATE_OVERRIDES.items():
                info = FILIAIS_MAP.get(sigla)
                if info:
                    filial_lookup[norm_placa(p)] = {**info, "original_sigla": sigla}

            # Aplica filial onde ainda não foi preenchido
            mask_vazio = (df["filial_nome"] == "") | df["filial_nome"].isna()
            df.loc[mask_vazio, "filial_nome"]   = df.loc[mask_vazio, "placa"].map(lambda p: filial_lookup.get(p, {}).get("nome", ""))
            df.loc[mask_vazio, "filial_estado"] = df.loc[mask_vazio, "placa"].map(lambda p: filial_lookup.get(p, {}).get("estado", ""))
            df.loc[mask_vazio, "filial_regiao"] = df.loc[mask_vazio, "placa"].map(lambda p: filial_lookup.get(p, {}).get("regiao", ""))

            # Flag de venda
            df["flag_venda"] = df["placa"].map(
                lambda p: "VENDA" in filial_lookup.get(p, {}).get("original_sigla", "").upper()
            )

            # Idade do veículo
            ano_map = veiculos.set_index("placa")["ano_modelo"].to_dict()
            ano_atual = datetime.now().year
            df["ano_modelo"] = df["placa"].map(ano_map).astype("Int64")
            df["idade_anos"] = df["ano_modelo"].apply(lambda a: (ano_atual - int(a)) if pd.notna(a) else None)

            # Modelo e Marca — pré-computados no ETL, usados por _add_grupo()
            modelo_map = veiculos.set_index("placa")["modelo"].to_dict()
            marca_map  = veiculos.set_index("placa")["montadora"].to_dict()
            if "modelo_veiculo" not in df.columns or df["modelo_veiculo"].eq("").all():
                df["modelo_veiculo"] = df["placa"].map(modelo_map).fillna("")
            else:
                mask = df["modelo_veiculo"].isna() | (df["modelo_veiculo"] == "")
                df.loc[mask, "modelo_veiculo"] = df.loc[mask, "placa"].map(modelo_map).fillna("")
            if "marca_veiculo" not in df.columns or df["marca_veiculo"].eq("").all():
                df["marca_veiculo"] = df["placa"].map(marca_map).fillna("")
            else:
                mask = df["marca_veiculo"].isna() | (df["marca_veiculo"] == "")
                df.loc[mask, "marca_veiculo"] = df.loc[mask, "placa"].map(marca_map).fillna("")

            # Grupo de veículo pré-computado (evita rodar VEICULO_RULES em cada transação)
            grupo_map = veiculos.set_index("placa")["grupo_veiculo"].to_dict()
            df["_grupo_pre"] = df["placa"].map(grupo_map)

        except Exception as e:
            logger.warning(f"Cache: não foi possível enriquecer via torre.veiculo_classificacao: {e}")
            df["_grupo_pre"] = None
            if "ano_modelo" not in df.columns:
                df["ano_modelo"] = None
                df["idade_anos"] = None
        return df

    def _add_grupo(self, df: pd.DataFrame) -> pd.DataFrame:
        # Usa o grupo pré-computado do ETL quando disponível (mais leve);
        # cai no get_veiculo_group() apenas para placas não encontradas na tabela.
        if "_grupo_pre" in df.columns:
            modelos = df["modelo_veiculo"].tolist() if "modelo_veiculo" in df.columns else [""] * len(df)
            marcas  = df["marca_veiculo"].tolist()  if "marca_veiculo"  in df.columns else [""] * len(df)
            placas  = df["placa"].tolist()          if "placa"          in df.columns else [""] * len(df)
            grupos = []
            for pre, m, b, p in zip(df["_grupo_pre"], modelos, marcas, placas):
                if pd.notna(pre) and pre:
                    grupos.append(pre)
                else:
                    grupos.append(get_veiculo_group(str(m or ""), str(b or ""), str(p or "")))
            df["grupo_veiculo"] = grupos
            df.drop(columns=["_grupo_pre"], inplace=True)
        else:
            modelos = df["modelo_veiculo"].tolist() if "modelo_veiculo" in df.columns else [""] * len(df)
            marcas  = df["marca_veiculo"].tolist()  if "marca_veiculo"  in df.columns else [""] * len(df)
            placas  = df["placa"].tolist()          if "placa"          in df.columns else [""] * len(df)
            df["grupo_veiculo"] = [
                get_veiculo_group(str(m or ""), str(b or ""), str(p or ""))
                for m, b, p in zip(modelos, marcas, placas)
            ]

        from config import is_fuel_incompatible
        grupos_comb = df["grupo_combustivel"].tolist() if "grupo_combustivel" in df.columns else [""] * len(df)
        df["flag_combustivel_indevido"] = [
            is_fuel_incompatible(gv, gc)
            for gv, gc in zip(df["grupo_veiculo"], grupos_comb)
        ]
        return df

    def _filter_operational(self, df: pd.DataFrame, key: str = "transacoes") -> pd.DataFrame:
        """
        Remove registros que não fazem parte da frota operacional Gritsch:
          - Veículos Vendidos (flag_venda)
          - Filiais de Referência (veículos de uso interno, não faturados)
          - Filiais não mapeadas (filial_estado == "?" → sigla desconhecida no FILIAIS_MAP)
          - Combustível "Outros" (nome_combustivel sem correspondência no mapa — só para transacoes)
        """
        n_before = len(df)

        if "flag_venda" in df.columns:
            df = df[df["flag_venda"] != True]

        if "filial_nome" in df.columns:
            # Remove filiais de referência pelo nome
            df = df[~df["filial_nome"].str.startswith("Referência", na=False)]

        if "filial_estado" in df.columns:
            # Remove registros com filial não mapeada (estado desconhecido)
            df = df[df["filial_estado"] != "?"]

        if key == "transacoes" and "grupo_combustivel" in df.columns:
            # Remove combustíveis não reconhecidos (Arla mal-digitado, produtos sem classificação, etc.)
            df = df[df["grupo_combustivel"] != "Outros"]

        n_after = len(df)
        if n_before != n_after:
            logger.info(f"Cache filter_operational ({key}): {n_before - n_after} registros excluídos ({n_after} restantes)")

        return df

    def _calc_kml(self, df: pd.DataFrame) -> pd.DataFrame:
        if "hodometro" not in df.columns:
            return pd.DataFrame()
        hodo = df[df["hodometro"].notna() & (df["hodometro"] > 0)].copy()
        if hodo.empty:
            return hodo
        hodo = hodo.sort_values(["placa", "data_transacao"])
        hodo["km_percorrido"] = hodo.groupby("placa")["hodometro"].diff()
        hodo = hodo[(hodo["km_percorrido"] > 0) & (hodo["km_percorrido"] <= 2000)]
        return hodo

    # ═══════════════════════════════════════════════════════════════════════════
    # Interface pública
    # ═══════════════════════════════════════════════════════════════════════════
    def get_df(self, key: str = "transacoes") -> pd.DataFrame:
        """Retorna o DataFrame do cache, atualizando-o se necessário.
        Transações/pedágios/estornos sempre vêm do PostgreSQL Railway."""
        return self._get_df_legacy(key)

    def _get_df_from_dw(self, key: str) -> pd.DataFrame:
        """Carrega dados do DW e retorna o split correto."""
        if self._is_dw_stale():
            try:
                raw = self._fetch_dw()
                self._dw_raw = raw
                self._dw_ts = datetime.now()

                df_combustivel, df_pedagios, df_estornos = self._split_dw_data(raw)

                # Calcula KML para combustível
                kml_df = self._calc_kml(df_combustivel)

                # Atualiza todos os caches de uma vez
                self._cache["transacoes"]["df"] = df_combustivel
                self._cache["transacoes"]["kml_df"] = kml_df
                self._cache["transacoes"]["ts"] = datetime.now()

                self._cache["pedagios"]["df"] = df_pedagios
                self._cache["pedagios"]["ts"] = datetime.now()

                self._cache["estornos"]["df"] = df_estornos
                self._cache["estornos"]["ts"] = datetime.now()

                logger.info("✓ Cache DW atualizado — transações, pedágios e estornos")

            except Exception as e:
                logger.error(f"Falha ao atualizar cache DW: {e}")
                # Tenta fallback para Railway
                if self._cache[key]["df"] is None:
                    logger.warning("DW falhou e não há cache anterior — tentando fallback Railway")
                    return self._get_df_legacy(key)

        return self._cache[key]["df"] if self._cache[key]["df"] is not None else pd.DataFrame()

    def _get_df_legacy(self, key: str) -> pd.DataFrame:
        """Carrega dados do PostgreSQL Railway (fallback)."""
        if self._is_stale(key):
            try:
                if key in ["transacoes", "pedagios", "estornos"]:
                    df = self._fetch_generic(key)
                    df = self._enrich_filiais(df)
                    df = self._add_grupo(df)
                    if key in ("transacoes", "pedagios"):
                        df = self._filter_operational(df, key)

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
        kml = self._cache["transacoes"]["kml_df"]
        return kml if kml is not None else pd.DataFrame()

    def force_refresh(self, key: str = "transacoes") -> None:
        if key in self._cache:
            self._cache[key]["ts"] = None
            self.get_df(key)

    @property
    def last_updated(self) -> Optional[datetime]:
        return self._cache["transacoes"]["ts"]

    @property
    def data_source(self) -> str:
        return "PostgreSQL Railway (integration_truckpag_transacoes)"


cache = DataCache()
