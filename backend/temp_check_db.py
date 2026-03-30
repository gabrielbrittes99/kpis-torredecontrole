import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def check_db():
    host = os.getenv("DB_HOST", "host.proxy.rlwy.net")
    port = os.getenv("DB_PORT", "12345")
    name = os.getenv("DB_NAME", "railway")
    user = os.getenv("DB_USER", "seu_usuario")
    password = os.getenv("DB_PASSWORD", "sua_senha")
    
    # Tentando carregar as credenciais reais de .env local (que eu não posso ler via tool mas posso usar)
    # Na verdade, a ferramenta uvicorn usa uvicorn main:app, então o setup deve carregar o env
    
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    if not all([db_user, db_pass, db_host, db_port, db_name]):
        print(f"Erro: Faltam credenciais no .env. Encontrados: {db_user}, {db_host}")
        return

    url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(url)
    
    try:
        query = "SELECT DISTINCT tipo_abastecimento FROM integration_truckpag_transacoes"
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn)
            print("Valores únicos em tipo_abastecimento:")
            print(df)
    except Exception as e:
        print(f"Erro ao consultar DB: {e}")

if __name__ == "__main__":
    check_db()
