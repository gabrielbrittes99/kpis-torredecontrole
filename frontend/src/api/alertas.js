import { cachedFetch, TTL } from './apiCache'

export function fetchAlertas() {
  return cachedFetch('/api/alertas', {}, { ttl: TTL.DASHBOARD })
}
