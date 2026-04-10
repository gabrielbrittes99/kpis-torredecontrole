import { cachedFetch, TTL } from './apiCache'

export function fetchKpisOperacional(params = {})      { return cachedFetch('/api/operacional/kpis', params, { ttl: TTL.DASHBOARD }) }
export function fetchCustoPorGrupo(params = {})        { return cachedFetch('/api/operacional/custo-por-grupo', params, { ttl: TTL.DASHBOARD }) }
export function fetchCustoPorFilial(params = {})       { return cachedFetch('/api/operacional/custo-por-filial', params, { ttl: TTL.DASHBOARD }) }
export function fetchEvolucaoMensal(params = {})       { return cachedFetch('/api/operacional/evolucao-mensal', params, { ttl: TTL.EVOLUCAO }) }
export function fetchVeiculosAcao(params = {})         { return cachedFetch('/api/operacional/veiculos-acao', params, { ttl: TTL.DASHBOARD }) }
