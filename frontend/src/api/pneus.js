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

export function fetchPneusFiltros()                  { return get('/api/pneus/filtros') }
export function fetchPneusKpis(params = {})           { return get('/api/pneus/kpis', params) }
export function fetchPneusTabela(params = {})         { return get('/api/pneus/tabela', params) }
export function fetchPneusPorFilial(params = {})      { return get('/api/pneus/por-filial', params) }
export function fetchPneusPorMarca(params = {})       { return get('/api/pneus/por-marca', params) }
export function fetchPneusPorFornecedor(params = {})  { return get('/api/pneus/por-fornecedor', params) }
export function fetchPneusPorEixo(params = {})        { return get('/api/pneus/por-eixo', params) }
export function fetchPneusPorMedida(params = {})      { return get('/api/pneus/por-medida', params) }
export function fetchPneusPorEstado(params = {})      { return get('/api/pneus/por-estado', params) }
export function fetchPneusPorTipo(params = {})        { return get('/api/pneus/por-tipo', params) }
export function fetchPneusTimeline(params = {})       { return get('/api/pneus/timeline', params) }
export function fetchPneusTopCaros(params = {})       { return get('/api/pneus/top-caros', params) }
export function fetchPneusPorPlaca(params = {})       { return get('/api/pneus/por-placa', params) }
export function fetchPneusTrimestres(params = {})     { return get('/api/pneus/trimestres', params) }
export function fetchAnomaliasPneu(params = {})      { return get('/api/pneus/anomalias', params) }
