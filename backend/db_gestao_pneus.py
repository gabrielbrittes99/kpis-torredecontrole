"""
Gestão de Pneus — Camada de banco de dados (SQLite local).
Tabelas: gp_filiais, gp_veiculos, gp_pneus, gp_movimentacoes.
Banco: backend/gestao_pneus.db
"""
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

_gp_engine = None

def _get_gp_engine():
    global _gp_engine
    if _gp_engine is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gestao_pneus.db")
        _gp_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return _gp_engine


# ── Configurações de eixos por tipo de veículo ─────────────────────────────

VEHICLE_CONFIGS = {
    "simples": {
        "nome": "1. Simples",
        "eixos": [
            {"num": 1, "nome": "Eixo 1 - Direção", "tipo": "simples", "posicoes": ["E1_ESQ", "E1_DIR"]},
            {"num": 2, "nome": "Eixo 2 - Traseiro", "tipo": "simples", "posicoes": ["E2_ESQ", "E2_DIR"]},
        ],
        "estepes": ["ESTEPE_1"],
    },
    "toco": {
        "nome": "2. Toco",
        "eixos": [
            {"num": 1, "nome": "Eixo 1 - Direção", "tipo": "simples", "posicoes": ["E1_ESQ", "E1_DIR"]},
            {"num": 2, "nome": "Eixo 2 - Tração", "tipo": "duplo", "posicoes": ["E2_ESQ_EXT", "E2_ESQ_INT", "E2_DIR_INT", "E2_DIR_EXT"]},
        ],
        "estepes": ["ESTEPE_1"],
    },
    "truck": {
        "nome": "3. Truck",
        "eixos": [
            {"num": 1, "nome": "Eixo 1 - Direção", "tipo": "simples", "posicoes": ["E1_ESQ", "E1_DIR"]},
            {"num": 2, "nome": "Eixo 2 - Tração", "tipo": "duplo", "posicoes": ["E2_ESQ_EXT", "E2_ESQ_INT", "E2_DIR_INT", "E2_DIR_EXT"]},
            {"num": 3, "nome": "Eixo 3 - Truck", "tipo": "duplo", "posicoes": ["E3_ESQ_EXT", "E3_ESQ_INT", "E3_DIR_INT", "E3_DIR_EXT"]},
        ],
        "estepes": ["ESTEPE_1"],
    },
    "bitruck": {
        "nome": "4. Bitruck",
        "eixos": [
            {"num": 1, "nome": "Eixo 1 - Direção", "tipo": "simples", "posicoes": ["E1_ESQ", "E1_DIR"]},
            {"num": 2, "nome": "Eixo 2 - Direcional", "tipo": "simples", "posicoes": ["E2_ESQ", "E2_DIR"]},
            {"num": 3, "nome": "Eixo 3 - Tração", "tipo": "duplo", "posicoes": ["E3_ESQ_EXT", "E3_ESQ_INT", "E3_DIR_INT", "E3_DIR_EXT"]},
            {"num": 4, "nome": "Eixo 4 - Truck", "tipo": "duplo", "posicoes": ["E4_ESQ_EXT", "E4_ESQ_INT", "E4_DIR_INT", "E4_DIR_EXT"]},
        ],
        "estepes": ["ESTEPE_1", "ESTEPE_2"],
    },
}

# ── Mapeamento de GrupoVeiculo SQL Server → tipo local ─────────────────────
# Ajuste conforme os valores reais do seu SQL Server
GRUPO_TO_TIPO = {
    "TOCO": "toco",
    "TRUCK": "truck",
    "BITRUCK": "bitruck",
    "CAVALO 4X2": "toco",
    "CAVALO MECANICO 4X2": "toco",
    "CAVALO 6X4": "truck",
    "CAVALO MECANICO 6X4": "truck",
    "CARRETA": "truck",
    "CARRETA 2 EIXOS": "toco",
    "CARRETA 3 EIXOS": "truck",
    "BITREM": "bitruck",
    "SEMI REBOQUE": "truck",
    "SAVEIRO": "simples",
    "PICK-UP": "simples",
    "UTILITARIO": "simples",
    "VAN": "simples",
    "ONIBUS": "truck",
}


def _inferir_tipo(grupo_veiculo: str, modelo: str = "") -> str:
    """Tenta mapear GrupoVeiculo/Modelo do SQL Server para um tipo de eixo local."""
    if not grupo_veiculo:
        return "truck"
    norm = str(grupo_veiculo).upper().strip()
    # Busca direta
    if norm in GRUPO_TO_TIPO:
        return GRUPO_TO_TIPO[norm]
    # Busca parcial
    for chave, tipo in GRUPO_TO_TIPO.items():
        if chave in norm or norm in chave:
            return tipo
    # Se modelo contém pistas
    mod = str(modelo).upper()
    if "SAVEIRO" in mod or "PICK" in mod or "UNO" in mod or "FIORINO" in mod:
        return "simples"
    if "CARRETA" in mod or "SEMI" in mod:
        return "truck"
    return "truck"  # Padrão seguro


