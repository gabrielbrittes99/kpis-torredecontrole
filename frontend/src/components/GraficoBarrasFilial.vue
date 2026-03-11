<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Custo/km por filial — {{ labelFamilia }}</div>
        <div class="card-hint">vermelho = ação urgente (>10% acima da média)</div>
      </div>
      <div class="toggle-group">
        <button
          v-for="f in FAMILIAS"
          :key="f.key"
          class="toggle-btn"
          :class="{ active: familia === f.key }"
          @click="$emit('update:familia', f.key)"
        >{{ f.label }}</button>
      </div>
    </div>
    <div v-if="loading" class="skel" style="height:320px" />
    <div v-else-if="!data.length" class="empty">Sem dados de filial</div>
    <apexchart v-else type="bar" :height="chartHeight" :options="options" :series="series" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
const apexchart = VueApexCharts

const FAMILIAS = [
  { key: 'diesel',   label: 'Diesel' },
  { key: 'gasolina', label: 'Gasolina' },
  { key: 'etanol',   label: 'Etanol' },
]

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  familia: { type: String,  default: 'diesel' },
  meta:    { type: Number,  default: 0.52 },
  loading: { type: Boolean, default: false },
})
defineEmits(['update:familia'])

const labelFamilia = computed(() => FAMILIAS.find(f => f.key === props.familia)?.label ?? props.familia)
const chartHeight = computed(() => Math.max(260, props.data.length * 52))

const COR_ACAO    = '#ef4444'
const COR_ATENCAO = '#f59e0b'
const COR_OK      = '#22c55e'
const COR_SEM_KM  = '#52525b'

const series = computed(() => [{
  name: 'R$/km',
  data: props.data.map(r => r.custo_km ?? 0),
}])

const options = computed(() => {
  const cores = props.data.map(r =>
    r.flag === 'ACAO'    ? COR_ACAO :
    r.flag === 'ATENCAO' ? COR_ATENCAO :
    r.flag === 'OK'      ? COR_OK : COR_SEM_KM
  )
  const categorias = props.data.map(r => r.filial)
  return {
    chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', animations: { speed: 500 } },
    theme: { mode: 'dark' },
    plotOptions: {
      bar: { horizontal: true, borderRadius: 4, distributed: true, dataLabels: { position: 'right' } },
    },
    colors: cores,
    legend: { show: false },
    dataLabels: {
      enabled: true,
      formatter: v => v ? `R$ ${v.toFixed(3)}` : '—',
      style: { fontSize: '11px', fontFamily: 'JetBrains Mono, monospace', colors: ['#a1a1aa'] },
      offsetX: 6,
    },
    xaxis: {
      categories: categorias,
      labels: { style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }, formatter: v => `R$ ${Number(v).toFixed(3)}` },
      axisBorder: { show: false }, axisTicks: { show: false },
    },
    yaxis: {
      labels: { style: { colors: '#a1a1aa', fontSize: '12px' } },
    },
    grid: { borderColor: '#1c1c1f', strokeDashArray: 4, yaxis: { lines: { show: false } } },
    annotations: {
      xaxis: props.meta ? [{
        x: props.meta,
        borderColor: '#f97316',
        borderWidth: 1.5,
        strokeDashArray: 4,
        label: { text: `Meta R$${props.meta}/km`, style: { color: '#f97316', background: 'transparent', fontSize: '11px' } },
      }] : [],
    },
    tooltip: {
      theme: 'dark',
      custom: ({ dataPointIndex: i }) => {
        const r = props.data[i]
        const flag = r.flag === 'ACAO' ? '<span style="color:#ef4444">🚨 AÇÃO</span>' : r.flag === 'ATENCAO' ? '<span style="color:#f59e0b">⚠ Atenção</span>' : '<span style="color:#22c55e">✓ OK</span>'
        return `<div style="padding:12px 16px;font-family:'Inter',sans-serif;font-size:12px;min-width:200px">
          <div style="font-weight:600;color:#fafafa;margin-bottom:8px">${r.filial} ${flag}</div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px"><span style="color:#a1a1aa">Custo/km</span><span style="color:#fafafa;font-family:monospace">${r.custo_km ? `R$ ${r.custo_km.toFixed(4)}` : '—'}</span></div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px"><span style="color:#a1a1aa">km/L</span><span style="color:#fafafa;font-family:monospace">${r.km_litro ?? '—'}</span></div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px"><span style="color:#a1a1aa">Vs média</span><span style="color:${r.pct_vs_media > 0 ? '#ef4444' : '#22c55e'};font-family:monospace">${r.pct_vs_media != null ? (r.pct_vs_media > 0 ? '+' : '') + r.pct_vs_media.toFixed(1) + '%' : '—'}</span></div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px"><span style="color:#a1a1aa">Veículos</span><span style="color:#fafafa">${r.qtd_veiculos}</span></div>
          <div style="display:flex;justify-content:space-between;gap:16px"><span style="color:#a1a1aa">Total gasto</span><span style="color:#fafafa">${Number(r.total_valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })}</span></div>
        </div>`
      },
    },
  }
})
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); margin-top: 2px; }
.toggle-group { display: flex; gap: 4px; flex-shrink: 0; }
.toggle-btn {
  background: transparent; border: 1px solid var(--border); color: var(--text-3);
  font-size: 11px; font-weight: 500; padding: 4px 10px; border-radius: 6px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all 0.15s;
}
.toggle-btn:hover { border-color: var(--text-3); color: var(--text-2); }
.toggle-btn.active { border-color: var(--accent); color: var(--accent); background: rgba(249,115,22,0.08); }
.empty { height: 180px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
