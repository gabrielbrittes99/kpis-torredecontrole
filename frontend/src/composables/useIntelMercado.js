import { ref, readonly } from 'vue'
import { GRITSCH_CONFIG } from '../gritsch.config'

export function useIntelMercado() {
  const intel = ref(null)
  const carregando = ref(false)

  async function atualizarIntel() {
    carregando.value = true
    try {
      const mockData = {
        brent: { valor: 82.40, variacao: 1.2, tendencia: 'Alta' },
        cambio: { valor: 4.98, variacao: -0.5 },
        noticias: [
          {
            id: 1,
            titulo: 'Opep+ mantém cortes de produção até final do trimestre',
            fonte: 'Bloomberg',
            impacto: 'Alto',
            analise: 'Pressão constante no diesel doméstico no curto prazo.',
            acao: 'Manter estoque alto nos postos próprios / Antecipar compras'
          },
          {
            id: 2,
            titulo: 'Petrobras anuncia revisão em política de dividendos e investimentos',
            fonte: 'Valor Econômico',
            impacto: 'Médio',
            analise: 'Possível volatilidade nas ações, mas preço diesel estável.',
            acao: 'Monitorar notícias de novos reajustes'
          },
          {
            id: 3,
            titulo: 'Demanda de frete no Sul aumenta 8% com safra de grãos',
            fonte: 'Portal NTC',
            impacto: 'Baixo',
            analise: 'Aumento de volume compensa margens apertadas.',
            acao: 'Revisar rotas preferenciais no PR'
          }
        ],
        tendencia_7_dias: 'Alta',
        ultima_atualizacao: new Date().toISOString()
      }
      await new Promise(r => setTimeout(r, 1200))
      intel.value = mockData
    } catch (e) {
      console.error('[IntelMercado] Error:', e)
    } finally {
      carregando.value = false
    }
  }

  return {
    intel: readonly(intel),
    carregando: readonly(carregando),
    atualizarIntel
  }
}
