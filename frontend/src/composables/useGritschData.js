import { ref, readonly } from 'vue'
import { GRITSCH_CONFIG } from '../gritsch.config'

const cache = new Map()

async function fetchComCache(rota, ttlMs) {
  const agora = Date.now()
  const cached = cache.get(rota)
  if (cached && agora - cached.timestamp < ttlMs) return cached.data

  try {
    const url = `${GRITSCH_CONFIG.URLS.BACKEND}${rota}`
    console.log(`[GritschAPI] Fetching: ${url}`)
    const resp = await fetch(url)
    if (!resp.ok) return null
    const data = await resp.json()
    cache.set(rota, { data, timestamp: agora })
    return data
  } catch (e) {
    console.error(`[GritschAPI] Error on ${rota}:`, e)
    return null
  }
}

export function useGritschData() {
  const estado = ref({
    combustivel: null,
    precos: [],
    benchmark: {},
    frota: [],
    projecao: {},
  })

  const carregando = ref(false)
  const erro = ref(null)

  async function atualizarTudo() {
    carregando.value = true
    try {
      // Usar Promise.allSettled para garantir que um erro de uma rota não quebre as outras
      const results = await Promise.all([
        fetchComCache('/api/combustivel/kpis', GRITSCH_CONFIG.TTLS.TRANSACOES),
        fetchComCache('/api/combustivel/top-postos', GRITSCH_CONFIG.TTLS.PRECOS),
        fetchComCache('/api/benchmark/resumo', GRITSCH_CONFIG.TTLS.ANP),
        fetchComCache('/api/frota/eficiencia-km-litro', GRITSCH_CONFIG.TTLS.TRANSACOES),
        fetchComCache('/api/combustivel/kpis-estrategicos', GRITSCH_CONFIG.TTLS.PROJECAO),
      ])

      estado.value.combustivel = results[0]
      estado.value.precos = results[1] || []
      estado.value.benchmark = results[2] || {}
      estado.value.frota = results[3] || []
      estado.value.projecao = results[4] || {}
      
      console.log('[GritschData] Dashboard State Updated:', estado.value)
    } catch (e) {
      erro.value = e.message
    } finally {
      carregando.value = false
    }
  }

  function invalidarCache() {
    cache.clear()
  }

  return {
    estado: readonly(estado),
    carregando: readonly(carregando),
    erro: readonly(erro),
    ultimaAtualizacao: readonly(ultimaAtualizacao),
    atualizarTudo,
    invalidarCache
  }
}
