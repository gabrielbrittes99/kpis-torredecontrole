<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Benchmark Estratégico vs ANP</div>
        <div class="card-hint">Visão combinada de volume consumido e preços negociados vs mercado por estado</div>
      </div>
      <div class="resumo-pills" v-if="resumo.combinacoes_analisadas">
        <div class="pill green" v-if="resumo.ufs_abaixo_mercado">
          <span>↓ {{ resumo.ufs_abaixo_mercado }} UF abaixo</span>
        </div>
        <div class="pill red" v-if="resumo.ufs_acima_mercado">
          <span>↑ {{ resumo.ufs_acima_mercado }} UF acima</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="skel" style="height:320px" />

    <template v-else-if="groupedCharts.length">
      <!-- Destaque de economia/sobrecusto (3 CARDS) -->
      <div class="highlight-grid">
        <div class="hl-card green">
          <div class="hl-label">Economia (Saving)</div>
          <div class="hl-value">{{ fmtR(resumo.saving_total_mes) }}</div>
          <div class="hl-sub">Lucro na balança comercial</div>
        </div>
        
        <div class="hl-card red">
          <div class="hl-label">Sobrecusto</div>
          <div class="hl-value">{{ fmtR(resumo.sobrecusto_total_mes) }}</div>
          <div class="hl-sub">Impacto inflacionário vs praça</div>
        </div>

        <div class="hl-card" :class="resumo.balanco_liquido > 0 ? 'red' : 'green'">
          <div class="hl-label">Balanço Líquido</div>
          <div class="hl-value">
            {{ resumo.balanco_liquido > 0 ? '+' : '' }}{{ fmtR(resumo.balanco_liquido) }}
          </div>
          <div class="hl-sub">{{ Math.abs(resumo.balanco_pct || 0).toFixed(1) }}% de margem no volume total</div>
        </div>
      </div>

      <!-- Gráficos por Combustível (Mistos) -->
      <div class="charts-wrap">
        <div v-for="chart in groupedCharts" :key="chart.name" class="fuel-chart-box">
          <div class="fc-header">{{ chart.name }}</div>
          <apexchart type="line" height="340" :options="chart.options" :series="chart.series" />
        </div>
      </div>
    </template>

    <div v-else class="empty">
      <div>Sem dados de benchmark para o período (ANP)</div>
      <div class="empty-sub">Tente selecionar outro período mais consolidado.</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

