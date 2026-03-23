import { GRITSCH_CONFIG } from '../gritsch.config'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

export async function fetchVisaoGeralDashboard(params = {}) {
  const url = new URL(`${BASE}/api/visao-geral/dashboard`, location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v)
  })
  
  const r = await fetch(url)
  if (!r.ok) throw new Error('Falha ao buscar visão geral')
  return r.json()
}

export async function fetchFiltrosDisponiveis() {
  const r = await fetch(`${BASE}/api/visao-geral/filtros-disponiveis`)
  if (!r.ok) throw new Error('Falha ao buscar filtros disponíveis')
  return r.json()
}

export async function fetchAgressores(params = {}) {
  const url = new URL(`${BASE}/api/visao-geral/agressores`, location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v)
  })
  const r = await fetch(url)
  if (!r.ok) throw new Error('Falha ao buscar agressores')
  return r.json()
}
