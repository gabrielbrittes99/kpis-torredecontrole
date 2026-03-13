import { computed } from 'vue'
import { GRITSCH_CONFIG } from '../gritsch.config'

export function useAlertas(estado) {
  
  const alertas = computed(() => {
    const list = []
    const c = estado.value.combustivel
    const p = estado.value.precos
    const b = estado.value.benchmark
    const f = estado.value.frota
    const proj = estado.value.projecao

    if (!c || !proj) return []

    // 1. Orçamento Crítico
    if (proj.percentual_orcamento > GRITSCH_CONFIG.THRESHOLDS.ORCAMENTO_ESTOURO_PCT) {
      list.push({
        id: 'orcamento_estouro',
        prioridade: 1,
        nivel: 'critico',
        ordem: 0,
        titulo: 'Reduzir Meta Diária de Abastecimento',
        descricao: `Ritmo atual excederá o orçamento. Gasto projetado R$ ${proj.projecao_fechamento?.toLocaleString()}`,
        impacto: `Impacto: R$ -${proj.desvio_reais?.toLocaleString()} até fim do mês`,
        passos: [
          'Acessar plataforma TruckPag > Limites por Veículo',
          'Reduzir limites diários em 15% para a frota administrativa',
          'Notificar gestores sobre a suspensão de rotas não-essenciais',
          'Vigiar novos abastecimentos em tempo real nas próximas 48h'
        ]
      })
    }

    // 2. Veículos com Consumo Anormal
    const veiculosAlerta = f?.filter(v => v.variacao_consumo_pct > GRITSCH_CONFIG.THRESHOLDS.CONSUMO_ANORMAL_PCT) || []
    if (veiculosAlerta.length > 0) {
      list.push({
        id: 'consumo_veiculos',
        prioridade: 2,
        nivel: 'critico',
        ordem: 1,
        titulo: `Inspecionar ${veiculosAlerta.length} Veículos com Alto Consumo`,
        descricao: `Placas: ${veiculosAlerta.slice(0,2).map(v => v.placa).join(', ')}... com consumo > 25% do histórico.`,
        impacto: `Impacto: R$ 4.200/semana em desperdício`,
        passos: [
          'Agendar inspeção mecânica imediata (filtros, pressão, telemetria)',
          'Verificar se o combustível foi drenado fora de operação',
          'Entrevistar motoristas para entender condições de rota',
          'Caso não haja falha mecânica, aplicar reciclagem de condução'
        ]
      })
    }

    // 3. Postos Muito Caros (Benchmark)
    const postosCaros = p?.filter(posto => posto.variacao_pct > GRITSCH_CONFIG.THRESHOLDS.POSTO_CARO_PCT).slice(0, 3) || []
    if (postosCaros.length > 0) {
      list.push({
        id: 'bloqueio_postos',
        prioridade: 3,
        nivel: 'atencao',
        ordem: 2,
        titulo: `Bloquear ${postosCaros.length} Postos Acima da ANP`,
        descricao: `Postos em ${postosCaros.map(p => p.cidade_posto).join(', ')} cobrando spread excessivo.`,
        impacto: `Economia: R$ 3.100/mês se bloqueados`,
        passos: [
          'Identificar CNPJ dos postos na lista de preços',
          'No TruckPag, inserir os CNPJs na "Lista Negra" de postos interditados',
          'Enviar alerta aos motoristas via app sobre a interdição',
          'Sugerir posto parceiro mais próximo (até 10km) com preço justo'
        ]
      })
    }

    // 4. Abastecimentos Fora de Rota
    if (proj.abastecimentos_fora_rota > 0) {
      list.push({
        id: 'fora_rota',
        prioridade: 4,
        nivel: 'atencao',
        ordem: 3,
        titulo: 'Auditar Desvios de Rota Cadastrada',
        descricao: `${proj.abastecimentos_fora_rota} abastecimentos detectados fora do raio operacional.`,
        impacto: 'Investigar possível uso indevido de cartões',
        passos: [
          'Cruzar locais de abastecimento com mapas de rota do BlueFleet',
          'Verificar se o veículo estava em trânsito oficial no horário',
          'Bloquear temporariamente cartões suspeitos para esclarecimento',
          'Recalibrar o raio de tolerância nas geocercas do sistema'
        ]
      })
    }

    return list.sort((a, b) => a.ordem - b.ordem)
  })

  return { alertas }
}
