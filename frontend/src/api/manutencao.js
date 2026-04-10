import { cachedFetch, TTL } from './apiCache'

export function fetchManutencaoFiltros()                      { return cachedFetch('/api/manutencao/filtros', {}, { ttl: TTL.FILTROS }) }
export function fetchManutencaoKpis(params = {})              { return cachedFetch('/api/manutencao/kpis', params, { ttl: TTL.DASHBOARD }) }
export function fetchManutencaoEvolucaoMensal(params = {})    { return cachedFetch('/api/manutencao/evolucao-mensal', params, { ttl: TTL.EVOLUCAO }) }
export function fetchManutencaoTopVeiculos(params = {})       { return cachedFetch('/api/manutencao/top-veiculos', params, { ttl: TTL.DASHBOARD }) }
export function fetchManutencaoTopFornecedores(params = {})   { return cachedFetch('/api/manutencao/top-fornecedores', params, { ttl: TTL.DASHBOARD }) }
export function fetchManutencaoPorFilial(params = {})         { return cachedFetch('/api/manutencao/por-filial', params, { ttl: TTL.DASHBOARD }) }
export function fetchManutencaoPorGrupo(params = {})          { return cachedFetch('/api/manutencao/por-grupo', params, { ttl: TTL.DASHBOARD }) }
export function fetchManutencaoKpisEstrategicos(params = {})  { return cachedFetch('/api/manutencao/kpis-estrategicos', params, { ttl: TTL.DASHBOARD }) }
export function fetchManutencaoTendencia(params = {})         { return cachedFetch('/api/manutencao/tendencia', params, { ttl: TTL.EVOLUCAO }) }
export function fetchManutencaoRankingFiliais(params = {})    { return cachedFetch('/api/manutencao/ranking-filiais-estrategico', params, { ttl: TTL.DASHBOARD }) }
