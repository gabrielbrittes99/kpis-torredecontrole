import { cachedFetch, TTL } from './apiCache'

export function fetchEvolucaoPorTipo(filtros = {}) {
  return cachedFetch('/api/precos/evolucao-por-tipo', filtros, { ttl: TTL.EVOLUCAO })
}

export function fetchPrecoPorUF(filtros = {}) {
  return cachedFetch('/api/precos/preco-por-uf', filtros, { ttl: TTL.DASHBOARD })
}

export function fetchRankingPostosPreco(params = {}) {
  return cachedFetch('/api/precos/ranking-postos-preco', params, { ttl: TTL.DASHBOARD })
}

export function fetchAnalisePremium(filtros = {}) {
  return cachedFetch('/api/precos/analise-premium', filtros, { ttl: TTL.DASHBOARD })
}

export function fetchVariacaoMensal(filtros = {}) {
  return cachedFetch('/api/precos/variacao-mensal', filtros, { ttl: TTL.EVOLUCAO })
}
