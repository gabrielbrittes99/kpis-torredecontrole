import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

def main():
    print("Iniciando migração de SQLite para PostgreSQL DW...")
    
    # 1. Configurar SQLite
    sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gestao_pneus.db")
    if not os.path.exists(sqlite_path):
        print("Arquivo SQLite gestao_pneus.db não encontrado!")
        return
        
    engine_sqlite = create_engine(f"sqlite:///{sqlite_path}")

    # 2. Configurar PostgreSQL
    dw_host = os.getenv("DW_HOST", "192.168.0.37")
    dw_port = os.getenv("DW_PORT", "5433")
    dw_db = os.getenv("DW_DB", "dw")
    dw_user = os.getenv("DW_USER", "gabriel_brittes")
    dw_password = os.getenv("DW_PASSWORD", "OKkK5yGSO6hxAU")
    dw_url = f"postgresql+psycopg2://{dw_user}:{dw_password}@{dw_host}:{dw_port}/{dw_db}?options=-c%20search_path=public"
    engine_pg = create_engine(dw_url)

    # 3. Importar a criacao de tabelas original para garantir schema correto
    try:
        from db_gestao_pneus import ensure_tables
        print("Garantindo esquemas e tabelas no Postgres...")
        ensure_tables()
    except Exception as getattr_err:
        print("Aviso: Falha ao invocar ensure_tables:", getattr_err)

    tabelas = ["gp_filiais", "gp_veiculos", "gp_pneus", "gp_movimentacoes"]

    for tab in tabelas:
        print(f"\nMigrando tabela {tab}...")
        df = pd.read_sql_table(tab, con=engine_sqlite)
        if df.empty:
            print(f"Tabela {tab} vazia. Pulando.")
            continue
            
        print(f"Lidos {len(df)} registros. Inserindo no PostgreSQL...")
        
        # O to_sql com if_exists='append' irá inserir os dados. 
        # Cuidado para não duplicar se rodar duas vezes.
        try:
            df.to_sql(tab, con=engine_pg, if_exists="append", index=False)
            print(f"Registros inseridos na {tab} com sucesso.")
            
            # Atualizar as sequences do Postgres
            with engine_pg.begin() as conn:
                seq_name = f"{tab}_id_seq"
                # Usa func max pra pegar id maximo
                max_id_df = df["id"].max()
                if pd.notna(max_id_df):
                    conn.execute(text(f"SELECT setval('{seq_name}', {int(max_id_df)})"))
                    print(f"Sequence {seq_name} atualizada para {int(max_id_df)}.")
        except Exception as e:
            print(f"Erro ao inserir na tabela {tab}: {e}")

    print("\nMigração concluída com sucesso!")

if __name__ == "__main__":
    main()
