<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Evolução mensal — {{ labelMetrica }}</div>
        <div class="card-hint">top 3 combustíveis por volume · série histórica</div>
      </div>
      <div class="toggles">
        <button
          v-for="m in METRICAS"
          :key="m.key"
          class="toggle-btn"
          :class="{ active: metrica === m.key }"
          @click="metrica = m.key"
        >{{ m.label }}</button>
      </div>
    </div>
    <div v-if="loading" class="skel" style="height:200px" />
    <div v-else-if="!hasDados" class="empty">Sem dados históricos</div>
    <apexchart v-else type="line" height="200" :options="options" :series="series" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
const apexchart = VueApexCharts

const props = defineProps({
  data:    { type: Object,  default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const METRICAS = [
  { key: 'preco_medio_litro', label: 'Preço/L' },
  { key: 'total_valor',       label: 'Valor' },
  { key: 'total_litros',      label: 'Litros' },
]
const metrica = ref('preco_medio_litro')
const labelMetrica = computed(() => METRICAS.find(m => m.key === metrica.value)?.label ?? '')

const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]} ${y.slice(2)}` }

const meses = computed(() => props.data?.meses ?? [])
const hasDados = computed(() => meses.value.length > 0 && props.data?.series?.length > 0)

const seriesTop = computed(() => {
  const all = props.data?.series ?? []
  return [...all]
    .sort((a, b) => b.dados.reduce((s,d) => s+(d.total_litros??0),0) - a.dados.reduce((s,d) => s+(d.total_litros??0),0))
    .slice(0, 3)
})

const CORES = ['#f97316', '#3b82f6', '#22c55e']

const series = computed(() => {
  const m = metrica.value
  return seriesTop.value.map((s, i) => ({
    name: s.combustivel,
    color: CORES[i],
    data: meses.value.map(mes => {
      const p = s.dados.find(d => d.ano_mes === mes)
      if (!p) return null
      const v = p[m]
      return v != null ? +Number(v).toFixed(m === 'preco_medio_litro' ? 4 : 0) : null
    }),
  }))
})

const yFmt = computed(() => {
  const m = metrica.value
  if (m === 'preco_medio_litro') return v => v != null ? `R$${Number(v).toFixed(2)}` : ''
  if (m === 'total_valor')       return v => v != null ? `R$${(v/1000).toFixed(0)}k` : ''
  return v => v != null ? `${(v/1000).toFixed(0)}k` : ''
})

const ttFmt = computed(() => {
  const m = metrica.value
  if (m === 'preco_medio_litro') return v => v != null ? `R$ ${Number(v).toFixed(4)}` : '—'
  if (m === 'total_valor')       return v => v != null ? Number(v).toLocaleString('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0}) : '—'
  return v => v != null ? `${Number(v).toLocaleString('pt-BR',{maximumFractionDigits:0})} L` : '—'
})

const options = computed(() => ({
  chart: { background:'transparent', toolbar:{show:false}, fontFamily:'Inter,sans-serif', animations:{speed:400} },
  theme: { mode:'dark' },
  stroke: { curve:'smooth', width:2 },
  markers: { size:3, strokeWidth:0 },
  dataLabels: { enabled:false },
  legend: { show:true, position:'top', horizontalAlign:'right', labels:{colors:'#71717a'}, fontSize:'11px', fontFamily:'Inter,sans-serif', itemMargin:{horizontal:8} },
  xaxis: {
    categories: meses.value.map(fmtMes),
    labels: { style:{colors:'#52525b',fontSize:'11px',fontFamily:'JetBrains Mono,monospace'} },
    axisBorder:{show:false}, axisTicks:{show:false},
  },
  yaxis: { labels:{ style:{colors:'#52525b',fontSize:'11px',fontFamily:'JetBrains Mono,monospace'}, formatter: yFmt.value } },
  grid: { borderColor:'#1c1c1f', strokeDashArray:4, xaxis:{lines:{show:false}} },
  tooltip: {
    theme:'dark', shared:true, intersect:false,
    custom: ({dataPointIndex:i, w}) => {
      const mes = meses.value[i]
      const fmt = ttFmt.value
      const rows = w.config.series.map((s,si) => {
        const v = s.data[i]
        return `<div style="display:flex;justify-content:space-between;gap:20px;margin-bottom:3px">
          <span style="display:flex;align-items:center;gap:6px;color:#a1a1aa">
            <span style="width:8px;height:8px;border-radius:50%;background:${CORES[si]};display:inline-block"></span>${s.name}
          </span>
          <span style="font-weight:600;color:#fafafa">${fmt(v)}</span>
        </div>`
      }).join('')
      return `<div style="padding:12px 16px;font-size:12px;min-width:200px"><div style="color:#71717a;margin-bottom:8px;font-size:11px">${mes}</div>${rows}</div>`
    },
  },
}))
</script>

<style scoped>
.card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:24px; }
.card-header { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:20px; }
.card-title { font-size:14px; font-weight:600; color:var(--text); }
.card-hint { font-size:12px; color:var(--text-3); margin-top:2px; }
.toggles { display:flex; gap:4px; flex-shrink:0; }
.toggle-btn { background:transparent; border:1px solid var(--border); color:var(--text-3); font-size:11px; font-weight:500; padding:4px 10px; border-radius:6px; cursor:pointer; font-family:'Inter',sans-serif; transition:all .15s; white-space:nowrap; }
.toggle-btn:hover { border-color:var(--text-3); color:var(--text-2); }
.toggle-btn.active { border-color:var(--accent); color:var(--accent); background:rgba(249,115,22,.08); }
.empty { height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-3); font-size:13px; }
.skel { background:var(--border); border-radius:8px; animation:pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
