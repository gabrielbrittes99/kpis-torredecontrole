<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Mix de combustíveis</div>
      <div class="card-hint">por valor total gasto</div>
    </div>
    <div v-if="loading" class="skel" style="height:260px" />
    <template v-else-if="data.length">
      <apexchart type="donut" height="200" :options="options" :series="series" />
      <div class="legend">
        <div v-for="(item, i) in data" :key="item.combustivel" class="legend-row">
          <span class="dot" :style="{ background: palette[i % palette.length] }" />
          <span class="legend-name">{{ item.combustivel }}</span>
          <span class="legend-pct mono">{{ item.pct_valor }}%</span>
          <span class="legend-val mono">{{ fmtR(item.total_valor) }}</span>
        </div>
      </div>
    </template>
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

const palette = ['#C41230','#3b82f6','#22c55e','#a855f7','#eab308','#06b6d4','#ec4899','#84cc16','#f43f5e']

const series  = computed(() => props.data.map(d => d.total_valor))
const options = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'dark' },
  colors: palette,
  labels: props.data.map(d => d.combustivel),
  legend: { show: false },
  dataLabels: { enabled: false },
  stroke: { width: 2, colors: ['#09090b'] },
  plotOptions: { pie: { donut: { size: '68%', labels: {
    show: true,
    total: {
      show: true, label: 'Total',
      fontSize: '11px', color: '#71717a', fontFamily: 'JetBrains Mono, monospace',
      formatter: w => {
        const t = w.globals.seriesTotals.reduce((a, b) => a + b, 0)
        return `R$ ${(t/1000).toFixed(0)}k`
      }
    },
    value: { fontSize: '18px', fontWeight: 700, color: '#fafafa', fontFamily: 'Inter, sans-serif', offsetY: 4 }
  }}}},
  tooltip: { theme: 'dark', y: { formatter: v => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) } },
}))

const fmtR = v => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { height: 260px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }

.legend { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.legend-row { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.legend-name { flex: 1; color: var(--text-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.legend-pct { color: var(--text-3); font-size: 11px; }
.legend-val { color: var(--text); font-size: 11px; }
.mono { font-family: 'JetBrains Mono', monospace; }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
