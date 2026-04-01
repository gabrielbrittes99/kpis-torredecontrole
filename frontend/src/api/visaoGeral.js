import { cachedFetch, TTL } from './apiCache'

export async function fetchVisaoGeralDashboard(params = {}) {
  return cachedFetch('/api/visao-geral/dashboard', params, { ttl: TTL.DASHBOARD })
}

export async function fetchFiltrosDisponiveis() {
  return cachedFetch('/api/visao-geral/filtros-disponiveis', {}, { ttl: TTL.FILTROS })
}

export async function fetchAgressores(params = {}) {
  return cachedFetch('/api/visao-geral/agressores', params, { ttl: TTL.DASHBOARD })
}
