import { cachedFetch, TTL } from './apiCache'

export function fetchPrecoPorUF(filtros = {}) {
  return cachedFetch('/api/precos/preco-por-uf', filtros, { ttl: TTL.DASHBOARD })
}

export function fetchRankingPostosPreco(params = {}) {
  return cachedFetch('/api/precos/ranking-postos-preco', params, { ttl: TTL.DASHBOARD })
}
