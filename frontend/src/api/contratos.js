import { cachedFetch, TTL } from './apiCache'

export function fetchContratosKpis(params = {}) {
  return cachedFetch('/api/contratos/kpis', params, { ttl: TTL.DASHBOARD })
}

export function fetchContratosHistorico(params = {}) {
  return cachedFetch('/api/contratos/historico', params, { ttl: TTL.EVOLUCAO })
}
