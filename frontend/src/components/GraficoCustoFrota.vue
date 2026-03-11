<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Custo mensal da frota</div>
      <div class="card-hint">total R$ e veículos ativos</div>
    </div>
    <div v-if="loading" class="skel" style="height:220px" />
    <apexchart v-else-if="data.length" type="bar" height="220" :options="options" :series="series" />
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

const series = computed(() => [
  { name: 'Custo R$', data: props.data.map(d => d.total_valor) },
])

const options = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', animations: { speed: 500 } },
  theme: { mode: 'dark' },
  colors: ['#f97316'],
  plotOptions: { bar: { borderRadius: 4, columnWidth: '60%' } },
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
      return `<div style="padding:12px 16px;font-family:'Inter',sans-serif;font-size:12px;min-width:180px">
        <div style="color:#71717a;margin-bottom:8px">${d.ano_mes}</div>
        <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Total</span>
          <span style="color:#f97316;font-weight:600">R$ ${Number(d.total_valor).toLocaleString('pt-BR',{maximumFractionDigits:0})}</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Litros</span>
          <span style="color:#fafafa">${Number(d.total_litros).toLocaleString('pt-BR',{maximumFractionDigits:0})} L</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
          <span style="color:#a1a1aa">Veículos</span>
          <span style="color:#fafafa">${d.qtd_veiculos}</span>
        </div>
        <div style="display:flex;justify-content:space-between;gap:16px">
          <span style="color:#a1a1aa">Custo/veículo</span>
          <span style="color:#fafafa">R$ ${Number(d.custo_medio_por_veiculo).toLocaleString('pt-BR',{maximumFractionDigits:0})}</span>
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
.empty { height: 220px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
