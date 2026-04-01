import pymssql
from db_sqlserver import get_sqlserver_conn
import pandas as pd

try:
    conn = get_sqlserver_conn()
    print("Conexão OK!")
    
    # Vamos olhar os 5 primeiros registros da ItensOrdemServico para ver os nomes das colunas
    query = """
    SELECT TOP 5 * 
    FROM ItensOrdemServico 
    WHERE FilialOperacional LIKE '%GRITSCH%' 
      AND (GrupoDespesa LIKE '%PNEU%' OR DescricaoItem LIKE '%PNEU%')
    """
    df = pd.read_sql(query, conn)
    print("\n--- COLUNAS ENCONTRADAS NA TABELA DE MANUTENÇÃO ---")
    print(df.columns.tolist())
    print("\n--- AMOSTRA DE DADOS ---")
    print(df[['Placa', 'OrdemServico', 'DataConclusaoOcorrencia', 'DescricaoItem']].head())
    
    conn.close()
except Exception as e:
    print(f"Erro ao acessar SQL: {e}")
