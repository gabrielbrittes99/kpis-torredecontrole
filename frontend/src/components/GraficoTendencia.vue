<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Custo total mensal</div>
      <div class="card-hint">últimos 12 meses com variação</div>
    </div>
    <div v-if="loading" class="skel" style="height:240px" />
    <apexchart v-else-if="data.length" type="area" height="240" :options="options" :series="series" />
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

const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]} ${y.slice(2)}` }

const series = computed(() => [{
  name: 'Custo R$',
  data: props.data.map(d => d.total_valor),
}])

const options = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', animations: { speed: 700 } },
  theme: { mode: 'dark' },
  colors: ['#C41230'],
  stroke: { curve: 'smooth', width: 2 },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.15, opacityTo: 0.0, stops: [0, 100] } },
  markers: {
    size: props.data.map((_, i) => i === props.data.length - 1 ? 5 : 0),
    colors: ['#C41230'], strokeColors: '#09090b', strokeWidth: 2,
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: props.data.map(d => fmtMes(d.ano_mes)),
    labels: { style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' } },
    axisBorder: { show: false }, axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
      formatter: v => `R$ ${(v/1000).toFixed(0)}k`,
    },
  },
  grid: { borderColor: '#1c1c1f', strokeDashArray: 4, xaxis: { lines: { show: false } } },
  tooltip: {
    theme: 'dark',
    custom: ({ dataPointIndex: i }) => {
      const d = props.data[i]
      const var_pct = d.variacao_pct
      const varColor = var_pct == null ? '#71717a' : var_pct > 0 ? '#ef4444' : '#22c55e'
      const varText = var_pct == null ? '—' : `${var_pct > 0 ? '+' : ''}${var_pct.toFixed(1)}%`
      return `<div style="padding:12px 16px;font-family:'Inter',sans-serif;font-size:12px;min-width:190px">
        <div style="color:#71717a;margin-bottom:8px;font-size:11px">${d.ano_mes}</div>
        <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Total</span>
          <span style="color:#C41230;font-weight:600">R$ ${Number(d.total_valor).toLocaleString('pt-BR',{maximumFractionDigits:0})}</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Litros</span>
          <span style="color:#fafafa">${Number(d.total_litros).toLocaleString('pt-BR',{maximumFractionDigits:0})} L</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Preço/L</span>
          <span style="color:#fafafa">R$ ${d.preco_medio.toFixed(3)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px">
          <span style="color:#a1a1aa">Variação</span>
          <span style="color:${varColor};font-weight:600">${varText}</span>
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
.empty { height: 240px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
