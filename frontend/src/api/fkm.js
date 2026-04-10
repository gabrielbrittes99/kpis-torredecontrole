import { cachedFetch, TTL } from './apiCache'

export function fetchFkmFiltros()                          { return cachedFetch('/api/fkm/filtros', {}, { ttl: TTL.FILTROS }) }
export function fetchFkmKpis(params = {})                  { return cachedFetch('/api/fkm/kpis', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmResumoPorFilial(params = {})        { return cachedFetch('/api/fkm/resumo-por-filial', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmCustoPorVeiculo(params = {})        { return cachedFetch('/api/fkm/custo-por-veiculo', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmEvolucaoMensal(params = {})         { return cachedFetch('/api/fkm/evolucao-mensal', params, { ttl: TTL.EVOLUCAO }) }
export function fetchFkmDistribuicaoCategorias(params = {}) { return cachedFetch('/api/fkm/distribuicao-categorias', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmRankingKmLitro(params = {})         { return cachedFetch('/api/fkm/ranking-km-litro', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmReconciliacao(params = {})          { return cachedFetch('/api/fkm/reconciliacao', params, { ttl: TTL.DASHBOARD }) }