const props = defineProps({
  data:    { type: Array,  default: () => [] },
  resumo:  { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const groupedCharts = computed(() => {
  if (!props.data || !props.data.length) return []
  
  // Agrupar amostras por combustível
  const groups = {}
  props.data.forEach(row => {
    if (!groups[row.combustivel]) groups[row.combustivel] = []
    groups[row.combustivel].push(row)
  })
  
  // Ordenar nomes dos combustíveis para manter estabilidade
  const sortedNames = Object.keys(groups).sort()
  
  return sortedNames.map(combName => {
    const rows = groups[combName]
    // ORDENAR POR LITRAGEM (Volume) ASC para o Pareto
    rows.sort((a, b) => (b.total_litros || 0) - (a.total_litros || 0))
    
    // Series Mistas
    const series = [
      {
        name: 'Volume Total (L)',
        type: 'column',
        data: rows.map(r => ({ x: r.uf, y: r.total_litros, meta: r }))
      },
      {
        name: 'Média ANP',
        type: 'line',
        data: rows.map(r => ({ x: r.uf, y: r.preco_anp_mercado, meta: r }))
      },
      {
        name: 'Nosso Preço',
        type: 'line',
        data: rows.map(r => ({ x: r.uf, y: r.preco_frota, meta: r }))
      }
    ]
    
    // Obter mínimo e máximo para englobar as duas linhas (Frota e ANP) de forma limpa
    const allPrices = rows.flatMap(r => [r.preco_frota, r.preco_anp_mercado]).filter(v => v != null)
    const minPrice = allPrices.length ? Math.min(...allPrices) * 0.95 : 0
    const maxPrice = allPrices.length ? Math.max(...allPrices) * 1.05 : 10
    
    const options = {
      chart: {
        type: 'line',
        toolbar: { show: false },
        fontFamily: 'Inter, sans-serif',
        animations: { speed: 400 }
      },
      stroke: {
        width: [0, 2, 3], // Coluna não tem borda, ANP=2px, Frota=3px
        curve: 'smooth',
        dashArray: [0, 4, 0] // C1=sólido, ANP=Tracejado, Frota=Sólido
      },
      colors: ['#e2e8f0', '#94a3b8', '#0f172a'],
      markers: {
        size: [0, 0, 4], // Bolinhas só na linha da Frota para destacar
        strokeWidth: 2,
        colors: ['transparent', 'transparent', '#ffffff'],
        strokeColors: '#0f172a',
        hover: { size: 6 }
      },
      plotOptions: {
        bar: {
          columnWidth: '55%',
          borderRadius: 2
        }
      },
      dataLabels: { enabled: false }, // Esconde rótulos para não poluir
      xaxis: {
        categories: rows.map(r => r.uf),
        tooltip: { enabled: false },
        axisBorder: { show: false },
        axisTicks: { show: false },
        labels: { style: { fontWeight: 600, colors: '#64748b' } }
      },
      yaxis: [
        {
          seriesName: 'Volume Total (L)',
          labels: {
            formatter: val => typeof val === 'number' ? val.toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : val,
            style: { colors: '#94a3b8', fontSize: '10px' }
          },
          title: { text: 'Volume (Litros)', style: { color: '#94a3b8', fontWeight: 500, fontSize: '11px' } }
        },
        {
          seriesName: 'Média ANP',
          opposite: true,
          min: minPrice,
          max: maxPrice,
          labels: {
            formatter: val => val != null ? val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—',
            style: { colors: '#0f172a', fontWeight: 700, fontFamily: 'JetBrains Mono, ui-monospace, monospace', fontSize: '11px' }
          },
          title: { text: 'Custo R$/L', style: { color: '#0f172a', fontWeight: 600, fontSize: '11px' } }
        },
        {
          seriesName: 'Média ANP', // Mapeia p/ mesmo eixo Y !
          show: false,
          min: minPrice,
          max: maxPrice
        }
      ],
      grid: {
        borderColor: 'var(--border-subtle, #f1f5f9)',
        strokeDashArray: 3,
        xaxis: { lines: { show: false } },
        yaxis: { lines: { show: true } }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'right',
        markers: { radius: 12 },
        itemMargin: { horizontal: 10, vertical: 0 }
      },
      tooltip: {
        theme: 'light',
        shared: true, // Mostra volume + preços juntos!
        intersect: false,
        custom: function({seriesIndex, dataPointIndex, w}) {
          // Extraímos os metadados do primeiro elemento da série mapeada
          const item = w.globals.initialSeries[0].data[dataPointIndex].meta
          const sign = item.economia_potencial > 0 ? '+' : ''
          const moneyColor = item.economia_potencial > 0 ? '#ef4444' : '#22c55e'
          const badgeText = item.economia_potencial > 0 ? 'SOBRECUSTO' : 'SAVING'
          
          return `
            <div style="padding: 14px; font-family: Inter, sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.06); min-width: 220px;">
              <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 10px;">
                <span style="font-size: 16px; font-weight: 800; color: #0f172a;">${item.uf}</span>
                <span style="font-size: 9px; font-weight: 800; background: ${moneyColor}; color: white; padding: 3px 6px; border-radius: 4px; letter-spacing: 0.05em;">${badgeText}</span>
              </div>
              
              <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px;">
                <span style="color: #64748b; display: flex; align-items: center; gap: 4px;"><div style="width: 8px; height: 8px; background: #cbd5e1; border-radius: 2px;"></div> Volume Operado:</span>
                <span style="font-weight: 700;">${fmtN(item.total_litros)} L</span>
              </div>

              <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px;">
                <span style="color: #64748b; display: flex; align-items: center; gap: 4px;"><div style="width: 8px; height: 2px; background: #94a3b8; border-radius: 1px;"></div> Preço ANP:</span>
                <span style="font-weight: 600;">R$ ${item.preco_anp_mercado?.toFixed(3)}/L</span>
              </div>
              
              <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 12px;">
                <span style="color: #64748b; display: flex; align-items: center; gap: 4px;"><div style="width: 8px; height: 2px; background: #0f172a; border-radius: 1px;"></div> Preço Frota:</span>
                <span style="font-weight: 800; color: #0f172a;">R$ ${item.preco_frota?.toFixed(3)}/L</span>
              </div>
              
              <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; padding-top: 10px; border-top: 1px dashed #cbd5e1; background: #f8fafc; margin: 0 -14px -14px; padding: 12px 14px;">
                <span style="color: #475569;">Impacto R$:</span>
                <span style="color: ${moneyColor}; font-size: 15px;">${sign}${fmtR(item.economia_potencial || 0)}</span>
              </div>
            </div>
          `
        }
      }
    }
    
    return {
      name: combName,
      options,
      series
    }
  })
})

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'
</script>

<style scoped>
.card { background: linear-gradient(var(--surface, white), var(--surface, white)) padding-box, linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box; border: 1px solid transparent; border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 24px; }
.card-title { font-size: 14px; font-weight: 700; color: var(--text); }
.card-hint  { font-size: 12px; color: var(--text-3); margin-top: 2px; line-height: 1.4; }

.resumo-pills { display: flex; gap: 8px; flex-shrink: 0; }
.pill { display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; border: 1px solid; }
.pill.green { background: rgba(34,197,94,.08);  border-color: rgba(34,197,94,.25);  color: var(--green); }
.pill.red   { background: rgba(239,68,68,.08);  border-color: rgba(239,68,68,.25);  color: var(--red); }

/* Grid de Highlights */
.highlight-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 32px;
}
.hl-card {
  display: flex; flex-direction: column; gap: 4px;
  padding: 16px 20px; border-radius: 12px; border: 1px solid var(--border);
  background: var(--surface-hover);
  position: relative; overflow: hidden;
}
.hl-card.green {
  background: rgba(34,197,94,.04);
  border-color: rgba(34,197,94,.15);
}
.hl-card.red {
  background: rgba(239,68,68,.04);
  border-color: rgba(239,68,68,.15);
}
.hl-label { font-size: 11px; font-weight: 700; color: var(--text-3); text-transform: uppercase; letter-spacing: .06em; }
.hl-value { font-size: 24px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; color: var(--text); }
.hl-card.red .hl-label { color: rgba(239,68,68,.9); }
.hl-card.green .hl-label { color: rgba(34,197,94,.9); }
.hl-card.red .hl-value { color: var(--red); }
.hl-card.green .hl-value { color: var(--green); }
.hl-sub { font-size: 11px; color: var(--text-3); font-weight: 500; margin-top: 2px; }

/* Wrapper dos Gráficos */
.charts-wrap {
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.fuel-chart-box {
  background: var(--surface);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 16px 16px 8px;
}
.fc-header {
  font-size: 14px;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 12px;
  margin-left: 8px;
  border-bottom: 2px solid var(--border-strong);
  padding-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.empty { padding: 48px 0; text-align: center; color: var(--text-3); font-size: 13px; }
.empty-sub { font-size: 11px; margin-top: 6px; opacity: .7; }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }

@media (max-width: 768px) {
  .highlight-grid { grid-template-columns: 1fr; }
}
</style>
