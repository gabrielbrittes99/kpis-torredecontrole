<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Preço médio por estado</div>
      <div class="card-hint">R$/L — do mais barato ao mais caro</div>
    </div>
    <div v-if="loading" class="skel" style="height:260px" />
    <apexchart v-else-if="data.length" type="bar" height="260" :options="options" :series="series" />
    <div v-else class="empty">Sem dados</div>
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

const series  = computed(() => [{ name: 'R$/L', data: props.data.map(d => +d.preco_medio.toFixed(4)) }])
const minVal  = computed(() => props.data.length ? Math.min(...props.data.map(d => d.preco_medio)) : 0)

const options = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', animations: { speed: 500 } },
  theme: { mode: 'dark' },
  colors: props.data.map(d =>
    d.preco_medio === minVal.value ? '#22c55e' : '#f97316'
  ),
  plotOptions: { bar: { horizontal: true, borderRadius: 4, distributed: true } },
  dataLabels: {
    enabled: true,
    formatter: v => `R$ ${v.toFixed(3)}`,
    style: { fontSize: '11px', fontFamily: 'JetBrains Mono, monospace', colors: ['#fafafa'] },
    offsetX: 4,
  },
  xaxis: {
    categories: props.data.map(d => d.uf),
    labels: { style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }, formatter: v => `R$${Number(v).toFixed(2)}` },
    axisBorder: { show: false }, axisTicks: { show: false },
  },
  yaxis: { labels: { style: { colors: '#71717a', fontSize: '12px' } } },
  grid: { borderColor: '#1c1c1f', strokeDashArray: 4, xaxis: { lines: { show: false } } },
  legend: { show: false },
  tooltip: {
    theme: 'dark',
    custom: ({ dataPointIndex: i }) => {
      const d = props.data[i]
      return `<div style="padding:10px 14px;font-family:'Inter',sans-serif;font-size:12px">
        <div style="color:#71717a;margin-bottom:6px">${d.uf}</div>
        <div style="display:flex;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Preço/L</span>
          <span style="color:#f97316;font-weight:600">R$ ${d.preco_medio.toFixed(4)}</span>
        </div>
        <div style="display:flex;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Litros</span>
          <span style="color:#fafafa">${Number(d.total_litros).toLocaleString('pt-BR')} L</span>
        </div>
        <div style="display:flex;gap:16px">
          <span style="color:#a1a1aa">Abast.</span>
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
.empty { height: 260px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
