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

function fmtMes(s) {
  var parts = s.split('-')
  var y = parts[0]
  var m = parseInt(parts[1]) - 1
  return MES[m] + ' ' + y.slice(2)
}

const series = computed(function() {
  return [{
    name: 'Custo R$',
    data: props.data.map(function(d) { return d.total_valor }),
  }]
})

function buildTooltip(i) {
  var d = props.data[i]
  var var_pct = d.variacao_pct
  var varColor = var_pct == null ? '#71717a' : (var_pct > 0 ? '#ef4444' : '#22c55e')
  var varText = var_pct == null ? '—' : (var_pct > 0 ? '+' : '') + var_pct.toFixed(1) + '%'
  var parcialTag = d.parcial ? '<span style="background:#f59e0b;color:#000;font-size:9px;padding:2px 6px;border-radius:4px;margin-left:8px;font-weight:700">PARCIAL</span>' : ''
  
  var html = [
    '<div style="padding:12px 16px;font-family:Inter,sans-serif;font-size:12px;min-width:220px">',
    '<div style="color:#71717a;margin-bottom:8px;font-size:11px">' + d.ano_mes + parcialTag + '</div>',
    '<div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">',
    '<span style="color:#a1a1aa">Total</span>',
    '<span style="color:#C41230;font-weight:600">R$ ' + Number(d.total_valor).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) + '</span>',
    '</div>',
    '<div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">',
    '<span style="color:#a1a1aa">Litros</span>',
    '<span style="color:#fafafa">' + Number(d.total_litros).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) + ' L</span>',
    '</div>',
    '<div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">',
    '<span style="color:#a1a1aa">Preco/L</span>',
    '<span style="color:#fafafa">R$ ' + d.preco_medio.toFixed(2) + '</span>',
    '</div>',
    '<div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">',
    '<span style="color:#a1a1aa">Dias c/ dados</span>',
    '<span style="color:#fafafa">' + (d.dias_com_dados || '—') + '</span>',
    '</div>',
    '<div style="display:flex;justify-content:space-between;gap:16px">',
    '<span style="color:#a1a1aa">Variacao</span>',
    '<span style="color:' + varColor + ';font-weight:600">' + varText + '</span>',
    '</div>',
    '</div>'
  ].join('')
  
  return html
}

const options = computed(function() {
  var categories = props.data.map(function(d) {
    var base = fmtMes(d.ano_mes)
    return d.parcial ? base + ' (parcial)' : base
  })
  
  return {
    chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', animations: { speed: 700 } },
    theme: { mode: 'dark' },
    colors: ['#C41230'],
    stroke: { curve: 'smooth', width: 2 },
    fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.15, opacityTo: 0.0, stops: [0, 100] } },
    markers: {
      size: props.data.map(function(d, i) { return i === props.data.length - 1 ? 5 : 0 }),
      colors: ['#C41230'], strokeColors: '#09090b', strokeWidth: 2,
    },
    dataLabels: { enabled: false },
    xaxis: {
      categories: categories,
      labels: { style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' } },
      axisBorder: { show: false }, axisTicks: { show: false },
    },
    yaxis: {
      labels: {
        style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
        formatter: function(v) { return 'R$ ' + (v/1000).toFixed(0) + 'k' },
      },
    },
    grid: { borderColor: '#1c1c1f', strokeDashArray: 4, xaxis: { lines: { show: false } } },
    tooltip: {
      theme: 'dark',
      custom: function(_ref) {
        var dataPointIndex = _ref.dataPointIndex
        return buildTooltip(dataPointIndex)
      },
    },
  }
})
</script>

<style scoped>
.card { background: linear-gradient(var(--surface, white), var(--surface, white)) padding-box, linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box; border: 1px solid transparent; border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { height: 240px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
