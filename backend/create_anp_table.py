"""
Cria a tabela anp_precos no DW sem executar ETL (apenas SQL).
"""
from db_dw import get_dw_engine
from sqlalchemy import text

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS silver.anp_precos (
    id SERIAL PRIMARY KEY,
    uf VARCHAR(2) NOT NULL,
    municipio VARCHAR(100),
    produto VARCHAR(50) NOT NULL,
    preco DECIMAL(8,4) NOT NULL,
    data_coleta DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anp_precos_uf_produto 
    ON silver.anp_precos (uf, produto, data_coleta);

CREATE INDEX IF NOT EXISTS idx_anp_precos_data_coleta 
    ON silver.anp_precos (data_coleta DESC);
"""

def run():
    engine = get_dw_engine()
    with engine.begin() as conn:
        conn.execute(text(_CREATE_TABLE_SQL))
    print("Tabela silver.anp_precos criada com sucesso!")

if __name__ == "__main__":
    run()