import { GRITSCH_CONFIG } from '../gritsch.config'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

export async function fetchFiliais(mes, ano) {
  const params = new URLSearchParams()
  if (mes) params.set('mes', mes)
  if (ano) params.set('ano', ano)
  const r = await fetch(`${BASE}/api/filiais/resumo?${params}`)
  if (!r.ok) throw new Error('filiais/resumo falhou')
  return r.json()
}
