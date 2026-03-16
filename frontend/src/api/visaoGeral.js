import { GRITSCH_CONFIG } from '../gritsch.config'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

export async function fetchVisaoGeralDashboard({ mes, ano, grupo, combustivel, estado, regiao, filial } = {}) {
  const params = new URLSearchParams()
  if (mes) params.set('mes', mes)
  if (ano) params.set('ano', ano)
  if (grupo) params.set('grupo', grupo)
  if (combustivel) params.set('combustivel', combustivel)
  if (estado) params.set('estado', estado)
  if (regiao) params.set('regiao', regiao)
  if (filial) params.set('filial', filial)
  
  const r = await fetch(`${BASE}/api/visao-geral/dashboard?${params}`)
  if (!r.ok) throw new Error('Falha ao buscar visão geral')
  return r.json()
}

export async function fetchFiltrosDisponiveis() {
  const r = await fetch(`${BASE}/api/visao-geral/filtros-disponiveis`)
  if (!r.ok) throw new Error('Falha ao buscar filtros disponíveis')
  return r.json()
}