def sincronizar_do_sqlserver():
    """
    Lê filiais e veículos do SQL Server (tabela Veiculos) e
    insere no SQLite local os que ainda não existem.
    Retorna um resumo da operação.
    """
    from db_sqlserver import get_veiculos_df

    df = get_veiculos_df()
    if df.empty:
        return {"ok": False, "erro": "Nenhum veículo retornado do SQL Server"}

    # Filtrar apenas veículos ativos da Gritsch (sem referência e sem baixados)
    if "FilialOperacional" in df.columns:
        df = df[df["FilialOperacional"].str.contains("GRITSCH", case=False, na=False)]
        df = df[~df["FilialOperacional"].str.upper().str.contains("REFERENCIA|REFERÊNCIA", na=False)]
    if "SituacaoVeiculo" in df.columns:
        df = df[~df["SituacaoVeiculo"].str.upper().str.contains("BAIXADO|REFERENCIA|REFERÊNCIA", na=False)]
    if "GrupoVeiculo" in df.columns:
        df = df[~df["GrupoVeiculo"].str.upper().str.contains("REFERENCIA|REFERÊNCIA", na=False)]

    engine = _get_gp_engine()
    filiais_criadas = 0
    filiais_existentes = 0
    veiculos_criados = 0
    veiculos_existentes = 0
    veiculos_atualizados = 0

    with engine.begin() as conn:
        # ── 1. Sincronizar FILIAIS ────────────────────────────────────
        filiais_sql = df["FilialOperacional"].dropna().unique().tolist()
        filiais_sql = [f.strip() for f in filiais_sql if f and str(f).strip()]

        # Carregar filiais já existentes
        rows_filiais = conn.execute(text("SELECT id, nome FROM gp_filiais WHERE ativo=1")).mappings().all()
        filiais_map = {str(r["nome"]).upper().strip(): r["id"] for r in rows_filiais}

        for nome_filial in filiais_sql:
            nome_norm = nome_filial.upper().strip()
            if nome_norm not in filiais_map:
                result = conn.execute(
                    text("INSERT INTO gp_filiais (nome, cidade, estado) VALUES (:n, '', '')"),
                    {"n": nome_filial.strip()}
                )
                novo_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
                filiais_map[nome_norm] = novo_id
                filiais_criadas += 1
            else:
                filiais_existentes += 1

        # ── 2. NÃO SINCRONIZAR VEÍCULOS AUTOMATICAMENTE ─────────────────
        # A pedido do usuário, veículos só entram 1 a 1 via busca por placa.

    logger.info(
        f"Sincronização SQL Server → SQLite: "
        f"filiais criadas={filiais_criadas} existentes={filiais_existentes}"
    )

    return {
        "ok": True,
        "filiais_criadas": filiais_criadas,
        "filiais_existentes": filiais_existentes,
        "veiculos_criados": 0,
        "veiculos_existentes": 0,
        "veiculos_atualizados": 0,
        "total_sql": len(df),
    }

def buscar_veiculo_sql(placa):
    """
    Busca os dados de um veículo específico no SQL Server pela placa.
    """
    from sqlalchemy import text
    from db_sqlserver import get_veiculos_df
    df = get_veiculos_df()
    if df.empty:
        return None
        
    placa_limpa = str(placa).upper().strip().replace("-", "")
    
    df["PlacaLimpa"] = df.get("Placa", "").fillna("").astype(str).str.upper().str.strip().str.replace("-", "")
    veiculo_df = df[df["PlacaLimpa"] == placa_limpa]
    if veiculo_df.empty:
        return None
        
    row = veiculo_df.iloc[0]
    
    grupo = str(row.get("GrupoVeiculo", "")).strip()
    modelo = str(row.get("Modelo", "")).strip()
    marca = str(row.get("Montadora", "")).strip()
    filial_nome = str(row.get("FilialOperacional", "")).strip()
    tipo = _inferir_tipo(grupo, modelo)
    
    filial_id = None
    if filial_nome:
        engine = _get_gp_engine()
        with engine.connect() as conn:
            row_f = conn.execute(
                text("SELECT id FROM gp_filiais WHERE UPPER(nome) = :n AND ativo=1"),
                {"n": filial_nome.upper()}
            ).mappings().first()
            if row_f:
                filial_id = row_f["id"]
                
    return {
        "placa": str(row.get("Placa", "")).strip(),
        "frota": "",
        "modelo": modelo,
        "marca": marca,
        "tipo": tipo,
        "filial_nome": filial_nome,
        "filial_id": filial_id
    }


# ── Criação das tabelas ────────────────────────────────────────────────────

