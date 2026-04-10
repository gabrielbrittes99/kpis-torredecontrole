"""
Gestão de Pneus — Endpoints REST.
Prefixo: /api/gestao-pneus
"""
import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from db_gestao_pneus import (
    ensure_tables,
    VEHICLE_CONFIGS,
    listar_filiais, criar_filial, atualizar_filial, desativar_filial,
    listar_veiculos, criar_veiculo, atualizar_veiculo, obter_veiculo_com_pneus, desativar_veiculo,
    listar_pneus, criar_pneu, atualizar_pneu, obter_pneu,
    alocar_pneu, remover_pneu, transferir_pneu, mover_pneu_veiculo,
    listar_movimentacoes, obter_dashboard, confirmar_recebimento,
    sincronizar_do_sqlserver, buscar_veiculo_sql,
    enviar_para_recicladora, listar_lotes_reciclagem,
    atualizar_valor_lote_reciclagem, obter_relatorio_financeiro_reciclagem
)
from db_pneus import get_pneus_df

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gestao-pneus", tags=["gestao-pneus"])

# Garante que as tabelas existam ao importar o módulo
try:
    ensure_tables()
except Exception as e:
    logger.error(f"Falha ao criar tabelas Gestão Pneus: {e}")


# ── Pydantic Models ────────────────────────────────────────────────────────

class FilialIn(BaseModel):
    nome: str
    cidade: str = ""
    estado: str = ""

class VeiculoIn(BaseModel):
    placa: str
    frota: str = ""
    modelo: str = ""
    marca: str = ""
    tipo: str = "truck"
    filial_id: Optional[int] = None

class PneuIn(BaseModel):
    numero_fogo: str
    marca: str
    modelo: str = ""
    medida: str
    dot: str = ""
    valor: float = 0
    vida: int = 1
    filial_id: int
    sulco_atual: float = 0
    nf: str = ""
    fornecedor: str = ""

class PneuUpdate(BaseModel):
    numero_fogo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    medida: Optional[str] = None
    dot: Optional[str] = None
    valor: Optional[float] = None
    vida: Optional[int] = None
    status: Optional[str] = None
    filial_id: Optional[int] = None
    sulco_atual: Optional[float] = None
    nf: Optional[str] = None
    fornecedor: Optional[str] = None

class AlocarIn(BaseModel):
    pneu_id: int
    veiculo_id: int
    posicao: str
    km_instalacao: float = 0
    observacao: str = ""

class RemoverIn(BaseModel):
    pneu_id: int
    destino: str = "estoque"  # estoque | descarte | recapagem
    filial_destino_id: Optional[int] = None
    km_momento: float = 0
    observacao: str = ""

class TransferirIn(BaseModel):
    pneu_id: int
    filial_destino_id: int
    observacao: str = ""


# ── CONFIGS ────────────────────────────────────────────────────────────────

@router.get("/configs/veiculos")
def get_vehicle_configs():
    """Retorna configurações de eixos por tipo de veículo."""
    return VEHICLE_CONFIGS


# ── FILIAIS ────────────────────────────────────────────────────────────────

@router.get("/filiais")
def get_filiais():
    return listar_filiais()

@router.post("/filiais")
def post_filial(body: FilialIn):
    try:
        return criar_filial(body.nome, body.cidade, body.estado)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/filiais/{filial_id}")
def put_filial(filial_id: int, body: FilialIn):
    result = atualizar_filial(filial_id, body.nome, body.cidade, body.estado)
    if not result:
        raise HTTPException(status_code=404, detail="Filial não encontrada")
    return result

@router.delete("/filiais/{filial_id}")
def delete_filial(filial_id: int):
    desativar_filial(filial_id)
    return {"ok": True}


# ── VEÍCULOS ───────────────────────────────────────────────────────────────

@router.get("/veiculos")
def get_veiculos(filial_id: Optional[int] = Query(None)):
    return listar_veiculos(filial_id=filial_id)

