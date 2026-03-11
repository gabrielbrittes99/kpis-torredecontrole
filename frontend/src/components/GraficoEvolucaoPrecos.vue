<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Preço médio por litro</div>
      <div class="card-hint">por tipo de combustível · mensal</div>
    </div>
    <div v-if="loading" class="skel" style="height:240px" />
    <apexchart v-else-if="hasSeries" type="line" height="240" :options="options" :series="series" />
    <div v-else class="empty">Sem dados suficientes</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
const apexchart = VueApexCharts

const props = defineProps({
  data:    { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]} ${y.slice(2)}` }

const CORES = ['#f97316','#3b82f6','#22c55e','#a855f7','#eab308','#06b6d4','#ec4899']

const hasSeries = computed(() => props.data?.series?.length > 0)

const series = computed(() =>
  (props.data?.series || []).map((s, i) => ({
    name: s.combustivel,
    data: s.dados.map(d => d.preco_medio != null ? +d.preco_medio.toFixed(4) : null),
  }))
)

const options = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', animations: { speed: 600 } },
  theme: { mode: 'dark' },
  colors: CORES,
  stroke: { curve: 'smooth', width: 2 },
  dataLabels: { enabled: false },
  markers: { size: 4, strokeColors: '#09090b', strokeWidth: 2 },
  xaxis: {
    categories: (props.data?.meses || []).map(fmtMes),
    labels: { style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' } },
    axisBorder: { show: false }, axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
      formatter: v => v != null ? `R$${v.toFixed(3)}` : '',
    },
  },
  grid: { borderColor: '#1c1c1f', strokeDashArray: 4, xaxis: { lines: { show: false } } },
  legend: {
    show: true,
    position: 'top',
    horizontalAlign: 'right',
    labels: { colors: '#71717a' },
    fontSize: '12px',
    fontFamily: 'Inter, sans-serif',
  },
  tooltip: {
    theme: 'dark',
    y: { formatter: v => v != null ? `R$ ${v.toFixed(4)}` : '—' },
  },
}))
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { height: 240px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
