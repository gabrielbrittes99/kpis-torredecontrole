"""
Vínculo Placa → Contrato — validado pelo gestor.

Permite que gestores registrem qual veículo está rodando em qual contrato,
com vigência (data inicial e data final opcional).
Toda placa precisa de vínculo para compor o FKM on-demand corretamente.

Tabela: torre.veiculo_contrato (DW)

Endpoints:
  GET    /api/veiculo-contrato/                    — lista vínculos vigentes (ou todos)
  POST   /api/veiculo-contrato/                    — cria novo vínculo
  PUT    /api/veiculo-contrato/{id}/encerrar       — encerra vigência de um vínculo
  DELETE /api/veiculo-contrato/{id}                — remove vínculo
  GET    /api/veiculo-contrato/sem-contrato        — placas sem contrato no mês (alerta)
"""
import logging
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/veiculo-contrato", tags=["veiculo-contrato"])


def _norm_placa(placa) -> str:
    return str(placa or "").upper().replace("-", "").strip()


def _get_dw():
    from db_dw import get_dw_engine
    return get_dw_engine()


# ── Schemas ───────────────────────────────────────────────────────────────────

class VinculoCreate(BaseModel):
    placa: str
    contrato: str
    filial: Optional[str] = ""
    vigencia_ini: date
    validado_por: Optional[str] = ""
    observacao: Optional[str] = ""


class VinculoEncerrar(BaseModel):
    vigencia_fim: date


# ── Listar vínculos ───────────────────────────────────────────────────────────

@router.get("/", summary="Lista vínculos placa→contrato")
def listar_vinculos(
    apenas_vigentes: bool = Query(default=True, description="Se True, retorna só vínculos vigentes hoje"),
    filial: Optional[str] = Query(default=None),
    contrato: Optional[str] = Query(default=None),
):
    """
    Lista todos os vínculos placa→contrato.
    Por padrão retorna apenas os vigentes (vigencia_fim IS NULL ou >= hoje).
    """
    try:
        engine = _get_dw()
        hoje = date.today().isoformat()
        conditions = []
        params: dict = {}

        if apenas_vigentes:
            conditions.append(
                "(vigencia_fim IS NULL OR vigencia_fim >= %(hoje)s)"
            )
            params["hoje"] = hoje
        if filial:
            conditions.append("filial ILIKE %(filial)s")
            params["filial"] = f"%{filial}%"
        if contrato:
            conditions.append("contrato ILIKE %(contrato)s")
            params["contrato"] = f"%{contrato}%"

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"""
            SELECT id, placa, contrato, filial, vigencia_ini, vigencia_fim,
                   validado_por, validado_em, observacao
            FROM torre.veiculo_contrato
            {where}
            ORDER BY placa, vigencia_ini DESC
        """
        df = pd.read_sql(sql, engine, params=params)
    except Exception as e:
        raise HTTPException(500, f"Erro ao consultar banco: {e}")

    return {
        "total": len(df),
        "vinculos": df.fillna("").to_dict(orient="records"),
    }


# ── Criar vínculo ─────────────────────────────────────────────────────────────

@router.post("/", summary="Cria vínculo placa→contrato")
def criar_vinculo(body: VinculoCreate):
    """
    Registra um novo vínculo placa→contrato.
    Se a placa já tiver um vínculo vigente sem data de fim,
    ele é encerrado automaticamente (vigencia_fim = vigencia_ini do novo - 1 dia).
    """
    placa = _norm_placa(body.placa)
    if len(placa) < 7:
        raise HTTPException(400, f"Placa inválida: '{body.placa}'")

    try:
        engine = _get_dw()
        with engine.connect() as conn:
            # Encerra vínculo anterior aberto da mesma placa
            conn.execute(
                """
                UPDATE torre.veiculo_contrato
                SET vigencia_fim = %(nova_ini)s - INTERVAL '1 day'
                WHERE placa = %(placa)s
                  AND vigencia_fim IS NULL
                  AND vigencia_ini < %(nova_ini)s
                """,
                {"placa": placa, "nova_ini": body.vigencia_ini.isoformat()},
            )

            result = conn.execute(
                """
                INSERT INTO torre.veiculo_contrato
                    (placa, contrato, filial, vigencia_ini, validado_por, observacao)
                VALUES
                    (%(placa)s, %(contrato)s, %(filial)s, %(vigencia_ini)s,
                     %(validado_por)s, %(observacao)s)
                RETURNING id
                """,
                {
                    "placa": placa,
                    "contrato": body.contrato.strip(),
                    "filial": (body.filial or "").strip(),
                    "vigencia_ini": body.vigencia_ini.isoformat(),
                    "validado_por": (body.validado_por or "").strip(),
                    "observacao": (body.observacao or "").strip(),
                },
            )
            novo_id = result.fetchone()[0]
            conn.commit()

        logger.info(f"veiculo_contrato: vínculo criado id={novo_id} placa={placa} contrato={body.contrato}")
    except Exception as e:
        logger.error(f"veiculo_contrato: falha ao criar vínculo: {e}")
        raise HTTPException(500, f"Erro ao salvar vínculo: {e}")

    # Invalida cache FKM
    try:
        from db_fkm_ondemand import refresh_fkm_cache
        refresh_fkm_cache()
    except Exception:
        pass

    return {"ok": True, "id": novo_id, "placa": placa, "contrato": body.contrato}


