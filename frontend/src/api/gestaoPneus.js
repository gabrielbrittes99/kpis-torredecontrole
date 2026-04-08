const BASE = import.meta.env.VITE_API_URL

async function get(path, params = {}) {
  const url = new URL(`${BASE}${path}`, location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v)
  })
  const res = await fetch(url)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

async function post(path, body = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

async function put(path, body = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

async function del(path) {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

const P = '/api/gestao-pneus'

// Configs
export const fetchVehicleConfigs = () => get(`${P}/configs/veiculos`)

// Filiais
export const fetchFiliais = () => get(`${P}/filiais`)
export const createFilial = (data) => post(`${P}/filiais`, data)
export const updateFilial = (id, data) => put(`${P}/filiais/${id}`, data)
export const deleteFilial = (id) => del(`${P}/filiais/${id}`)

// Veículos
export const fetchVeiculos = (params = {}) => get(`${P}/veiculos`, params)
export const fetchVeiculo = (id) => get(`${P}/veiculos/${id}`)
export const createVeiculo = (data) => post(`${P}/veiculos`, data)
export const updateVeiculo = (id, data) => put(`${P}/veiculos/${id}`, data)
export const deleteVeiculo = (id) => del(`${P}/veiculos/${id}`)

// Pneus
export const fetchPneusList = (params = {}) => get(`${P}/pneus`, params)
export const fetchPneuDetail = (id) => get(`${P}/pneus/${id}`)
export const createPneu = (data) => post(`${P}/pneus`, data)
export const updatePneu = (id, data) => put(`${P}/pneus/${id}`, data)

// Operações
export const alocarPneu = (data) => post(`${P}/alocar`, data)
export const removerPneu = (data) => post(`${P}/remover`, data)
export const transferirPneu = (data) => post(`${P}/transferir`, data)
export const confirmarRecebimento = (pneuId) => post(`${P}/confirmar-recebimento`, { pneu_id: pneuId })
export const rodizioPneu = (data) => post(`${P}/rodizio`, data)

// Movimentações
export const fetchMovimentacoes = (params = {}) => get(`${P}/movimentacoes`, params)

// Dashboard
export const fetchGPDashboard = () => get(`${P}/dashboard`)

// Sincronização SQL Server
export const sincronizarSqlServer = () => post(`${P}/sincronizar`)
export const fetchBuscaVeiculoSql = (placa) => get(`${P}/busca-veiculo-sql/${placa}`)

// Planilha Pneus Online
export const fetchPlanilhaPneus = () => get(`${P}/planilha-pneus`)

// Reciclagem e Financeiro
export const fetchLotesReciclagem = (params = {}) => get(`${P}/reciclagem/lotes`, params)
export const enviarParaReciclagem = (data) => post(`${P}/reciclagem/enviar`, data)
export const atualizarValorLote = (data) => post(`${P}/reciclagem/atualizar-valor`, data)
export const fetchRelatorioFinanceiroReciclagem = (params = {}) => get(`${P}/reciclagem/relatorio-financeiro`, params)

