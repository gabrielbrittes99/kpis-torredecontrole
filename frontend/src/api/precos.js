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

export function fetchEvolucaoPorTipo(filtros = {}) {
  return get('/api/precos/evolucao-por-tipo', filtros)
}

export function fetchPrecoPorUF(filtros = {}) {
  return get('/api/precos/preco-por-uf', filtros)
}

export function fetchRankingPostosPreco(params = {}) {
  return get('/api/precos/ranking-postos-preco', params)
}

export function fetchAnalisePremium(filtros = {}) {
  return get('/api/precos/analise-premium', filtros)
}

export function fetchVariacaoMensal(filtros = {}) {
  return get('/api/precos/variacao-mensal', filtros)
}