# ── Encerrar vigência ─────────────────────────────────────────────────────────

@router.put("/{vinculo_id}/encerrar", summary="Encerra vigência de um vínculo")
def encerrar_vinculo(vinculo_id: int, body: VinculoEncerrar):
    """Define a data de fim de um vínculo, tornando-o histórico."""
    try:
        engine = _get_dw()
        with engine.connect() as conn:
            result = conn.execute(
                """
                UPDATE torre.veiculo_contrato
                SET vigencia_fim = %(fim)s
                WHERE id = %(id)s
                RETURNING id
                """,
                {"fim": body.vigencia_fim.isoformat(), "id": vinculo_id},
            )
            updated = result.rowcount
            conn.commit()
    except Exception as e:
        raise HTTPException(500, f"Erro ao encerrar vínculo: {e}")

    if updated == 0:
        raise HTTPException(404, f"Vínculo {vinculo_id} não encontrado")

    try:
        from db_fkm_ondemand import refresh_fkm_cache
        refresh_fkm_cache()
    except Exception:
        pass

    return {"ok": True, "id": vinculo_id, "vigencia_fim": body.vigencia_fim.isoformat()}


# ── Deletar vínculo ───────────────────────────────────────────────────────────

@router.delete("/{vinculo_id}", summary="Remove um vínculo placa→contrato")
def deletar_vinculo(vinculo_id: int):
    """Remove permanentemente um vínculo. Use 'encerrar' para histórico."""
    try:
        engine = _get_dw()
        with engine.connect() as conn:
            result = conn.execute(
                "DELETE FROM torre.veiculo_contrato WHERE id = %(id)s RETURNING id",
                {"id": vinculo_id},
            )
            deleted = result.rowcount
            conn.commit()
    except Exception as e:
        raise HTTPException(500, f"Erro ao deletar vínculo: {e}")

    if deleted == 0:
        raise HTTPException(404, f"Vínculo {vinculo_id} não encontrado")

    try:
        from db_fkm_ondemand import refresh_fkm_cache
        refresh_fkm_cache()
    except Exception:
        pass

    return {"ok": True, "id": vinculo_id, "deletado": True}


# ── Placas sem contrato ───────────────────────────────────────────────────────

@router.get("/sem-contrato", summary="Placas ativas sem contrato no mês")
def placas_sem_contrato(
    ano_mes: Optional[str] = Query(default=None, description="Ex: 2026-04"),
):
    """
    Retorna placas que apareceram no FKM do mês (manutenção ou combustível)
    mas não têm vínculo de contrato vigente.
    Útil como alerta pré-fechamento.
    """
    if not ano_mes:
        hoje = date.today()
        ano_mes = f"{hoje.year}-{hoje.month:02d}"

    ano_str, mes_str = ano_mes[:4], ano_mes[5:7]

    # Placas com vínculo vigente no mês
    import calendar
    ano, mes = int(ano_str), int(mes_str)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    prim_dia = f"{ano_mes}-01"
    ult_dia = f"{ano_mes}-{ultimo_dia:02d}"

    try:
        engine = _get_dw()
        df_vc = pd.read_sql(
            """
            SELECT DISTINCT placa
            FROM torre.veiculo_contrato
            WHERE vigencia_ini <= %(ult_dia)s
              AND (vigencia_fim IS NULL OR vigencia_fim >= %(prim_dia)s)
            """,
            engine,
            params={"ult_dia": ult_dia, "prim_dia": prim_dia},
        )
        placas_com_contrato = set(df_vc["placa"].apply(_norm_placa).tolist())
    except Exception as e:
        logger.warning(f"veiculo_contrato: falha ao buscar vínculos: {e}")
        placas_com_contrato = set()

    # Placas no FKM do mês (usa cache se disponível)
    try:
        from db_fkm_ondemand import get_fkm_df
        df_fkm = get_fkm_df()
        placas_fkm = set(df_fkm["placa"].dropna().unique().tolist())
    except Exception:
        placas_fkm = set()

    sem_contrato = sorted(placas_fkm - placas_com_contrato)

    # Enriquece com modelo/filial do SQL Server se disponível
    detalhes = []
    try:
        from db_sqlserver import get_veiculos_df
        veiculos = get_veiculos_df()
        v_map = veiculos.set_index("Placa")[["Modelo", "FilialOperacional"]].to_dict("index") if not veiculos.empty else {}
        for placa in sem_contrato:
            info = v_map.get(placa, {})
            detalhes.append({
                "placa": placa,
                "modelo": info.get("Modelo", ""),
                "filial": info.get("FilialOperacional", ""),
            })
    except Exception:
        detalhes = [{"placa": p, "modelo": "", "filial": ""} for p in sem_contrato]

    return {
        "ano_mes": ano_mes,
        "total_sem_contrato": len(sem_contrato),
        "placas": detalhes,
    }
