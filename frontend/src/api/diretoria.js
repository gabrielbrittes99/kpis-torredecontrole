const BASE = import.meta.env.VITE_API_URL

async function get(path, params = {}) {
  const url = new URL(`${BASE}${path}`)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v)
  })
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export function fetchKpisEstrategicos() {
  return get('/api/diretoria/kpis-estrategicos')
}

export function fetchTendencia12Meses() {
  return get('/api/diretoria/tendencia-12-meses')
}

export function fetchPotencialEconomia() {
  return get('/api/diretoria/potencial-economia')
}

export function fetchMixCombustiveis() {
  return get('/api/diretoria/mix-combustiveis')
}

export function fetchComparativoMeses() {
  return get('/api/diretoria/comparativo-meses')
}

// Benchmark ANP
const BASE_BENCH = import.meta.env.VITE_API_URL

async function getBench(path) {
  const res = await fetch(`${BASE_BENCH}${path}`)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json()
}

export function fetchBenchmarkComparativo() {
  return getBench('/api/benchmark/comparativo-frota')
}

export function fetchBenchmarkResumo() {
  return getBench('/api/benchmark/resumo')
}
