import { ref, readonly } from 'vue'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const cache = new Map()

async function fetchComCache(rota, ttlMs = 10 * 60 * 1000) {
  const agora = Date.now()
  const cached = cache.get(rota)
  if (cached && agora - cached.timestamp < ttlMs) return cached.data

  const resp = await fetch(`${BASE_URL}${rota}`)
  if (!resp.ok) throw new Error(`Erro ${resp.status} em ${rota}`)
  const data = await resp.json()
  cache.set(rota, { data, timestamp: agora })
  return data
}

const TTL = {
  combustivel: 10 * 60 * 1000,
  precos:       4 * 60 * 60 * 1000,
  benchmark:   24 * 60 * 60 * 1000,
  frota:       10 * 60 * 1000,
  projecao:    60 * 60 * 1000,
  alertas:      5 * 60 * 1000,
}

export function useTorreApi() {
  const estado = ref({
    kpis: null,
    alertas: [],
    benchmark: null,
    topPostos: [],
    eficiencia: [],
  })

  const carregando = ref(false)
  const ultimaAtualizacao = ref(null)

  async function carregarTorre() {
    carregando.value = true
    try {
      const [k, a, b, p, f] = await Promise.all([
        fetchComCache('/api/combustivel/kpis', TTL.combustivel),
        fetchComCache('/api/alertas', TTL.alertas),
        fetchComCache('/api/benchmark/resumo', TTL.benchmark),
        fetchComCache('/api/combustivel/top-postos', TTL.precos),
        fetchComCache('/api/frota/eficiencia-km-litro', TTL.frota),
      ])
      
      estado.value.kpis = k
      estado.value.alertas = a
      estado.value.benchmark = b
      estado.value.topPostos = p
      estado.value.eficiencia = f
      ultimaAtualizacao.value = new Date()
    } catch (e) {
      console.error('[Torre] Erro ao carregar dados:', e)
    } finally {
      carregando.value = false
    }
  }

  function getKpisDecisao() {
    if (!estado.value.kpis) return null
    const k = estado.value.kpis
    const b = estado.value.benchmark
    const a = estado.value.alertas

    return {
      percentualOrcamento: k.variacao_pct ?? 0,
      statusOrcamento: k.status === 'ALTA' ? 'critico' : k.status === 'ESTAVEL' ? 'atencao' : 'ok',
      
      veiculosComAlerta: a.filter(al => al.id === 'consumo_anormal' || al.tipo === 'operacional').length,
      
      statusPrecos: (b?.economia_pct ?? 0) < 0 ? 'critico' : 'ok',
      savingMes: b?.economia_potencial_total ?? 0,
      
      saudeOperacao: calcularSaude(k, b, a)
    }
  }

  function calcularSaude(k, b, a) {
    let score = 100
    if (k.status === 'ALTA') score -= 20
    if ((b?.economia_pct ?? 0) < 0) score -= 15
    score -= (a.length * 5)
    return Math.max(score, 0)
  }

  return {
    estado: readonly(estado),
    carregando: readonly(carregando),
    ultimaAtualizacao: readonly(ultimaAtualizacao),
    carregarTorre,
    getKpisDecisao
  }
}
