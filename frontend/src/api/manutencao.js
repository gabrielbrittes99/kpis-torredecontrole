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

export function fetchManutencaoFiltros()                      { return get('/api/manutencao/filtros') }
export function fetchManutencaoKpis(params = {})              { return get('/api/manutencao/kpis', params) }
export function fetchManutencaoEvolucaoMensal(params = {})    { return get('/api/manutencao/evolucao-mensal', params) }
export function fetchManutencaoTopVeiculos(params = {})       { return get('/api/manutencao/top-veiculos', params) }
export function fetchManutencaoTopFornecedores(params = {})   { return get('/api/manutencao/top-fornecedores', params) }
export function fetchManutencaoPorFilial(params = {})         { return get('/api/manutencao/por-filial', params) }
export function fetchManutencaoPorGrupo(params = {})          { return get('/api/manutencao/por-grupo', params) }
export function fetchManutencaoKpisEstrategicos(params = {})  { return get('/api/manutencao/kpis-estrategicos', params) }
export function fetchManutencaoTendencia(params = {})         { return get('/api/manutencao/tendencia', params) }
export function fetchManutencaoRankingFiliais(params = {})    { return get('/api/manutencao/ranking-filiais-estrategico', params) }
