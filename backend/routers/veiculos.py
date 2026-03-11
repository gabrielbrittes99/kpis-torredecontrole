"""
Seção 5 — Dados de Frota (SQL Server / BlueFleet)
Veículos e filiais vindos do sistema BlueFleet da Gritsch.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from db_sqlserver import get_sqlserver_conn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/veiculos", tags=["veiculos"])


def _query(sql: str, params=None) -> list[dict]:
    try:
        conn = get_sqlserver_conn()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            clean = {}
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    clean[k] = v.isoformat()
                elif hasattr(v, "__float__"):
                    clean[k] = float(v)
                else:
                    clean[k] = v
            result.append(clean)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"SQL Server error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lista")
def get_lista_veiculos(
    filial: Optional[str] = Query(None, description="Filtrar por filial operacional"),
):
    """Lista veículos com campos relevantes para cruzamento com TruckPag."""
    where = "WHERE 1=1"
    params = []
    if filial:
        where += " AND FilialOperacional LIKE %s"
        params.append(f"%{filial}%")

    sql = f"""
        SELECT
            Placa,
            Modelo,
            Montadora,
            AnoModelo,
            AnoFabricacao,
            Cor,
            Filial,
            FilialOperacional,
            IdadeEmMeses,
            TanqueLitros,
            ValorCompra,
            ValorAtualFIPE,
            Proprietario
        FROM veiculos
        {where}
        ORDER BY FilialOperacional, Placa
    """
    return _query(sql, params or None)


@router.get("/por-filial")
def get_por_filial():
    """Quantidade de veículos por filial operacional."""
    sql = """
        SELECT
            FilialOperacional,
            COUNT(*) AS qtd_veiculos,
            AVG(CAST(IdadeEmMeses AS FLOAT)) AS idade_media_meses,
            SUM(CAST(ValorAtualFIPE AS FLOAT)) AS valor_fipe_total
        FROM veiculos
        GROUP BY FilialOperacional
        ORDER BY qtd_veiculos DESC
    """
    return _query(sql)


@router.get("/health")
def get_sqlserver_health():
    """Verifica conexão com SQL Server."""
    try:
        conn = get_sqlserver_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM veiculos")
        total = cursor.fetchone()[0]
        conn.close()
        return {"status": "ok", "total_veiculos": total}
    except RuntimeError as e:
        return {"status": "not_configured", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
