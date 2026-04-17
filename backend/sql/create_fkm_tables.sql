-- ============================================================
-- DDL: Tabelas FKM On-Demand no DW (schema torre)
-- Executar uma vez no banco DW (PostgreSQL interno)
-- ============================================================

-- ------------------------------------------------------------
-- 1. Abastecimentos realizados fora do cartão TruckPag
--    Upload pelos gestores via planilha Excel mensal
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS torre.abastecimentos_diretos (
    id               SERIAL        PRIMARY KEY,
    placa            VARCHAR(10)   NOT NULL,        -- sem hífen, maiúsculo
    ano_mes          CHAR(7)       NOT NULL,        -- "YYYY-MM"
    data_abastec     DATE          NOT NULL,
    litros           NUMERIC(10,3) NOT NULL,
    valor            NUMERIC(10,2) NOT NULL,
    nome_combustivel VARCHAR(50),                   -- "DIESEL S10", "GASOLINA", etc.
    posto            VARCHAR(150),
    cidade           VARCHAR(100),
    uf               CHAR(2),
    motorista        VARCHAR(150),
    observacao       VARCHAR(500),
    filial           VARCHAR(100),                  -- filial do gestor que lançou
    upload_por       VARCHAR(100),                  -- quem fez o upload
    upload_em        TIMESTAMP     DEFAULT NOW(),
    upload_arquivo   VARCHAR(255)                   -- nome do arquivo original
);

CREATE INDEX IF NOT EXISTS idx_abast_diretos_placa_mes
    ON torre.abastecimentos_diretos (placa, ano_mes);

COMMENT ON TABLE torre.abastecimentos_diretos IS
    'Abastecimentos realizados fora do cartão TruckPag (~10% do volume). '
    'Inseridos pelos gestores via upload de planilha Excel mensal. '
    'Compõem o FKM junto com os dados do TruckPag (PostgreSQL Railway).';


-- ------------------------------------------------------------
-- 2. Vínculo Placa → Contrato, validado pelo gestor
--    Toda placa precisa de vínculo para o FKM funcionar
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS torre.veiculo_contrato (
    id           SERIAL       PRIMARY KEY,
    placa        VARCHAR(10)  NOT NULL,        -- sem hífen, maiúsculo
    contrato     VARCHAR(150) NOT NULL,
    filial       VARCHAR(100),
    vigencia_ini DATE         NOT NULL,
    vigencia_fim DATE,                         -- NULL = vigente até hoje
    validado_por VARCHAR(100),
    validado_em  TIMESTAMP    DEFAULT NOW(),
    observacao   VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_veiculo_contrato_placa_vigencia
    ON torre.veiculo_contrato (placa, vigencia_ini, vigencia_fim);

COMMENT ON TABLE torre.veiculo_contrato IS
    'Vincula cada placa ao contrato em que o veículo está operando, '
    'com período de vigência. Validado e mantido pelos gestores. '
    'Fonte autoritativa de "contrato" para o FKM on-demand.';
