import { cachedFetch, TTL } from './apiCache'

export async function fetchPedagiosVisaoGeral(params = {}) {
  return cachedFetch('/api/pedagios/visao-geral', params, { ttl: TTL.DASHBOARD })
}

export async function fetchPedagiosHistoricoMensal(params = {}) {
  return cachedFetch('/api/pedagios/historico-mensal', params, { ttl: TTL.EVOLUCAO })
}

export async function fetchPedagiosRankingVeiculos(params = {}) {
  return cachedFetch('/api/pedagios/ranking-veiculos', params, { ttl: TTL.DASHBOARD })
}

export async function fetchPedagiosPorFilial(params = {}) {
  return cachedFetch('/api/pedagios/por-filial', params, { ttl: TTL.DASHBOARD })
}

export async function fetchPedagiosPorGrupo(params = {}) {
  return cachedFetch('/api/pedagios/por-grupo', params, { ttl: TTL.DASHBOARD })
}
