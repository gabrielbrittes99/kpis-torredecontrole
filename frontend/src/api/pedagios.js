import { GRITSCH_CONFIG } from '../gritsch.config'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

function buildUrl(path, params = {}) {
  const url = new URL(`${BASE}${path}`, location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') {
      url.searchParams.set(k, v)
    }
  })
  return url
}

export async function fetchPedagiosVisaoGeral(params = {}) {
  const r = await fetch(buildUrl('/api/pedagios/visao-geral', params))
  if (!r.ok) throw new Error('Falha ao buscar visão geral de pedágios')
  return r.json()
}

export async function fetchPedagiosHistoricoMensal(params = {}) {
  const r = await fetch(buildUrl('/api/pedagios/historico-mensal', params))
  if (!r.ok) throw new Error('Falha ao buscar histórico mensal de pedágios')
  return r.json()
}

export async function fetchPedagiosRankingVeiculos(params = {}) {
  const r = await fetch(buildUrl('/api/pedagios/ranking-veiculos', params))
  if (!r.ok) throw new Error('Falha ao buscar ranking de veículos (pedágios)')
  return r.json()
}

export async function fetchPedagiosPorFilial(params = {}) {
  const r = await fetch(buildUrl('/api/pedagios/por-filial', params))
  if (!r.ok) throw new Error('Falha ao buscar pedágios por filial')
  return r.json()
}

export async function fetchPedagiosPorGrupo(params = {}) {
  const r = await fetch(buildUrl('/api/pedagios/por-grupo', params))
  if (!r.ok) throw new Error('Falha ao buscar pedágios por grupo')
  return r.json()
}
