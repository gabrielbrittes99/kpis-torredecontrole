/*
  FKM — COMBUSTÍVEL TruckPag POR PLACA/MÊS (PARAMETRIZADO)
  Sentinelas substituídos em Python antes de executar:
    {DATE_FROM}  (ex: '2026-04-01') — início do período
    {DATE_TO}    (ex: '2026-05-01') — fim exclusivo do período
*/

WITH resumo_mensal AS (
    SELECT
        TO_CHAR(data_transacao, 'YYYY-MM') AS ano_mes,
        placa,
        -- Primeiro hodômetro VÁLIDO (> 0) do mês
        (ARRAY_AGG(hodometro ORDER BY data_transacao ASC) FILTER (WHERE hodometro > 0))[1] AS odom_primeiro_do_mes,
        MAX(hodometro) AS odom_final_mes,
        SUM(litragem)  AS litros_total,
        SUM(valor)     AS valor_total,
        SUM(valor)  FILTER (WHERE nome_combustivel ILIKE '%DIESEL%')    AS vlr_diesel,
        SUM(valor)  FILTER (WHERE nome_combustivel ILIKE '%ARLA%')      AS vlr_arla,
        SUM(litragem) FILTER (WHERE nome_combustivel ILIKE '%DIESEL%')  AS litros_diesel,
        SUM(litragem) FILTER (WHERE nome_combustivel ILIKE '%ARLA%')    AS litros_arla,
        -- Motorista mais frequente no mês
        MODE() WITHIN GROUP (ORDER BY motorista)            AS motorista_principal,
        -- Combustível predominante no mês
        MODE() WITHIN GROUP (ORDER BY nome_combustivel)     AS nome_combustivel_principal
    FROM public.integration_truckpag_transacoes
    WHERE servico = 'ABASTECIMENTO'
      AND transacao_estornada = '0'
      AND data_transacao >= {DATE_FROM}
      AND data_transacao <  {DATE_TO}
    GROUP BY 1, 2
),
transicao_mes AS (
    SELECT
        *,
        LAG(odom_final_mes) OVER (PARTITION BY placa ORDER BY ano_mes) AS odom_mes_passado
    FROM resumo_mensal
),
ajuste_fkm AS (
    SELECT
        *,
        COALESCE(odom_mes_passado, odom_primeiro_do_mes) AS odom_inicial_calculado
    FROM transicao_mes
)
SELECT
    ano_mes,
    UPPER(REPLACE(placa, '-', ''))                               AS placa,
    odom_inicial_calculado                                       AS odom_inicial,
    odom_final_mes                                               AS odom_final,
    GREATEST(odom_final_mes - odom_inicial_calculado, 0)         AS km_rodado_no_mes,
    COALESCE(litros_total, 0)                                    AS litros_total,
    CASE
        WHEN COALESCE(litros_total, 0) > 0
             AND GREATEST(odom_final_mes - odom_inicial_calculado, 0) > 0
        THEN ROUND(
            GREATEST(odom_final_mes - odom_inicial_calculado, 0)::numeric
            / litros_total, 2
        )
        ELSE 0
    END                                                          AS media_km_l,
    COALESCE(vlr_diesel, 0)                                      AS vlr_diesel,
    COALESCE(vlr_arla, 0)                                        AS vlr_arla,
    COALESCE(litros_diesel, 0)                                   AS litros_diesel,
    COALESCE(litros_arla, 0)                                     AS litros_arla,
    COALESCE(valor_total, 0)                                     AS valor_total,
    motorista_principal,
    nome_combustivel_principal
FROM ajuste_fkm
ORDER BY ano_mes DESC, placa ASC
;
