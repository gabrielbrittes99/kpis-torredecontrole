import { GRITSCH_CONFIG } from '../gritsch.config.js'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

async function get(path, params = {}) {
  const url = new URL(`${BASE}${path}`, location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v)
  })
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export function fetchContratosKpis(params = {}) { 
  return get('/api/contratos/kpis', params) 
}

export function fetchContratosHistorico(params = {}) { 
  return get('/api/contratos/historico', params) 
}
