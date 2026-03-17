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

export function fetchKpisOperacional(params = {})      { return get('/api/operacional/kpis', params) }
export function fetchCustoPorGrupo(params = {})        { return get('/api/operacional/custo-por-grupo', params) }
export function fetchCustoPorFilial(params = {})       { return get('/api/operacional/custo-por-filial', params) }
export function fetchEvolucaoMensal(params = {})       { return get('/api/operacional/evolucao-mensal', params) }
export function fetchVeiculosAcao(params = {})         { return get('/api/operacional/veiculos-acao', params) }
export function fetchEtanolGasolinaFilial(params = {}) { return get('/api/operacional/etanol-gasolina-filial', params) }
