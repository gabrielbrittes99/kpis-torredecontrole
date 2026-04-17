import { cachedFetch, TTL } from './apiCache'

export function fetchFkmFiltros()                          { return cachedFetch('/api/fkm/filtros', {}, { ttl: TTL.FILTROS }) }
export function fetchFkmKpis(params = {})                  { return cachedFetch('/api/fkm/kpis', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmResumoPorFilial(params = {})        { return cachedFetch('/api/fkm/resumo-por-filial', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmCustoPorVeiculo(params = {})        { return cachedFetch('/api/fkm/custo-por-veiculo', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmEvolucaoMensal(params = {})         { return cachedFetch('/api/fkm/evolucao-mensal', params, { ttl: TTL.EVOLUCAO }) }
export function fetchFkmDistribuicaoCategorias(params = {}) { return cachedFetch('/api/fkm/distribuicao-categorias', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmRankingKmLitro(params = {})         { return cachedFetch('/api/fkm/ranking-km-litro', params, { ttl: TTL.DASHBOARD }) }
export function fetchFkmReconciliacao(params = {})          { return cachedFetch('/api/fkm/reconciliacao', params, { ttl: TTL.DASHBOARD }) }

// Funções para upload de abastecimento direto
export async function uploadFkmFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('filial', 'USER')  // Placeholder — use contexto real se disponível
  formData.append('upload_por', 'GESTOR')

  const response = await fetch('/api/fkm-direto/upload', {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`)
  }

  return response.json()
}

// Funções para rateio (matriz) — stubs por enquanto
export function fetchFkmRateioMatriz(mes) {
  return Promise.resolve({
    ano_mes: mes,
    pendente: 0,
    alocado: 0,
    total: 0,
    itens: []
  })
}

export function salvarRateioMatriz(mes, itens) {
  return Promise.resolve({
    ok: true,
    mes: mes,
    alocados: itens.length
  })
}

export function confirmarFkmUpload(upload_key, ajustes) {
  return Promise.resolve({
    sucesso: true,
    upload_key,
    relatorio_ajustes: [],
    pendencias_sistema: []
  })
}
