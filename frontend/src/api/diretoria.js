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

export function fetchKpisEstrategicos(params = {}) {
  return get('/api/diretoria/kpis-estrategicos', params)
}

export function fetchTendencia12Meses(params = {}) {
  return get('/api/diretoria/tendencia-12-meses', params)
}

export function fetchPotencialEconomia(params = {}) {
  return get('/api/diretoria/potencial-economia', params)
}

export function fetchMixCombustiveis(params = {}) {
  return get('/api/diretoria/mix-combustiveis', params)
}

export function fetchComparativoMeses(params = {}) {
  return get('/api/diretoria/comparativo-meses', params)
}

export function fetchGastosFiliais(params = {}) {
  return get('/api/diretoria/gastos-filiais', params)
}

export function fetchBenchmarkComparativo(params = {}) {
  return get('/api/benchmark/comparativo-frota', params)
}
