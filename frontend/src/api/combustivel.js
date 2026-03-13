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

export function fetchFiltros() {
  return get('/api/combustivel/filtros')
}

export function fetchKpis(filtros = {}) {
  return get('/api/combustivel/kpis', filtros)
}

export function fetchKpisEstrategicos(filtros = {}) {
  return get('/api/combustivel/kpis-estrategicos', filtros)
}

export function fetchDiario(mes, ano, filtros = {}) {
  return get('/api/combustivel/diario', { mes, ano, ...filtros })
}

export function fetchPorTipo(filtros = {}) {
  return get('/api/combustivel/por-tipo', filtros)
}

export function fetchHistoricoMensal(filtros = {}, porCombustivel = false) {
  return get('/api/combustivel/historico-mensal', { ...filtros, por_combustivel: porCombustivel || undefined })
}

export function fetchTopPostos(limit = 10, filtros = {}) {
  return get('/api/combustivel/top-postos', { limit, ...filtros })
}

export function fetchCustoDiaSemana(filtros = {}) {
  return get('/api/combustivel/custo-dia-semana', filtros)
}

export function fetchResumoPeriodo(params = {}) {
  return get('/api/combustivel/resumo-periodo', params)
}

export function fetchImpactoPreco(params = {}) {
  return get('/api/combustivel/impacto-preco', params)
}

export async function forceRefresh() {
  const res = await fetch(`${BASE}/api/combustivel/cache/refresh`, { method: 'POST' })
  return res.json()
}
