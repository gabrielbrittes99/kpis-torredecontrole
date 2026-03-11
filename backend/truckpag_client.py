import hashlib
import logging
import os
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TRUCKPAG_URL = os.getenv("TRUCKPAG_URL", "https://api.truckpag.com.br")
TRUCKPAG_USER = os.getenv("TRUCKPAG_USER", "")
TRUCKPAG_PASSWORD = os.getenv("TRUCKPAG_PASSWORD", "")

# Dias por chunk para evitar timeout na API
CHUNK_DAYS = int(os.getenv("TRUCKPAG_CHUNK_DAYS", "7"))


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def get_token() -> str:
    response = httpx.post(
        f"{TRUCKPAG_URL}/auth",
        auth=(TRUCKPAG_USER, _md5(TRUCKPAG_PASSWORD)),
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["token"]


def _fetch_chunk(token: str, dtini: str, dtfim: str, todas: bool) -> list[dict]:
    """Busca um chunk de transações com retry em caso de timeout."""
    params: dict = {"dtini": dtini, "dtfim": dtfim}
    if todas:
        params["todas"] = "S"

    response = httpx.get(
        f"{TRUCKPAG_URL}/Transacoes",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=60.0,
    )
    response.raise_for_status()

    data = response.json()
    if not data:
        return []
    if isinstance(data, dict):
        return data.get("Transacoes", [])
    return []


def get_transacoes(dtini: str, dtfim: str, todas: bool = True) -> list[dict]:
    """
    Busca transações da API TruckPag em chunks semanais para evitar timeout.
    dtini, dtfim: formato YYYYMMDD
    todas=True retorna inclusive as já integradas
    """
    dt_ini = datetime.strptime(dtini, "%Y%m%d")
    dt_fim = datetime.strptime(dtfim, "%Y%m%d")

    all_transacoes: list[dict] = []
    seen_ids: set[str] = set()

    token = get_token()
    current = dt_ini

    while current <= dt_fim:
        chunk_end = min(current + timedelta(days=CHUNK_DAYS - 1), dt_fim)
        chunk_ini_str = current.strftime("%Y%m%d")
        chunk_fim_str = chunk_end.strftime("%Y%m%d")

        logger.info(f"Buscando chunk {chunk_ini_str} → {chunk_fim_str}")

        try:
            chunk = _fetch_chunk(token, chunk_ini_str, chunk_fim_str, todas)
            # Deduplica por número de transação
            for t in chunk:
                tid = str(t.get("Transacao", ""))
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    all_transacoes.append(t)
        except httpx.ReadTimeout:
            logger.warning(f"Timeout no chunk {chunk_ini_str}→{chunk_fim_str}, pulando")

        current = chunk_end + timedelta(days=1)

    logger.info(f"Total coletado: {len(all_transacoes)} transações únicas")
    return all_transacoes
