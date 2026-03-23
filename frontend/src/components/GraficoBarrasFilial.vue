<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Custo/KM por Filial · {{ labelFamilia }}</div>
        <div class="card-hint">Ordenado do maior para o menor custo/km · apenas filiais com hodômetro registrado</div>
      </div>
    </div>

    <div v-if="loading" class="skel" style="height:320px" />
    <div v-else-if="!dataComKm.length" class="empty">Sem dados de custo/km por filial para este filtro</div>
    <apexchart v-else type="bar" :height="chartHeight" :options="options" :series="series" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
const apexchart = VueApexCharts

const FAMILIAS = [
  { key: 'todos',    label: 'Geral' },
  { key: 'diesel',   label: 'Diesel' },
  { key: 'gasolina', label: 'Gasolina' },
  { key: 'etanol',   label: 'Etanol' },
]

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  familia: { type: String,  default: 'todos' },
  loading: { type: Boolean, default: false },
})

const labelFamilia = computed(() => FAMILIAS.find(f => f.key === props.familia)?.label ?? props.familia)

// Só mostra filiais com custo/km calculado
const dataComKm = computed(() => props.data.filter(r => r.custo_km != null))

const chartHeight = computed(() => Math.max(240, dataComKm.value.length * 46))

// Gradiente de cor: menor custo = verde, maior = laranja
function interpolateColor(idx, total) {
  if (total <= 1) return '#10b981'
  const t = idx / (total - 1) // 0 = menor (verde), 1 = maior (laranja/vermelho)
  // Verde #10b981 → Laranja #C41230
  const r = Math.round(16  + t * (249 - 16))
  const g = Math.round(185 + t * (115 - 185))
  const b = Math.round(129 + t * (22  - 129))
  return `rgb(${r},${g},${b})`
}

const series = computed(() => [{
  name: 'R$/km',
  data: [...dataComKm.value].reverse().map(r => +r.custo_km.toFixed(4)),
}])

const options = computed(() => {
  const reversed = [...dataComKm.value].reverse()
  const n = reversed.length
  const cores = reversed.map((_, i) => interpolateColor(i, n))

  return {
    chart: {
      background: 'transparent',
      toolbar: { show: false },
      fontFamily: 'Inter, sans-serif',
    },
    theme: { mode: 'light' },
    plotOptions: {
      bar: {
        horizontal: true,
        borderRadius: 4,
        distributed: true,
        dataLabels: { position: 'right' },
        barHeight: '68%',
      },
    },
    colors: cores,
    legend: { show: false },
    dataLabels: {
      enabled: true,
      formatter: v => `R$ ${Number(v).toFixed(4)}`,
      style: {
        fontSize: '11px',
        fontFamily: 'JetBrains Mono, monospace',
        colors: ['#475569'],
      },
      offsetX: 6,
    },
    xaxis: {
      categories: reversed.map(r => r.filial.replace('Gritsch ', '')),
      labels: {
        style: { colors: '#94a3b8', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
        formatter: v => `R$ ${Number(v).toFixed(2)}`,
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      labels: { style: { colors: '#334155', fontSize: '12px', fontWeight: 600 } },
    },
    grid: {
      borderColor: '#f1f5f9',
      strokeDashArray: 4,
      yaxis: { lines: { show: false } },
    },
    tooltip: {
      theme: 'light',
      custom: ({ dataPointIndex: i }) => {
        const r = [...dataComKm.value].reverse()[i]
        const nome = r.filial
        const composicaoHtml = r.composicao_grupos?.length
          ? `<div style="border-top:1px solid #f1f5f9;margin-top:8px;padding-top:8px">
               <div style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px">Composição da frota</div>
               ${r.composicao_grupos.slice(0, 4).map(c => {
                 const grp = c.grupo.replace('Caminhão', 'Cam.').replace('Ton', 'T')
                 const ck = c.custo_km ? `R$ ${c.custo_km.toFixed(3)}/km` : '—'
                 return `<div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:3px">
                   <span style="color:#64748b">${grp} · ${c.qtd_veiculos}v · ${c.pct_valor}%</span>
                   <span style="color:#0f172a;font-family:monospace;font-size:11px;font-weight:600">${ck}</span>
                 </div>`
               }).join('')}
             </div>`
          : ''
        return `<div style="padding:12px 16px;font-family:'Inter',sans-serif;font-size:12px;min-width:260px">
          <div style="font-weight:700;color:#0f172a;margin-bottom:10px;border-bottom:1px solid #f1f5f9;padding-bottom:8px">${nome}</div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
            <span style="color:#64748b">Custo/km</span>
            <span style="color:#0f172a;font-weight:700;font-family:monospace">R$ ${r.custo_km.toFixed(4)}</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
            <span style="color:#64748b">km/L</span>
            <span style="color:#0f172a;font-weight:700;font-family:monospace">${r.km_litro?.toFixed(2) ?? '—'}</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
            <span style="color:#64748b">Gasto total</span>
            <span style="color:#0f172a;font-weight:700">${Number(r.total_valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })}</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px">
            <span style="color:#64748b">KM rodados</span>
            <span style="color:#0f172a;font-weight:700;font-family:monospace">${r.total_km ? Number(r.total_km).toLocaleString('pt-BR') + ' km' : '—'}</span>
          </div>
          <div style="display:flex;justify-content:space-between;gap:16px">
            <span style="color:#64748b">Veículos</span>
            <span style="color:#0f172a;font-weight:700;font-family:monospace">${r.qtd_veiculos}</span>
          </div>
          ${composicaoHtml}
        </div>`
      },
    },
  }
})
</script>

<style scoped>
.card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 24px; }
.card-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.card-hint { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.empty { height: 180px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 13px; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.8} }
</style>
