import { cachedFetch, TTL } from './apiCache'

export function fetchContratosKpis(params = {}) {
  return cachedFetch('/api/contratos/kpis', params, { ttl: TTL.DASHBOARD })
}
