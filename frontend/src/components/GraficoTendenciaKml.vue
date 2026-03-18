<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Tendência de km/L por veículo</div>
      <div class="card-hint">evolução mensal — veículos com hodômetro</div>
    </div>
    <div v-if="loading" class="skel" style="height:280px" />
    <template v-else-if="data.length">
      <!-- Legenda com badges de tendência -->
      <div class="tendencia-badges">
        <span
          v-for="v in veiculosVisiveis"
          :key="v.placa"
          class="badge"
          :class="v.tendencia"
          :title="v.modelo"
        >
          {{ v.placa }}
          <span class="badge-delta">
            {{ v.variacao_pct > 0 ? '+' : '' }}{{ v.variacao_pct }}%
          </span>
        </span>
      </div>
      <apexchart type="line" height="260" :options="options" :series="series" />
    </template>
    <div v-else class="empty">Sem dados com hodômetro suficiente</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
const apexchart = VueApexCharts

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]}/${y.slice(2)}` }

// Cores: queda = vermelho, estavel = azul, melhora = verde
const COR_TENDENCIA = { queda: '#ef4444', estavel: '#64748b', melhora: '#22c55e' }

// Coleta todos os meses únicos (eixo X compartilhado)
const todosOsMeses = computed(() => {
  const set = new Set()
  props.data.forEach(v => v.pontos.forEach(p => set.add(p.mes)))
  return [...set].sort()
})

const veiculosVisiveis = computed(() => props.data.slice(0, 10))

const series = computed(() =>
  veiculosVisiveis.value.map(v => {
    const mapaKml = Object.fromEntries(v.pontos.map(p => [p.mes, p.km_litro]))
    return {
      name: v.placa,
      data: todosOsMeses.value.map(m => mapaKml[m] ?? null),
      color: COR_TENDENCIA[v.tendencia] ?? '#64748b',
    }
  })
)

const options = computed(() => ({
  chart: {
    background: 'transparent',
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif',
    animations: { speed: 400 },
  },
  theme: { mode: 'dark' },
  stroke: { width: 2, curve: 'smooth' },
  markers: { size: 3, hover: { size: 5 } },
  dataLabels: { enabled: false },
  xaxis: {
    categories: todosOsMeses.value.map(fmtMes),
    labels: {
      style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
      formatter: v => v != null ? v.toFixed(1) : '',
    },
    title: {
      text: 'km/L',
      style: { color: '#52525b', fontSize: '11px', fontFamily: 'Inter, sans-serif' },
    },
  },
  grid: { borderColor: '#27272a', strokeDashArray: 4 },
  tooltip: {
    theme: 'dark',
    y: { formatter: v => v != null ? v.toFixed(2) + ' km/L' : '—' },
  },
  legend: { show: false },
}))
</script>

<style scoped>
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
}
.card-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 12px;
}
.card-title { font-size: 13px; font-weight: 600; color: var(--text-2); }
.card-hint  { font-size: 11px; color: var(--text-3); }

.tendencia-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid;
}
.badge.queda   { color: #ef4444; border-color: rgba(239,68,68,.3);  background: rgba(239,68,68,.06); }
.badge.estavel { color: #94a3b8; border-color: rgba(100,116,139,.3); background: rgba(100,116,139,.06); }
.badge.melhora { color: #22c55e; border-color: rgba(34,197,94,.3);  background: rgba(34,197,94,.06); }
.badge-delta { font-size: 10px; opacity: .8; }

.empty { font-size: 12px; color: var(--text-3); text-align: center; padding: 40px 0; }
.skel  { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
