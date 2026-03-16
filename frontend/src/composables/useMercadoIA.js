import { ref } from 'vue'
import { GRITSCH_CONFIG } from '../gritsch.config'

export function useMercadoIA() {
  const intel = ref(null)
  const loading = ref(false)
  const erro = ref(null)

  const fetchIntel = async () => {
    loading.value = true
    erro.value = null
    try {
      const resp = await fetch(`${GRITSCH_CONFIG.URLS.BACKEND}/api/torre/dashboard`)
      if (!resp.ok) throw new Error('Falha ao buscar dados de mercado')
      const json = await resp.json()
      const mercado = json.data?.mercado || {}
      const noticias = (mercado.noticias || []).map(n => ({
        titulo: n.titulo,
        fonte: n.fonte || 'Google News',
        impacto: n.impacto || 'neutro',
        analise: '',
        brent_usd: mercado.brent?.valor_usd || null,
        brent_var: mercado.brent?.variacao_pct != null ? `${mercado.brent.variacao_pct > 0 ? '+' : ''}${mercado.brent.variacao_pct.toFixed(2)}%` : null,
        cambio: mercado.cambio?.usd_brl?.valor ? `R$ ${mercado.cambio.usd_brl.valor.toFixed(4)}` : null,
      }))
      intel.value = {
        noticias,
        resumo: mercado.brent?.valor_usd
          ? `Brent: US$ ${mercado.brent.valor_usd.toFixed(2)} | USD/BRL: R$ ${(mercado.cambio?.usd_brl?.valor || 0).toFixed(4)}`
          : 'Dados de mercado indisponíveis no momento.',
        tendencia: (mercado.brent?.variacao_pct || 0) > 0 ? 'alta' : 'estavel',
        timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      }
    } catch (e) {
      erro.value = 'Falha ao consultar mercado'
      console.error('[MercadoIA]', e)
    } finally {
      loading.value = false
    }
  }

  return { intel, loading, erro, fetchIntel }
}