_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS gp_filiais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        cidade TEXT,
        estado TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS gp_veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT NOT NULL UNIQUE,
        frota TEXT,
        modelo TEXT,
        marca TEXT,
        tipo TEXT DEFAULT 'truck',
        filial_id INTEGER REFERENCES gp_filiais(id),
        ativo INTEGER DEFAULT 1,
        criado_em TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS gp_pneus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_fogo TEXT NOT NULL UNIQUE,
        marca TEXT NOT NULL,
        modelo TEXT,
        medida TEXT NOT NULL,
        dot TEXT,
        valor REAL DEFAULT 0,
        status TEXT DEFAULT 'estoque',
        vida INTEGER DEFAULT 1,
        filial_id INTEGER REFERENCES gp_filiais(id),
        veiculo_id INTEGER REFERENCES gp_veiculos(id),
        posicao TEXT,
        km_instalacao REAL DEFAULT 0,
        sulco_atual REAL DEFAULT 0,
        km_total REAL DEFAULT 0,
        cpk REAL DEFAULT 0,
        nf TEXT,
        fornecedor TEXT,
        recebido INTEGER DEFAULT 1,
        lote_id INTEGER REFERENCES gp_lotes_reciclagem(id),
        criado_em TEXT DEFAULT (datetime('now', 'localtime')),
        atualizado_em TEXT DEFAULT (datetime('now', 'localtime'))
    )""",
    """CREATE TABLE IF NOT EXISTS gp_movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pneu_id INTEGER REFERENCES gp_pneus(id),
        tipo TEXT NOT NULL,
        filial_origem_id INTEGER REFERENCES gp_filiais(id),
        filial_destino_id INTEGER REFERENCES gp_filiais(id),
        veiculo_id INTEGER REFERENCES gp_veiculos(id),
        posicao TEXT,
        km_momento REAL DEFAULT 0,
        observacao TEXT,
        criado_em TEXT DEFAULT (datetime('now', 'localtime'))
    )""",
    """CREATE TABLE IF NOT EXISTS gp_lotes_reciclagem (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_lote TEXT NOT NULL UNIQUE,
        data_envio TEXT NOT NULL,
        filial_id INTEGER REFERENCES gp_filiais(id),
        status TEXT DEFAULT 'enviado',
        valor_total REAL DEFAULT 0,
        valor_pneu REAL DEFAULT 0,
        criado_em TEXT DEFAULT (datetime('now', 'localtime'))
    )""",
]


def ensure_tables():
    engine = _get_gp_engine()
    with engine.begin() as conn:
        for stmt in _STATEMENTS:
            conn.execute(text(stmt))
            
        # Adiciona colunas novas caso não existam
        try: conn.execute(text("ALTER TABLE gp_pneus ADD COLUMN nf TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE gp_pneus ADD COLUMN fornecedor TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE gp_pneus ADD COLUMN km_total REAL DEFAULT 0"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE gp_pneus ADD COLUMN cpk REAL DEFAULT 0"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE gp_pneus ADD COLUMN recebido INTEGER DEFAULT 1"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE gp_pneus ADD COLUMN filial_origem_id INTEGER"))
        except Exception: pass
    logger.info("Gestão Pneus: tabelas SQLite criadas/verificadas.")


# ── Helpers ────────────────────────────────────────────────────────────────

def _e():
    return _get_gp_engine()


def _fetch_row(conn, table, row_id):
    return dict(conn.execute(text(f"SELECT * FROM {table} WHERE id = :id"), {"id": row_id}).mappings().first())


# ── FILIAIS ────────────────────────────────────────────────────────────────

def listar_filiais(apenas_ativas=True):
    try:
        sincronizar_do_sqlserver()
    except Exception as e:
        logger.warning(f"Aviso ao sincronizar filiais: {e}")

    sql = "SELECT * FROM gp_filiais"
    if apenas_ativas:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY nome"
    with _e().connect() as conn:
        return [dict(r) for r in conn.execute(text(sql)).mappings().all()]


def criar_filial(nome, cidade="", estado=""):
    with _e().begin() as conn:
        conn.execute(text("INSERT INTO gp_filiais (nome, cidade, estado) VALUES (:n, :c, :e)"),
                     {"n": nome.strip(), "c": cidade.strip(), "e": estado.strip().upper()})
        row = conn.execute(text("SELECT * FROM gp_filiais WHERE id = last_insert_rowid()")).mappings().first()
    return dict(row)


def atualizar_filial(filial_id, nome, cidade="", estado=""):
    with _e().begin() as conn:
        conn.execute(text("UPDATE gp_filiais SET nome=:n, cidade=:c, estado=:e WHERE id=:id"),
                     {"id": filial_id, "n": nome.strip(), "c": cidade.strip(), "e": estado.strip().upper()})
        row = conn.execute(text("SELECT * FROM gp_filiais WHERE id=:id"), {"id": filial_id}).mappings().first()
    return dict(row) if row else {}


def desativar_filial(filial_id):
    with _e().begin() as conn:
        conn.execute(text("UPDATE gp_filiais SET ativo=0 WHERE id=:id"), {"id": filial_id})
    return True


# ── VEÍCULOS ───────────────────────────────────────────────────────────────

def listar_veiculos(filial_id=None, apenas_ativos=True):
    sql = "SELECT v.*, f.nome as filial_nome FROM gp_veiculos v LEFT JOIN gp_filiais f ON v.filial_id=f.id WHERE 1=1"
    params = {}
    if apenas_ativos:
        sql += " AND v.ativo=1"
    if filial_id:
        sql += " AND v.filial_id=:fid"
        params["fid"] = filial_id
    sql += " ORDER BY v.placa"
    with _e().connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        result = []
        
        # Mapear KM_Atual do SQL Server
        km_map = {}
        try:
            import pandas as pd
            from db_sqlserver import get_veiculos_df
            df = get_veiculos_df()
            if not df.empty:
                df["PlacaLimpa"] = df["Placa"].fillna("").astype(str).str.upper().str.strip().str.replace("-", "")
                km_map = dict(zip(df["PlacaLimpa"], pd.to_numeric(df["OdometroConfirmado"], errors="coerce").fillna(0)))
        except Exception as e:
            logger.warning(f"Erro ao buscar KMs no listar_veiculos: {e}")

        for r in rows:
            d = dict(r)
            cnt = conn.execute(text("SELECT COUNT(*) as total FROM gp_pneus WHERE veiculo_id=:vid AND status='em_uso'"),
                               {"vid": d["id"]}).mappings().first()
            cfg = VEHICLE_CONFIGS.get(d.get("tipo", "truck"), VEHICLE_CONFIGS["truck"])
            d["pneus_alocados"] = cnt["total"] if cnt else 0
            d["total_posicoes"] = sum(len(e["posicoes"]) for e in cfg["eixos"]) + len(cfg["estepes"])
            d["km_atual"] = float(km_map.get(str(d["placa"]).upper().strip().replace("-", ""), 0))
            result.append(d)
    return result


def criar_veiculo(placa, frota="", modelo="", marca="", tipo="truck", filial_id=None):
    with _e().begin() as conn:
        conn.execute(text("INSERT INTO gp_veiculos (placa, frota, modelo, marca, tipo, filial_id) VALUES (:p,:f,:m,:ma,:t,:fi)"),
                     {"p": placa.strip().upper().replace("-",""), "f": frota.strip(), "m": modelo.strip(),
                      "ma": marca.strip(), "t": tipo, "fi": filial_id})
        row = conn.execute(text("SELECT * FROM gp_veiculos WHERE id=last_insert_rowid()")).mappings().first()
    return dict(row)


def atualizar_veiculo(veiculo_id, **kwargs):
    sets, params = [], {"id": veiculo_id}
    for key in ["placa", "frota", "modelo", "marca", "tipo", "filial_id"]:
        if key in kwargs and kwargs[key] is not None:
            val = kwargs[key]
            if key == "placa": val = str(val).strip().upper().replace("-","")
            elif isinstance(val, str): val = val.strip()
            sets.append(f"{key}=:{key}")
            params[key] = val
    if not sets:
        return {}
    with _e().begin() as conn:
        conn.execute(text(f"UPDATE gp_veiculos SET {','.join(sets)} WHERE id=:id"), params)
        row = conn.execute(text("SELECT * FROM gp_veiculos WHERE id=:id"), {"id": veiculo_id}).mappings().first()
    return dict(row) if row else {}


def obter_veiculo_com_pneus(veiculo_id):
    with _e().connect() as conn:
        vrow = conn.execute(text("SELECT v.*, f.nome as filial_nome FROM gp_veiculos v LEFT JOIN gp_filiais f ON v.filial_id=f.id WHERE v.id=:id"),
                            {"id": veiculo_id}).mappings().first()
        if not vrow:
            return {}
        veiculo = dict(vrow)
        prows = conn.execute(text("SELECT * FROM gp_pneus WHERE veiculo_id=:vid AND status='em_uso' ORDER BY posicao"),
                             {"vid": veiculo_id}).mappings().all()
        pneus_map = {dict(p)["posicao"]: dict(p) for p in prows}
    cfg = VEHICLE_CONFIGS.get(veiculo.get("tipo", "truck"), VEHICLE_CONFIGS["truck"])
    veiculo["config"] = cfg
    veiculo["pneus"] = pneus_map
    
    # Busca KM dinâmico e REAL-TIME do SQL Server (sem usar cache!)
    veiculo["km_atual"] = 0
    try:
        from db_sqlserver import get_odometro_realtime
        veiculo["km_atual"] = get_odometro_realtime(veiculo["placa"])
    except Exception as e:
        logger.warning(f"Erro ao buscar KM realtime do veículo {veiculo['placa']}: {e}")

    return veiculo


def desativar_veiculo(veiculo_id):
    with _e().begin() as conn:
        conn.execute(text("UPDATE gp_veiculos SET ativo=0 WHERE id=:id"), {"id": veiculo_id})
    return True


# ── PNEUS ──────────────────────────────────────────────────────────────────

def listar_pneus(filial_id=None, status=None, veiculo_id=None):
    sql = """SELECT p.*, f.nome as filial_nome, v.placa as veiculo_placa,
                    fo.nome as filial_origem_nome
             FROM gp_pneus p 
             LEFT JOIN gp_filiais f ON p.filial_id=f.id
             LEFT JOIN gp_filiais fo ON p.filial_origem_id=fo.id
             LEFT JOIN gp_veiculos v ON p.veiculo_id=v.id WHERE 1=1"""
    params = {}
    if filial_id:
        sql += " AND p.filial_id=:fid"; params["fid"] = filial_id
    if status:
        sql += " AND p.status=:st"; params["st"] = status
    if veiculo_id:
        sql += " AND p.veiculo_id=:vid"; params["vid"] = veiculo_id
    sql += " ORDER BY p.numero_fogo"
    with _e().connect() as conn:
        return [dict(r) for r in conn.execute(text(sql), params).mappings().all()]


def criar_pneu(numero_fogo, marca, medida, filial_id, modelo="", dot="", valor=0.0, vida=1, sulco_atual=0.0, nf="", fornecedor=""):
    with _e().begin() as conn:
        conn.execute(text("""
            INSERT INTO gp_pneus (numero_fogo, marca, modelo, medida, dot, valor, vida, filial_id, sulco_atual, nf, fornecedor)
            VALUES (:nfog, :ma, :mo, :med, :d, :val, :vi, :fi, :su, :nf, :forn)
        """), {
            "nfog": numero_fogo.strip(), "ma": marca.strip(), "mo": modelo.strip(), "med": medida.strip(),
            "d": dot.strip(), "val": float(valor), "vi": int(vida), "fi": filial_id, "su": float(sulco_atual),
            "nf": str(nf).strip(), "forn": str(fornecedor).strip()
        })
        row = conn.execute(text("SELECT * FROM gp_pneus WHERE id=last_insert_rowid()")).mappings().first()
        pneu_id = row["id"]
    _registrar_movimentacao(pneu_id, "entrada_estoque", filial_destino_id=filial_id, observacao="Pneu cadastrado no estoque")
    return dict(row)


def atualizar_pneu(pneu_id, **kwargs):
    allowed = ["numero_fogo", "marca", "modelo", "medida", "dot", "valor", "vida", "sulco_atual", "nf", "fornecedor"]
    sets, params = [], {"id": pneu_id}
    for key in allowed:
        if key in kwargs and kwargs[key] is not None:
            val = kwargs[key]
            if key == "numero_fogo": val = str(val).strip().upper()
            elif isinstance(val, str): val = val.strip()
            sets.append(f"{key}=:{key}")
            params[key] = val
    sets.append("atualizado_em=datetime('now')")
    with _e().begin() as conn:
        conn.execute(text(f"UPDATE gp_pneus SET {','.join(sets)} WHERE id=:id"), params)
        row = conn.execute(text("SELECT * FROM gp_pneus WHERE id=:id"), {"id": pneu_id}).mappings().first()
    return dict(row) if row else {}


def obter_pneu(pneu_id):
    with _e().connect() as conn:
        row = conn.execute(text("""SELECT p.*, f.nome as filial_nome, fo.nome as filial_origem_nome, v.placa as veiculo_placa
                                   FROM gp_pneus p 
                                   LEFT JOIN gp_filiais f ON p.filial_id=f.id
                                   LEFT JOIN gp_filiais fo ON p.filial_origem_id=fo.id
                                   LEFT JOIN gp_veiculos v ON p.veiculo_id=v.id WHERE p.id=:id"""),
                           {"id": pneu_id}).mappings().first()
    return dict(row) if row else {}

def _is_sucata(filial_id, conn):
    if not filial_id: return False
    f = conn.execute(text("SELECT nome FROM gp_filiais WHERE id=:id"), {"id": filial_id}).mappings().first()
    return f and "SUCATA" in f["nome"].upper()


# ── OPERAÇÕES DE MOVIMENTAÇÃO ──────────────────────────────────────────────

def alocar_pneu(pneu_id, veiculo_id, posicao, km_instalacao=0, observacao=""):
    with _e().begin() as conn:
        pneu = conn.execute(text("SELECT * FROM gp_pneus WHERE id=:id"), {"id": pneu_id}).mappings().first()
        if not pneu: raise ValueError("Pneu não encontrado")
        if pneu["status"] != "estoque": raise ValueError(f"Pneu não está no estoque (status: {pneu['status']})")
        ocupado = conn.execute(text("SELECT id FROM gp_pneus WHERE veiculo_id=:vid AND posicao=:pos AND status='em_uso'"),
                               {"vid": veiculo_id, "pos": posicao}).mappings().first()
        if ocupado: raise ValueError(f"Posição {posicao} já está ocupada")
        veiculo = conn.execute(text("SELECT * FROM gp_veiculos WHERE id=:id"), {"id": veiculo_id}).mappings().first()
        conn.execute(text("""UPDATE gp_pneus SET status='em_uso', veiculo_id=:vid, posicao=:pos,
                             km_instalacao=:km, filial_id=:fid, recebido=1, atualizado_em=datetime('now') WHERE id=:id"""),
                     {"id": pneu_id, "vid": veiculo_id, "pos": posicao, "km": km_instalacao, "fid": veiculo["filial_id"]})
        
        _registrar_movimentacao(pneu_id, "alocacao", conn=conn, veiculo_id=veiculo_id, posicao=posicao,
                                km_momento=km_instalacao, filial_destino_id=veiculo["filial_id"] if veiculo else None,
                                observacao=observacao or f"Pneu alocado na posição {posicao}")
    return obter_pneu(pneu_id)


def remover_pneu(pneu_id, destino="estoque", km_momento=0, observacao="", filial_destino_id=None):
    with _e().begin() as conn:
        pneu = conn.execute(text("SELECT * FROM gp_pneus WHERE id=:id"), {"id": pneu_id}).mappings().first()
        if not pneu: raise ValueError("Pneu não encontrado")
        
        # Se for para descarte ou recapagem, permitimos mesmo que esteja no estoque
        if destino not in ("descarte", "recapagem") and pneu["status"] != "em_uso":
            raise ValueError(f"Pneu não está em uso (status: {pneu['status']})")
        new_status = destino if destino in ("descarte", "recapagem") else "estoque"
        tipo_mov = {"descarte": "descarte", "recapagem": "recapagem"}.get(destino, "remocao")
        
        # ── CÁLCULO DE CPK ──
        km_inst = pneu["km_instalacao"] or 0
        km_momento = float(km_momento)
        km_rodado_etapa = km_momento - km_inst if km_momento > km_inst else 0
        km_total_novo = (pneu.get("km_total") or 0) + km_rodado_etapa
        pneu_valor = float(pneu.get("valor") or 0)
        cpk_novo = (pneu_valor / km_total_novo) if km_total_novo > 0 else 0
        
        fid = filial_destino_id if filial_destino_id else pneu["filial_id"]
        
        # Só atualizamos a filial_origem se a filial atual NÃO for sucata
        # Isso garante que se o pneu já está na sucata, ele mantenha a origem anterior (operacional)
        origem_id = pneu["filial_origem_id"] # Default mantém o que já está
        if not _is_sucata(pneu["filial_id"], conn):
            origem_id = pneu["filial_id"]

        # Ao remover do veículo para estoque/descarte, marcamos como recebimento pendente (recebido=0) para a filial de destino
        conn.execute(text("""UPDATE gp_pneus SET status=:st, veiculo_id=NULL, posicao=NULL, filial_id=:fid, 
                             filial_origem_id=:origem, km_total=:kmt, cpk=:cpk, recebido=0, 
                             atualizado_em=datetime('now') WHERE id=:id"""),
                     {"id": pneu_id, "st": new_status, "fid": fid, "origem": origem_id, 
                      "kmt": km_total_novo, "cpk": cpk_novo})
        
        obs_cpk = f"Rodou {km_rodado_etapa}km. CPK Atual: R${cpk_novo:.4f}."
        obs_total = (observacao + " | " + obs_cpk) if observacao else obs_cpk

        _registrar_movimentacao(pneu_id, tipo_mov, conn=conn, veiculo_id=pneu["veiculo_id"], posicao=pneu["posicao"],
                                km_momento=km_momento, filial_origem_id=pneu["filial_id"], filial_destino_id=fid,
                                observacao=obs_total)
    return obter_pneu(pneu_id)


def transferir_pneu(pneu_id, filial_destino_id, observacao=""):
    with _e().begin() as conn:
        pneu = conn.execute(text("SELECT * FROM gp_pneus WHERE id=:id"), {"id": pneu_id}).mappings().first()
        if not pneu: raise ValueError("Pneu não encontrado")
        if pneu["status"] != "estoque": raise ValueError("Pneu precisa estar no estoque para transferir")
        
        origem_id = pneu["filial_origem_id"]
        if not _is_sucata(pneu["filial_id"], conn):
            origem_id = pneu["filial_id"]

        # Ao transferir, marcamos como recebimento pendente (recebido=0)
        conn.execute(text("UPDATE gp_pneus SET filial_id=:fid, filial_origem_id=:origem, recebido=0, atualizado_em=datetime('now') WHERE id=:id"),
                     {"id": pneu_id, "fid": filial_destino_id, "origem": origem_id})
        _registrar_movimentacao(pneu_id, "transferencia", conn=conn, filial_origem_id=origem_id,
                                filial_destino_id=filial_destino_id, observacao=observacao or "Transferência entre filiais")
    return obter_pneu(pneu_id)


def mover_pneu_veiculo(veiculo_id, pos_origem, pos_destino, observacao="", km_momento=None):
    try:
        engine = _get_gp_engine()
        with engine.begin() as conn:
            # 1. Pega dados do veículo para o KM se não informado
            if km_momento is None:
                v = conn.execute(text("SELECT km_atual FROM gp_veiculos WHERE id=:vid"), {"vid": veiculo_id}).mappings().first()
                km_v = v["km_atual"] if v else 0
            else:
                km_v = km_momento

            # 2. Identifica os pneus envolvidos
            p_orig = conn.execute(text("SELECT id FROM gp_pneus WHERE veiculo_id=:vid AND posicao=:pos"),
                                  {"vid": veiculo_id, "pos": pos_origem}).mappings().first()
            if not p_orig: raise ValueError("Nenhum pneu na posição de origem")
            
            p_dest = conn.execute(text("SELECT id FROM gp_pneus WHERE veiculo_id=:vid AND posicao=:pos"),
                                  {"vid": veiculo_id, "pos": pos_destino}).mappings().first()
            
            # 3. Executa a troca
            # Move o da origem para o destino
            conn.execute(text("UPDATE gp_pneus SET posicao=:pos, atualizado_em=datetime('now') WHERE id=:id"), 
                         {"pos": pos_destino, "id": p_orig["id"]})
            
            # Se tinha alguém no destino, move para a origem
            if p_dest:
                conn.execute(text("UPDATE gp_pneus SET posicao=:pos, atualizado_em=datetime('now') WHERE id=:id"), 
                             {"pos": pos_origem, "id": p_dest["id"]})
                
            # 4. Registra Histórico (passando a conexão ativa)
            _registrar_movimentacao(p_orig["id"], "rodizio", conn=conn, veiculo_id=veiculo_id, posicao=pos_destino, 
                                    km_momento=km_v, observacao=f"Rodízio: {pos_origem} ➔ {pos_destino} | {observacao}")
            if p_dest:
                _registrar_movimentacao(p_dest["id"], "rodizio", conn=conn, veiculo_id=veiculo_id, posicao=pos_origem, 
                                        km_momento=km_v, observacao=f"Rodízio: {pos_destino} ➔ {pos_origem} (Troca) | {observacao}")
        return True
    except Exception as e:
        logger.error(f"Erro no rodizio: {e}")
        raise e


# ── HISTÓRICO ──────────────────────────────────────────────────────────────

def _registrar_movimentacao(pneu_id, tipo, conn=None, **kw):
    stmt = text("""INSERT INTO gp_movimentacoes (pneu_id,tipo,filial_origem_id,filial_destino_id,veiculo_id,posicao,km_momento,observacao)
                   VALUES (:pid,:tp,:fo,:fd,:vid,:pos,:km,:obs)""")
    params = {"pid": pneu_id, "tp": tipo, "fo": kw.get("filial_origem_id"), "fd": kw.get("filial_destino_id"),
              "vid": kw.get("veiculo_id"), "pos": kw.get("posicao"), "km": kw.get("km_momento", 0),
              "obs": kw.get("observacao", "")}
    
    if conn:
        conn.execute(stmt, params)
    else:
        with _e().begin() as conn:
            conn.execute(stmt, params)


def listar_movimentacoes(pneu_id=None, veiculo_id=None, filial_id=None, tipo=None, limit=100):
    sql = """SELECT m.*, p.numero_fogo, p.marca as pneu_marca, p.medida as pneu_medida,
                    fo.nome as filial_origem_nome, fd.nome as filial_destino_nome, 
                    v.placa as veiculo_placa, v.tipo as veiculo_tipo
             FROM gp_movimentacoes m
             LEFT JOIN gp_pneus p ON m.pneu_id=p.id
             LEFT JOIN gp_filiais fo ON m.filial_origem_id=fo.id
             LEFT JOIN gp_filiais fd ON m.filial_destino_id=fd.id
             LEFT JOIN gp_veiculos v ON m.veiculo_id=v.id WHERE 1=1"""
    params = {}
    if pneu_id: sql += " AND m.pneu_id=:pid"; params["pid"] = pneu_id
    if veiculo_id: sql += " AND m.veiculo_id=:vid"; params["vid"] = veiculo_id
    # O filtro de filial só deve ser aplicado se o usuário explicitamente pedir, não pode ser obrigatório
    if filial_id: 
        sql += " AND (m.filial_origem_id=:fid OR m.filial_destino_id=:fid)"
        params["fid"] = filial_id
    if tipo: sql += " AND m.tipo=:tp"; params["tp"] = tipo
    sql += " ORDER BY m.id DESC LIMIT 500"
    with _e().connect() as conn:
        return [dict(r) for r in conn.execute(text(sql), params).mappings().all()]


# ── DASHBOARD KPIs ─────────────────────────────────────────────────────────

def obter_dashboard():
    with _e().connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM gp_pneus")).scalar() or 0
        estoque = conn.execute(text("SELECT COUNT(*) FROM gp_pneus WHERE status='estoque'")).scalar() or 0
        em_uso = conn.execute(text("SELECT COUNT(*) FROM gp_pneus WHERE status='em_uso'")).scalar() or 0
        descartados = conn.execute(text("SELECT COUNT(*) FROM gp_pneus WHERE status='descarte'")).scalar() or 0
        recapagem = conn.execute(text("SELECT COUNT(*) FROM gp_pneus WHERE status='recapagem'")).scalar() or 0
        veiculos = conn.execute(text("SELECT COUNT(*) FROM gp_veiculos WHERE ativo=1")).scalar() or 0
        filiais = conn.execute(text("SELECT COUNT(*) FROM gp_filiais WHERE ativo=1")).scalar() or 0
        val_estoque = conn.execute(text("SELECT COALESCE(SUM(valor),0) FROM gp_pneus WHERE status='estoque'")).scalar() or 0
        val_uso = conn.execute(text("SELECT COALESCE(SUM(valor),0) FROM gp_pneus WHERE status='em_uso'")).scalar() or 0
        est_filial = conn.execute(text("""SELECT f.nome as filial, COUNT(*) as total, COALESCE(SUM(p.valor),0) as valor
                                          FROM gp_pneus p JOIN gp_filiais f ON p.filial_id=f.id
                                          WHERE p.status='estoque' GROUP BY f.nome ORDER BY f.nome""")).mappings().all()
        
        pneus_uso = conn.execute(text("""SELECT p.id, p.numero_fogo, p.km_instalacao, v.placa as veiculo_placa, p.posicao
                                         FROM gp_pneus p JOIN gp_veiculos v ON p.veiculo_id = v.id
                                         WHERE p.status='em_uso'""")).mappings().all()

    try:
        from db_sqlserver import get_veiculos_df
        import pandas as pd
        df = get_veiculos_df()
        df["PlacaLimpa"] = df["Placa"].fillna("").astype(str).str.upper().str.strip().str.replace("-", "")
        km_map = dict(zip(df["PlacaLimpa"], pd.to_numeric(df["OdometroConfirmado"], errors="coerce").fillna(0)))
    except:
        km_map = {}

    alertas_rodizio = []
    for p in pneus_uso:
        v_placa = str(p["veiculo_placa"]).upper().strip().replace("-", "")
        km_atual = float(km_map.get(v_placa, 0))
        km_inst = float(p["km_instalacao"] or 0)
        rodado = km_atual - km_inst
        if rodado >= 7000:
            alertas_rodizio.append({
                "numero_fogo": p["numero_fogo"],
                "placa": p["veiculo_placa"],
                "posicao": p["posicao"],
                "km_rodado": rodado,
                "limite": 7000
            })
            
    alertas_rodizio = sorted(alertas_rodizio, key=lambda x: x["km_rodado"], reverse=True)

    return {
        "total_pneus": total, "em_estoque": estoque, "em_uso": em_uso,
        "descartados": descartados, "em_recapagem": recapagem,
        "total_veiculos": veiculos, "total_filiais": filiais,
        "valor_estoque": float(val_estoque), "valor_em_uso": float(val_uso),
        "estoque_por_filial": [dict(r) for r in est_filial],
        "alertas_rodizio": alertas_rodizio
    }


def confirmar_recebimento(pneu_id):
    with _e().begin() as conn:
        # Quando confirmamos o recebimento em uma filial "SUCATA", mudamos o status para 'descarte' se não estiver
        pneu = conn.execute(text("SELECT filial_id FROM gp_pneus WHERE id=:id"), {"id": pneu_id}).mappings().first()
        status_update = ""
        if pneu:
            # Busca se a filial de destino é sucata
            f = conn.execute(text("SELECT nome FROM gp_filiais WHERE id=:id"), {"id": pneu["filial_id"]}).mappings().first()
            if f and "SUCATA" in f["nome"].upper():
                status_update = ", status='descarte'"
        
        conn.execute(text(f"UPDATE gp_pneus SET recebido=1 {status_update}, atualizado_em=datetime('now') WHERE id=:id"), {"id": pneu_id})
        _registrar_movimentacao(pneu_id, "recebimento_sucata", conn=conn, filial_destino_id=pneu["filial_id"] if pneu else None, 
                                observacao="Recebimento confirmado na Sucata")
    return True


def enviar_para_recicladora(pneu_id, data_envio, observacao=''):
    with _e().begin() as conn:
        pneu = conn.execute(text("SELECT * FROM gp_pneus WHERE id=:id"), {"id": pneu_id}).mappings().first()
        if not pneu: raise ValueError("Pneu não encontrado")
        
        # 1. Encontrar ou criar o lote para esta data
        data_fmt = data_envio.replace('-', '')
        numero_lote = f"LOTE-{data_fmt}"
        
        lote = conn.execute(text("SELECT id FROM gp_lotes_reciclagem WHERE numero_lote=:n"), {"n": numero_lote}).mappings().first()
        if not lote:
            res = conn.execute(text("INSERT INTO gp_lotes_reciclagem (numero_lote, data_envio, filial_id) VALUES (:n, :d, :f)"),
                             {"n": numero_lote, "d": data_envio, "f": pneu["filial_id"]})
            lote_id = res.lastrowid
        else:
            lote_id = lote["id"]
            
        # 2. Atualizar o pneu
        conn.execute(text("UPDATE gp_pneus SET status='reciclagem', lote_id=:lid, atualizado_em=datetime('now', 'localtime') WHERE id=:id"),
                     {'id': pneu_id, 'lid': lote_id})
        
        # 3. Registrar movimentação
        _registrar_movimentacao(pneu_id, "reciclagem", conn=conn, filial_origem_id=pneu["filial_id"], 
                                observacao=f"Pneu enviado p/ recicladora. Lote: {numero_lote}. {observacao}")
    return True

def listar_lotes_reciclagem(filial_id=None):
    sql = "SELECT * FROM gp_lotes_reciclagem WHERE 1=1"
    params = {}
    if filial_id: sql += " AND filial_id = :fid"; params["fid"] = filial_id
    sql += " ORDER BY data_envio DESC"
    
    with _e().connect() as conn:
        lotes = [dict(r) for r in conn.execute(text(sql), params).mappings().all()]
        for l in lotes:
            p_sql = """SELECT p.*, f.nome as filial_nome, fo.nome as filial_origem_nome 
                             FROM gp_pneus p 
                             LEFT JOIN gp_filiais f ON p.filial_id = f.id
                             LEFT JOIN gp_filiais fo ON p.filial_origem_id = fo.id
                             WHERE p.lote_id = :lid"""
            l['pneus'] = [dict(r) for r in conn.execute(text(p_sql), {'lid': l['id']}).mappings().all()]
        return lotes

def atualizar_valor_lote_reciclagem(lote_id, valor_total):
    with _e().begin() as conn:
        # 1. Contar pneus no lote
        count = conn.execute(text("SELECT COUNT(*) FROM gp_pneus WHERE lote_id=:lid"), {"lid": lote_id}).scalar() or 0
        valor_pneu = (float(valor_total) / count) if count > 0 else 0
        
        # 2. Atualizar o lote
        conn.execute(text("UPDATE gp_lotes_reciclagem SET valor_total=:vt, valor_pneu=:vp, status='pago' WHERE id=:lid"),
                     {"vt": valor_total, "vp": valor_pneu, "lid": lote_id})
    return True

def obter_relatorio_financeiro_reciclagem(mes=None, filial_id=None):
    # mes format: YYYY-MM
    sql = """SELECT l.data_envio, l.numero_lote, l.valor_total, l.valor_pneu,
                    p.id as pneu_id, p.numero_fogo, f.nome as filial_origem_nome, f.id as filial_origem_id
             FROM gp_lotes_reciclagem l
             JOIN gp_pneus p ON l.id = p.lote_id
             JOIN gp_filiais f ON p.filial_origem_id = f.id
             WHERE 1=1"""
    params = {}
    if mes:
        sql += " AND l.data_envio LIKE :m"; params["m"] = f"{mes}%"
    if filial_id:
        sql += " AND f.id = :fid"; params["fid"] = filial_id
        
    sql += " ORDER BY l.data_envio DESC"
    
    with _e().connect() as conn:
        items = [dict(r) for r in conn.execute(text(sql), params).mappings().all()]
        # Resumo por Filial
        resumo = {}
        for it in items:
            fid = it["filial_origem_id"]
            if fid not in resumo:
                resumo[fid] = {"nome": it["filial_origem_nome"], "total": 0, "pneus": 0}
            resumo[fid]["total"] += (it["valor_pneu"] or 0)
            resumo[fid]["pneus"] += 1
            
        return {
            "detalhes": items,
            "resumo_filiais": list(resumo.values()),
            "total_geral": sum((it["valor_pneu"] or 0) for it in items)
        }
