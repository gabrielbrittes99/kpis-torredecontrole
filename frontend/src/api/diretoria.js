import { cachedFetch, TTL } from './apiCache'

export function fetchKpisEstrategicos(params = {}) {
  return cachedFetch('/api/diretoria/kpis-estrategicos', params, { ttl: TTL.DASHBOARD })
}

export function fetchTendencia12Meses(params = {}) {
  return cachedFetch('/api/diretoria/tendencia-12-meses', params, { ttl: TTL.EVOLUCAO })
}

export function fetchPotencialEconomia(params = {}) {
  return cachedFetch('/api/diretoria/potencial-economia', params, { ttl: TTL.DASHBOARD })
}

export function fetchMixCombustiveis(params = {}) {
  return cachedFetch('/api/diretoria/mix-combustiveis', params, { ttl: TTL.DASHBOARD })
}

export function fetchComparativoMeses(params = {}) {
  return cachedFetch('/api/diretoria/comparativo-meses', params, { ttl: TTL.DASHBOARD })
}

export function fetchGastosFiliais(params = {}) {
  return cachedFetch('/api/diretoria/gastos-filiais', params, { ttl: TTL.DASHBOARD })
}

export function fetchBenchmarkComparativo(params = {}) {
  return cachedFetch('/api/benchmark/comparativo-frota', params, { ttl: TTL.DASHBOARD })
}
