<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Gasto diário</div>
      <div class="card-hint">R$ por dia no mês</div>
    </div>
    <div v-if="loading" class="skel" style="height:200px" />
    <apexchart v-else type="bar" height="200" :options="options" :series="series" />
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

const maxIdx = computed(() => {
  if (!props.data.length) return -1
  return props.data.reduce((mi, d, i, a) => d.total_valor > a[mi].total_valor ? i : mi, 0)
})

const series  = computed(() => [{ name: 'R$', data: props.data.map(d => +d.total_valor.toFixed(2)) }])
const options = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', sparkline: { enabled: false } },
  theme: { mode: 'dark' },
  plotOptions: { bar: { borderRadius: 3, columnWidth: '65%', distributed: true } },
  colors: props.data.map((_, i) => i === maxIdx.value ? '#f97316' : '#27272a'),
  legend: { show: false },
  dataLabels: { enabled: false },
  xaxis: {
    categories: props.data.map(d => d.dia.slice(8)),
    labels: { style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' } },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: { labels: { style: { colors: '#52525b', fontSize: '11px' }, formatter: v => `${(v/1000).toFixed(0)}k` } },
  grid: { borderColor: '#1c1c1f', strokeDashArray: 0, xaxis: { lines: { show: false } } },
  states: { hover: { filter: { type: 'lighten', value: 0.1 } } },
  tooltip: {
    theme: 'dark',
    custom: ({ dataPointIndex: i }) => {
      const d = props.data[i]
      return `<div style="padding:12px 16px;font-family:'Inter',sans-serif;font-size:12px;min-width:160px">
        <div style="color:#71717a;margin-bottom:8px;font-size:11px">${d.dia}</div>
        <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Valor</span>
          <span style="color:#fafafa;font-weight:600">R$ ${d.total_valor.toLocaleString('pt-BR',{minimumFractionDigits:2})}</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Litros</span>
          <span style="color:#fafafa">${d.total_litros.toLocaleString('pt-BR',{minimumFractionDigits:0})} L</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px">
          <span style="color:#a1a1aa">Abastec.</span>
          <span style="color:#fafafa">${d.qtd_abastecimentos}</span>
        </div>
      </div>`
    },
  },
}))
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
