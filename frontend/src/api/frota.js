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

export function fetchEficienciaKmLitro(params = {}) {
  return get('/api/frota/eficiencia-km-litro', params)
}

export function fetchCustoPorPlaca(params = {}) {
  return get('/api/frota/custo-por-placa', params)
}

export function fetchRankingMotoristas(params = {}) {
  return get('/api/frota/ranking-motoristas', params)
}

export function fetchAbastecimentosSuspeitos(params = {}) {
  return get('/api/frota/abastecimentos-suspeitos', params)
}

export function fetchCustoMensalFrota(params = {}) {
  return get('/api/frota/custo-mensal-frota', params)
}

export function fetchVeiculosPorFilial() {
  return get('/api/veiculos/por-filial')
}

export function fetchResumoFrota() {
  return get('/api/veiculos/resumo')
}
