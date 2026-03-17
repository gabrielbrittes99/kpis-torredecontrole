from db_sqlserver import get_sqlserver_conn
import pandas as pd

try:
    conn = get_sqlserver_conn()
    print("Conectado ao SQL Server.")
    
    # Check columns of Movimentos
    query_cols = "SELECT TOP 0 * FROM Movimentos"
    df = pd.read_sql(query_cols, conn)
    print(f"Colunas em Movimentos: {list(df.columns)}")
    
    # Check sample data to see values for filial/status
    query_sample = "SELECT TOP 3 * FROM Movimentos ORDER BY Data DESC"
    df_sample = pd.read_sql(query_sample, conn)
    print("\nAmostra de dados:")
    print(df_sample.to_string())
    
    conn.close()
except Exception as e:
    print(f"Erro: {e}")
