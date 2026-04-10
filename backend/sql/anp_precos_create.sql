-- Tabela para armazenar dados de preços ANP
-- Fonte: CSV semanal da ANP (https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis)

CREATE TABLE IF NOT EXISTS silver.anp_precos (
    id SERIAL PRIMARY KEY,
    uf VARCHAR(2) NOT NULL,
    municipio VARCHAR(100),
    produto VARCHAR(50) NOT NULL,
    preco DECIMAL(8,4) NOT NULL,
    data_coleta DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--Índice para consultas rápidas
CREATE INDEX IF NOT EXISTS idx_anp_precos_uf_produto 
    ON silver.anp_precos (uf, produto, data_coleta);

CREATE INDEX IF NOT EXISTS idx_anp_precos_data_coleta 
    ON silver.anp_precos (data_coleta DESC);