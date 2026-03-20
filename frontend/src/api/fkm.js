const BASE = import.meta.env.VITE_API_URL

async function get(path, params = {}) {
  const url = new URL(`${BASE}${path}`, location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v)
  })
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export function fetchFkmFiltros()                          { return get('/api/fkm/filtros') }
export function fetchFkmKpis(params = {})                  { return get('/api/fkm/kpis', params) }
export function fetchFkmResumoPorFilial(params = {})        { return get('/api/fkm/resumo-por-filial', params) }
export function fetchFkmCustoPorVeiculo(params = {})        { return get('/api/fkm/custo-por-veiculo', params) }
export function fetchFkmEvolucaoMensal(params = {})         { return get('/api/fkm/evolucao-mensal', params) }
export function fetchFkmDistribuicaoCategorias(params = {}) { return get('/api/fkm/distribuicao-categorias', params) }
export function fetchFkmRankingKmLitro(params = {})         { return get('/api/fkm/ranking-km-litro', params) }
