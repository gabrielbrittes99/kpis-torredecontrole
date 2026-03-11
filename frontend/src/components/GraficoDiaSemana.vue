<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Média por dia · Dia útil vs Fim de semana</div>
        <div class="card-hint">barras = R$/dia · linha = L/dia · últimos 12 meses</div>
      </div>
      <div class="legend">
        <span class="leg-item"><span class="dot bar" />R$/dia</span>
        <span class="leg-item"><span class="dot line" />L/dia</span>
      </div>
    </div>

    <div v-if="loading" class="charts-row">
      <div class="skel" style="height:220px" />
      <div class="skel" style="height:220px" />
    </div>
    <div v-else-if="!data.length" class="empty">Sem dados</div>
    <div v-else class="charts-row">

      <!-- Dia útil -->
      <div class="chart-bloco">
        <div class="bloco-title util">Dia útil <span class="bloco-hint">seg – sex</span></div>
        <apexchart type="bar" height="200" :options="optUtil" :series="seriesUtil" />
      </div>

      <!-- Fim de semana -->
      <div class="chart-bloco">
        <div class="bloco-title fds">Fim de semana <span class="bloco-hint">sáb – dom</span></div>
        <apexchart type="bar" height="200" :options="optFds" :series="seriesFds" />
      </div>

    </div>

    <!-- Linha de ratio FDS/Útil -->
    <template v-if="!loading && data.length">
      <div class="ratio-row">
        <div
          v-for="d in data"
          :key="d.periodo"
          class="ratio-cell"
        >
          <div class="ratio-mes">{{ fmtMesCurto(d.periodo) }}</div>
          <div class="ratio-val" :class="ratioClass(d.ratio_fds_util)">
            {{ d.ratio_fds_util != null ? d.ratio_fds_util.toFixed(2) + '×' : '—' }}
          </div>
          <div class="ratio-label">fds/útil</div>
        </div>
      </div>
      <div class="ratio-hint">
        <span class="dot-sm green" /> &lt; 0.5× normal &nbsp;
        <span class="dot-sm amber" /> 0.5–1.0× aceitável &nbsp;
        <span class="dot-sm red" /> &gt; 1.0× atenção (fds gasta mais por dia)
      </div>
    </template>
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
const fmtMes      = s => { const [y, m] = s.split('-'); return `${MES[+m-1]}/${y.slice(2)}` }
const fmtMesCurto = s => { const [, m] = s.split('-'); return MES[+m-1] }

const cats = computed(() => props.data.map(d => fmtMes(d.periodo)))

// ── Séries ──────────────────────────────────────────────────
const seriesUtil = computed(() => [
  { name: 'R$/dia',  type: 'bar',  data: props.data.map(d => d.media_valor_util)  },
  { name: 'L/dia',   type: 'line', data: props.data.map(d => d.media_litros_util) },
])
const seriesFds = computed(() => [
  { name: 'R$/dia',  type: 'bar',  data: props.data.map(d => d.media_valor_fds)  },
  { name: 'L/dia',   type: 'line', data: props.data.map(d => d.media_litros_fds) },
])

// ── Opções base ──────────────────────────────────────────────
function makeOptions(color, cats) {
  return {
    chart: {
      background: 'transparent', toolbar: { show: false },
      fontFamily: 'Inter, sans-serif', animations: { speed: 400 },
    },
    theme: { mode: 'dark' },
    colors: [color, 'rgba(255,255,255,0.4)'],
    plotOptions: { bar: { columnWidth: '55%', borderRadius: 3 } },
    dataLabels: { enabled: false },
    legend: { show: false },
    stroke: { width: [0, 2], curve: 'smooth' },
    markers: { size: [0, 3], strokeWidth: 0 },
    xaxis: {
      categories: cats,
      labels: { style: { colors: '#52525b', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' } },
      axisBorder: { show: false }, axisTicks: { show: false },
    },
    yaxis: [
      {
        seriesName: 'R$/dia',
        labels: {
          style: { colors: '#52525b', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' },
          formatter: v => `R$${(v / 1000).toFixed(0)}k`,
        },
      },
      {
        seriesName: 'L/dia',
        opposite: true,
        labels: {
          style: { colors: '#52525b', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' },
          formatter: v => `${Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}L`,
        },
      },
    ],
    grid: { borderColor: '#1c1c1f', strokeDashArray: 4, xaxis: { lines: { show: false } } },
    tooltip: {
      theme: 'dark', shared: true, intersect: false,
      y: [
        { formatter: v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—' },
        { formatter: v => v != null ? `${Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} L` : '—' },
      ],
    },
  }
}

const optUtil = computed(() => makeOptions('#3b82f6', cats.value))
const optFds  = computed(() => makeOptions('#f97316', cats.value))

const ratioClass = r => {
  if (r == null) return 'dim'
  if (r > 1.0) return 'red'
  if (r > 0.5) return 'amber'
  return 'green'
}
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint  { font-size: 12px; color: var(--text-3); margin-top: 2px; }

.legend { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }
.leg-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-3); }
.dot { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.dot.bar  { background: #71717a; }
.dot.line { background: rgba(255,255,255,.4); border-radius: 50%; }

/* Dois gráficos lado a lado */
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.chart-bloco { display: flex; flex-direction: column; gap: 8px; }
.bloco-title {
  font-size: 13px; font-weight: 600;
  display: flex; align-items: baseline; gap: 8px;
}
.bloco-title.util { color: #3b82f6; }
.bloco-title.fds  { color: #f97316; }
.bloco-hint { font-size: 11px; font-weight: 400; color: var(--text-3); }

/* Linha de ratio */
.ratio-row {
  display: flex; gap: 4px; margin-top: 20px; overflow-x: auto; padding-bottom: 4px;
}
.ratio-cell {
  flex: 1; min-width: 44px; display: flex; flex-direction: column;
  align-items: center; gap: 2px; padding: 7px 4px; border-radius: 6px;
  background: rgba(255,255,255,.02); border: 1px solid var(--border-subtle);
}
.ratio-mes   { font-size: 10px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; }
.ratio-val   { font-size: 12px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.ratio-val.green { color: var(--green); }
.ratio-val.amber { color: #f59e0b; }
.ratio-val.red   { color: var(--red); }
.ratio-val.dim   { color: var(--text-3); }
.ratio-label { font-size: 9px; color: var(--text-3); }

.ratio-hint { font-size: 11px; color: var(--text-3); margin-top: 10px; display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.dot-sm { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-sm.green { background: var(--green); }
.dot-sm.amber { background: #f59e0b; }
.dot-sm.red   { background: var(--red); }

.empty { height: 200px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel  { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }

@media (max-width: 768px) { .charts-row { grid-template-columns: 1fr; } }
</style>