@router.post("/veiculos")
def post_veiculo(body: VeiculoIn):
    try:
        return criar_veiculo(
            placa=body.placa, frota=body.frota, modelo=body.modelo,
            marca=body.marca, tipo=body.tipo, filial_id=body.filial_id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/veiculos/{veiculo_id}")
def get_veiculo_detail(veiculo_id: int):
    result = obter_veiculo_com_pneus(veiculo_id)
    if not result:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return result

@router.put("/veiculos/{veiculo_id}")
def put_veiculo(veiculo_id: int, body: VeiculoIn):
    result = atualizar_veiculo(
        veiculo_id, placa=body.placa, frota=body.frota, modelo=body.modelo,
        marca=body.marca, tipo=body.tipo, filial_id=body.filial_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return result

@router.delete("/veiculos/{veiculo_id}")
def delete_veiculo(veiculo_id: int):
    desativar_veiculo(veiculo_id)
    return {"ok": True}


# ── PNEUS ──────────────────────────────────────────────────────────────────

@router.get("/pneus")
def get_pneus(
    filial_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    veiculo_id: Optional[int] = Query(None),
):
    return listar_pneus(filial_id=filial_id, status=status, veiculo_id=veiculo_id)

@router.post("/pneus")
def post_pneu(body: PneuIn):
    try:
        return criar_pneu(
            numero_fogo=body.numero_fogo, marca=body.marca, modelo=body.modelo,
            medida=body.medida, dot=body.dot, valor=body.valor,
            vida=body.vida, filial_id=body.filial_id, sulco_atual=body.sulco_atual,
            nf=body.nf, fornecedor=body.fornecedor
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pneus/{pneu_id}")
def get_pneu_detail(pneu_id: int):
    result = obter_pneu(pneu_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pneu não encontrado")
    return result

@router.put("/pneus/{pneu_id}")
def put_pneu(pneu_id: int, body: PneuUpdate):
    result = atualizar_pneu(pneu_id, **body.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Pneu não encontrado")
    return result

@router.post("/confirmar-recebimento", tags=["operacoes"])
def post_confirmar_recebimento(body: dict):
    pneu_id = body.get("pneu_id")
    if not pneu_id:
        raise HTTPException(status_code=400, detail="pneu_id é obrigatório")
    confirmar_recebimento(pneu_id)
    return {"ok": True}


@router.post("/rodizio")
def post_rodizio(body: dict):
    mover_pneu_veiculo(
        veiculo_id=body["veiculo_id"],
        pos_origem=body["pos_origem"],
        pos_destino=body["pos_destino"],
        observacao=body.get("observacao", ""),
        km_momento=body.get("km_momento")
    )
    return {"ok": True}


# ── OPERAÇÕES ──────────────────────────────────────────────────────────────

@router.post("/alocar")
def post_alocar(body: AlocarIn):
    try:
        return alocar_pneu(
            pneu_id=body.pneu_id, veiculo_id=body.veiculo_id,
            posicao=body.posicao, km_instalacao=body.km_instalacao,
            observacao=body.observacao,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/remover")
def post_remover(body: RemoverIn):
    try:
        return remover_pneu(
            pneu_id=body.pneu_id, destino=body.destino,
            km_momento=body.km_momento, observacao=body.observacao,
            filial_destino_id=body.filial_destino_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transferir")
def post_transferir(body: TransferirIn):
    try:
        return transferir_pneu(
            pneu_id=body.pneu_id, filial_destino_id=body.filial_destino_id,
            observacao=body.observacao,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── MOVIMENTAÇÕES ──────────────────────────────────────────────────────────

@router.get("/movimentacoes")
def get_movimentacoes(
    pneu_id: Optional[int] = Query(None),
    veiculo_id: Optional[int] = Query(None),
    filial_id: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    limit: int = Query(100),
):
    return listar_movimentacoes(
        pneu_id=pneu_id, veiculo_id=veiculo_id,
        filial_id=filial_id, tipo=tipo, limit=limit,
    )


# ── DASHBOARD ──────────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard():
    try:
        return obter_dashboard()
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── RECICLAGEM ─────────────────────────────────────────────────────────────

@router.post("/reciclagem/enviar", tags=["operacoes"])
def post_enviar_reciclagem(body: dict):
    try:
        return enviar_para_recicladora(
            pneu_id=body["pneu_id"],
            data_envio=body["data_envio"],
            observacao=body.get("observacao", "")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reciclagem/lotes")
def get_lotes_reciclagem(filial_id: Optional[int] = Query(None)):
    return listar_lotes_reciclagem(filial_id=filial_id)

@router.post("/reciclagem/atualizar-valor")
def post_atualizar_valor_lote(body: dict):
    try:
        return atualizar_valor_lote_reciclagem(lote_id=body["lote_id"], valor_total=body["valor_total"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reciclagem/relatorio-financeiro")
def get_relatorio_financeiro_reciclagem(mes: Optional[str] = Query(None), filial_id: Optional[int] = Query(None)):
    return obter_relatorio_financeiro_reciclagem(mes=mes, filial_id=filial_id)


# ── SINCRONIZAÇÃO SQL SERVER ───────────────────────────────────────────────

@router.post("/sincronizar")
def post_sincronizar():
    """Importa filiais do SQL Server para o SQLite local."""
    try:
        resultado = sincronizar_do_sqlserver()
        return resultado
    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/busca-veiculo-sql/{placa}")
def get_busca_veiculo_sql(placa: str):
    """Busca dados de um veículo pelo SQL Server usando a Placa."""
    try:
        resultado = buscar_veiculo_sql(placa)
        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado na base SQL")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na busca do SQL Server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/planilha-pneus")
def get_planilha_pneus():
    """Retorna os pneus listados na planilha online FR PNEUS para auto-completar no frontend."""
    try:
        df = get_pneus_df()
        if df.empty:
            return []
        
        # Filtramos as colunas que importam, removemos duplicatas pelo n_fogo
        # e tratamos valores nulos
        df_clean = df.drop_duplicates(subset=["n_fogo"], keep="last")
        colunas_importam = ["n_fogo", "dot", "medida", "marca", "modelo", "fornecedor", "nf", "valor_un"]
        cols_existentes = [c for c in colunas_importam if c in df_clean.columns]
        
        df_out = df_clean[cols_existentes].fillna("")
        # Removemos os que não tem numero de fogo valido
        df_out = df_out[df_out["n_fogo"].astype(str).str.strip() != ""]
        
        return df_out.to_dict("records")
    except Exception as e:
        logger.error(f"Erro ao buscar planilha pneus: {e}")
        return []
