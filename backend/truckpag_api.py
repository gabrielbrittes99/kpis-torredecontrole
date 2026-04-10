import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TruckPagAPI:
    """
    Cliente para a API da TruckPag (Integração Clientes).
    Autenticação via Bearer Token fixo (variável de ambiente).
    """

    def __init__(self):
        self.base_url = os.getenv("TRUCKPAG_URL", "https://api.prd.truckpag.com.br").rstrip("/")
        self.token = os.getenv("TRUCKPAG_TOKEN")

        if not self.token:
            logger.warning("TruckPagAPI: TRUCKPAG_TOKEN não configurado no .env")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get_transacoes_analitico(
        self,
        data_inicio: str,
        data_fim: str,
        status: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        POST /api/integracao-clientes/relatorios/analitico-transacao
        status: ["RECUSADA"] = apenas recusadas, None = todas
        """
        url = f"{self.base_url}/api/integracao-clientes/relatorios/analitico-transacao"
        body: Dict[str, Any] = {
            "data_inicial": data_inicio,
            "data_final": data_fim,
        }
        # Nota: a API ignora/rejeita transacao_status no body — filtramos client-side abaixo

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.post(url, json=body, headers=self._headers(), timeout=60)
                response.raise_for_status()
                data = response.json()
                # A API pode retornar lista direta ou objeto com chave 'data'
                items: list = data if isinstance(data, list) else data.get("data", data.get("transacoes", []))
                # Nota: o campo transacao_status no body é ignorado pela API — filtramos client-side
                if status:
                    status_upper = {s.upper() for s in status}
                    items = [t for t in items if str(t.get("transacao_status", "")).upper() in status_upper]
                return items
            except httpx.HTTPStatusError as e:
                logger.error(f"TruckPagAPI HTTP {e.response.status_code}: {e.response.text[:300]}")
                return []
            except Exception as e:
                logger.error(f"TruckPagAPI: Erro ao buscar transações analíticas: {e}")
                return []

    async def get_veiculos(self) -> List[Dict[str, Any]]:
        """GET /api/integracao-clientes/veiculo"""
        url = f"{self.base_url}/api/integracao-clientes/veiculo"
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=self._headers(), timeout=20)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    return data
                return data.get("data", [])
            except Exception as e:
                logger.error(f"TruckPagAPI: Erro ao buscar veículos: {e}")
                return []


# Instância global
truckpag_api = TruckPagAPI()
