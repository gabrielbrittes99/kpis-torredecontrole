import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

def run_etl():
    print("Iniciando ETL de Pneus para o DW (torre.controle pneus)...")
    
    # 1. Configurar SQLite (Fonte)
    sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gestao_pneus.db")
    if not os.path.exists(sqlite_path):
        print("Arquivo SQLite gestao_pneus.db não encontrado!")
        return
        
    engine_sqlite = create_engine(f"sqlite:///{sqlite_path}")

    # 2. Configurar PostgreSQL (Destino)
    dw_host = os.getenv("DW_HOST", "192.168.0.37")
    dw_port = os.getenv("DW_PORT", "5433")
    dw_db = os.getenv("DW_DB", "dw")
    dw_user = os.getenv("DW_USER", "gabriel_brittes")
    dw_password = os.getenv("DW_PASSWORD", "OKkK5yGSO6hxAU")
    
    dw_url = f"postgresql+psycopg2://{dw_user}:{dw_password}@{dw_host}:{dw_port}/{dw_db}"
    engine_pg = create_engine(dw_url)

    # 3. Extração e JOIN
    try:
        print("Lendo dados locais...")
        pneus = pd.read_sql("SELECT * FROM gp_pneus", con=engine_sqlite)
        veiculos = pd.read_sql("SELECT id as veiculo_id, placa, frota, modelo as modelo_veiculo, marca as marca_veiculo, tipo as tipo_veiculo FROM gp_veiculos", con=engine_sqlite)
        filiais = pd.read_sql("SELECT id as filial_id, nome as filial_nome FROM gp_filiais", con=engine_sqlite)
        
        # Tabela de lotes PODE estar vazia, lidamos com isso
        try:
            lotes = pd.read_sql("SELECT id as lote_id, numero_lote, data_envio as lote_data_envio, valor_total as lote_valor_total, valor_pneu as lote_valor_pneu FROM gp_lotes_reciclagem", con=engine_sqlite)
        except:
            lotes = pd.DataFrame(columns=["lote_id", "numero_lote", "lote_data_envio", "lote_valor_total", "lote_valor_pneu"])

        if pneus.empty:
            print("Nenhum pneu encontrado localmente para exportar.")
            return

        # 4. Transformação (Flatten)
        print("Transformando dados...")
        
        # Join com veículos
        df = pneus.merge(veiculos, on="veiculo_id", how="left")
        
        # Join com filiais (Localização Atual)
        filiais_atual = filiais.rename(columns={"filial_nome": "unidade_atual"})
        df = df.merge(filiais_atual, on="filial_id", how="left")
        
        # Join com filiais (Origem Operacional)
        filiais_origem = filiais.rename(columns={"filial_id": "filial_origem_id", "filial_nome": "unidade_origem"})
        df = df.merge(filiais_origem, on="filial_origem_id", how="left")
        
        # Join com Lotes de Reciclagem
        df = df.merge(lotes, on="lote_id", how="left")

        # Obter IDs reais do servidor SQL Server e juntar com base na placa
        try:
            from db_sqlserver import get_veiculos_df
            sql_veiculos = get_veiculos_df()
            if not sql_veiculos.empty:
                cols_sql = ["Placa", "IdVeiculo", "IdFilialOperacional", "IdFilial"]
                sql_sub = sql_veiculos[[c for c in cols_sql if c in sql_veiculos.columns]]
                
                df['PlacaLimpa'] = df['placa'].fillna('').astype(str).str.upper().str.strip().str.replace('-', '')
                sql_sub['PlacaLimpa'] = sql_sub['Placa'].fillna('').astype(str).str.upper().str.strip().str.replace('-', '')
                
                df = df.merge(sql_sub.drop(columns=['Placa']), on='PlacaLimpa', how='left')
                df = df.drop(columns=['PlacaLimpa'])
        except Exception as e:
            print(f"Aviso: Não foi possível cruzar com SQL Server: {e}")

        # Limpeza / Renomear colunas para o DW ficar legível
        df = df.rename(columns={
            "id": "pneu_id_gestao",
            "marca": "marca_pneu",
            "modelo": "modelo_pneu"
        })
        
        # Garantir que valores monetários sejam floats (evita erro de tipo no PostgreSQL)
        for col in ['lote_valor_total', 'lote_valor_pneu']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        df["data_atualizacao_etl"] = pd.Timestamp.now()
        
        # 5. Carga (Load)
        schema = "torre"
        table_name = "controle pneus"
        
        print(f"Enviando {len(df)} registros para {dw_host} (esquema {schema})...")
        df.to_sql(table_name, con=engine_pg, schema=schema, if_exists="replace", index=False)
        print("ETL concluído com sucesso!")

    except Exception as e:
        import traceback
        print(f"ERRO FATAL NO ETL: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_etl()
