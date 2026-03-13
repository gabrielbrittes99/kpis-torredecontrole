import { ref } from 'vue'

export function useMercadoIA() {
  const intel = ref(null)
  const loading = ref(false)
  const erro = ref(null)

  const fetchIntel = async () => {
    loading.value = true
    erro.value = null
    
    // Simulação da chamada Claude API v2.0 solicitada no prompt
    try {
      await new Promise(r => setTimeout(r, 1800)) // Fake latency
      
      const mockResult = {
        "noticias": [
          {
            "titulo": "Brent opera em alta com tensões no Oriente Médio",
            "fonte": "Reuters",
            "impacto": "alto",
            "analise": "O aumento no barril pressiona a Petrobras a reajustar o diesel nas refinarias na próxima quinzena.",
            "acao": "Priorizar abastecimento em postos com estoque antigo e preço travado.",
            "brent_usd": 84.12,
            "brent_var": "+1.2%",
            "cambio": "R$ 5,14"
          },
          {
            "titulo": "Petrobras avalia nova política de dividendos e preços",
            "fonte": "Bloomberg",
            "impacto": "medio",
            "analise": "Possível manutenção de preços abaixo da paridade internacional para conter inflação.",
            "acao": "Manter estratégia de compra spot conforme necessidade imediata.",
            "brent_usd": null,
            "brent_var": null,
            "cambio": null
          },
          {
            "titulo": "Demanda por diesel cresce 4% no agro (MT/PR)",
            "fonte": "ANP",
            "impacto": "baixo",
            "analise": "Safra recorde aumenta volume, mas pulveriza a oferta em postos de rodovia.",
            "acao": "Reforçar contratos de volume fixo nas rotas do escoamento da safra.",
            "brent_usd": null,
            "brent_var": null,
            "cambio": null
          }
        ],
        "resumo": "Mercado pressionado por custos internacionais, tendência de estabilidade interna.",
        "tendencia": "estavel",
        "dias": 7,
        "timestamp": new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
      }
      
      intel.value = mockResult
    } catch (e) {
      erro.value = "Falha ao consultar IA de mercado"
    } finally {
      loading.value = false
    }
  }

  return { intel, loading, erro, fetchIntel }
}
