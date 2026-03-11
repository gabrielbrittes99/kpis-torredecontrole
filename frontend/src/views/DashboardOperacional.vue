<template>
  <div class="page">

    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="section-name">Visão Operacional · Diretor de Operações</span>
      </div>
      <div class="topbar-right">
        <span class="meta-badge" :class="kpis.status_meta === 'OK' ? 'ok' : 'acima'">
          Meta R$/km: {{ kpis.meta_custo_km?.toFixed(2) ?? '0.52' }} · {{ kpis.status_meta === 'OK' ? '✓ Dentro' : kpis.status_meta === 'ACIMA' ? '⚠ Acima' : '—' }}
        </span>
      </div>
    </header>

    <div class="page-header">
      <div>
        <h1>Operacional</h1>
        <p class="page-sub">Custo/km diesel · Alertas de frota · Decisão etanol × gasolina</p>
      </div>
    </div>

    <!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ SEÇÃO 1: DIRETOR -->
    <div class="page-body">

      <div class="section-heading">Diretor — 1 olhar · Diesel</div>

      <!-- 4 KPI cards -->
      <div class="kpis-grid" v-if="!lKpis">
        <!-- Custo total diesel -->
        <div class="kpi-card">
          <div class="kpi-label">Custo total diesel</div>
          <div class="kpi-value">{{ fmtR(kpis.total_valor_diesel) }}</div>
          <div class="kpi-sub">{{ fmtN(kpis.total_litros_diesel) }} L · {{ fmtN(kpis.total_km) }} km</div>
        </div>

        <!-- Custo/km diesel -->
        <div class="kpi-card" :class="kpis.status_meta === 'ACIMA' ? 'kpi-red' : kpis.status_meta === 'OK' ? 'kpi-green' : ''">
          <div class="kpi-label">Custo/km diesel</div>
          <div class="kpi-value mono" :class="kpis.status_meta === 'ACIMA' ? 'red' : 'green'">
            {{ kpis.custo_km ? `R$ ${kpis.custo_km.toFixed(4)}` : '—' }}
          </div>
          <div class="kpi-sub" v-if="kpis.pct_vs_meta != null">
            {{ kpis.pct_vs_meta > 0 ? '+' : '' }}{{ kpis.pct_vs_meta.toFixed(1) }}% vs meta R$ {{ kpis.meta_custo_km }}
          </div>
          <div class="kpi-sub" v-else>Sem dados de hodômetro</div>
        </div>

        <!-- km/L diesel -->
        <div class="kpi-card">
          <div class="kpi-label">km/L diesel</div>
          <div class="kpi-value mono">{{ kpis.km_litro?.toFixed(2) ?? '—' }}</div>
          <div class="kpi-sub">{{ kpis.tem_km ? 'calculado via hodômetro' : 'sem hodômetro' }}</div>
        </div>

        <!-- Economia vs ANP -->
        <div class="kpi-card" :class="kpis.economia_anp > 0 ? 'kpi-green' : kpis.economia_anp < 0 ? 'kpi-red' : ''">
          <div class="kpi-label">Economia vs ANP (diesel)</div>
          <div class="kpi-value" :class="kpis.economia_anp > 0 ? 'green' : kpis.economia_anp < 0 ? 'red' : ''">
            {{ kpis.economia_anp != null ? (kpis.economia_anp > 0 ? '+' : '') + fmtR(kpis.economia_anp) : '—' }}
          </div>
          <div class="kpi-sub" v-if="kpis.preco_anp_referencia">
            ANP ref: R$ {{ kpis.preco_anp_referencia?.toFixed(4) }}/L
          </div>
          <div class="kpi-sub" v-else>ANP carregando</div>
        </div>
      </div>
      <div v-else class="kpis-grid">
        <div v-for="i in 4" :key="i" class="kpi-card skel" style="height:90px" />
      </div>

      <!-- Gráfico de barras — custo/km por filial -->
      <GraficoBarrasFilial
        :data="custoPorFilial"
        :familia="familiaFiltro"
        :meta="kpis.meta_custo_km ?? 0.52"
        :loading="lFilial"
        @update:familia="onFamiliaChange"
      />

      <!-- Evolução mensal custo/km -->
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Evolução custo/km — {{ labelFamilia }} · 12 meses</div>
            <div class="card-hint">linha laranja = meta R$ {{ kpis.meta_custo_km?.toFixed(2) ?? '0.52' }}/km</div>
          </div>
        </div>
        <div v-if="lEvolucao" class="skel" style="height:200px" />
        <div v-else-if="!evolucao.length" class="empty">Sem dados mensais</div>
        <apexchart v-else type="line" height="200" :options="optEvolucao" :series="seriesEvolucao" />
      </div>

      <!-- Top veículos para ação -->
      <TabelaVeiculosAcao :data="veiculosAcao" :resumo="resumoAcao" :loading="lAcao" />

      <!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ SEÇÃO 2: ETANOL x GASOLINA -->
      <div class="section-heading">Etanol × Gasolina — decisão inteligente</div>
      <TabelaEtanolGasolina :data="etanolGasolina" :loading="lEtanol" />

    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import GraficoBarrasFilial from '../components/GraficoBarrasFilial.vue'
import TabelaVeiculosAcao  from '../components/TabelaVeiculosAcao.vue'
import TabelaEtanolGasolina from '../components/TabelaEtanolGasolina.vue'
import {
  fetchKpisDiesel, fetchCustoPorFilial, fetchEvolucaoMensal,
  fetchVeiculosAcao, fetchEtanolGasolinaFilial,
} from '../api/operacional.js'

const apexchart = VueApexCharts

const familiaFiltro = ref('diesel')
const FAMILIA_LABELS = { diesel: 'Diesel', gasolina: 'Gasolina', etanol: 'Etanol' }
const labelFamilia = computed(() => FAMILIA_LABELS[familiaFiltro.value] ?? familiaFiltro.value)

const kpis          = ref({})
const custoPorFilial = ref([])
const evolucao      = ref([])
const veiculosAcao  = ref([])
const resumoAcao    = ref({})
const etanolGasolina = ref([])

const lKpis   = ref(true)
const lFilial = ref(true)
const lEvolucao = ref(true)
const lAcao   = ref(true)
const lEtanol = ref(true)

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]} ${y.slice(2)}` }

async function onFamiliaChange(f) {
  familiaFiltro.value = f
  lFilial.value = lEvolucao.value = true
  await Promise.allSettled([
    fetchCustoPorFilial({ familia: f }).then(d => custoPorFilial.value = d).finally(() => lFilial.value = false),
    fetchEvolucaoMensal({ familia: f }).then(d => evolucao.value = d).finally(() => lEvolucao.value = false),
  ])
}

// Gráfico de linha evolução mensal
const seriesEvolucao = computed(() => {
  const comKm = evolucao.value.filter(d => d.custo_km != null)
  return [
    { name: 'Custo/km', data: comKm.map(d => +d.custo_km.toFixed(4)) },
    { name: 'Preço/L',  data: comKm.map(d => +(d.preco_litro ?? 0).toFixed(4)) },
  ]
})
const optEvolucao = computed(() => {
  const comKm = evolucao.value.filter(d => d.custo_km != null)
  const meta = kpis.value.meta_custo_km ?? 0.52
  return {
    chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', animations: { speed: 500 } },
    theme: { mode: 'dark' },
    colors: ['#f97316', '#3b82f6'],
    stroke: { curve: 'smooth', width: [2.5, 1.5] },
    markers: { size: [3, 0], strokeWidth: 0 },
    dataLabels: { enabled: false },
    legend: { show: true, position: 'top', horizontalAlign: 'right', labels: { colors: '#71717a' }, fontSize: '11px', fontFamily: 'Inter, sans-serif' },
    xaxis: {
      categories: comKm.map(d => fmtMes(d.ano_mes)),
      labels: { style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' } },
      axisBorder: { show: false }, axisTicks: { show: false },
    },
    yaxis: {
      labels: { style: { colors: '#52525b', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }, formatter: v => `R$ ${Number(v).toFixed(3)}` },
    },
    annotations: {
      yaxis: [{ y: meta, borderColor: '#f97316', borderWidth: 1, strokeDashArray: 4, label: { text: `Meta R$${meta}/km`, style: { color: '#f97316', background: 'transparent', fontSize: '10px' } } }],
    },
    grid: { borderColor: '#1c1c1f', strokeDashArray: 4, xaxis: { lines: { show: false } } },
    tooltip: { theme: 'dark', shared: true, intersect: false },
  }
})

onMounted(async () => {
  await Promise.allSettled([
    fetchKpisDiesel().then(d => kpis.value = d).finally(() => lKpis.value = false),
    fetchCustoPorFilial({ familia: 'diesel' }).then(d => custoPorFilial.value = d).finally(() => lFilial.value = false),
    fetchEvolucaoMensal({ familia: 'diesel' }).then(d => evolucao.value = d).finally(() => lEvolucao.value = false),
    fetchVeiculosAcao().then(d => { veiculosAcao.value = d.veiculos ?? []; resumoAcao.value = d.resumo ?? {} }).finally(() => lAcao.value = false),
    fetchEtanolGasolinaFilial().then(d => etanolGasolina.value = d).finally(() => lEtanol.value = false),
  ])
})
</script>

<style scoped>
.page { min-height: 100vh; display: flex; flex-direction: column; }

.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 40px; height: 52px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  position: sticky; top: 0; z-index: 10;
}
.topbar-left { display: flex; align-items: center; }
.section-name { font-size: 14px; font-weight: 500; color: var(--text-2); }
.topbar-right { display: flex; align-items: center; }

.meta-badge {
  font-size: 11px; font-family: 'JetBrains Mono', monospace; font-weight: 600;
  padding: 4px 12px; border-radius: 20px; border: 1px solid;
}
.meta-badge.ok    { color: var(--green); background: rgba(34,197,94,.08);  border-color: rgba(34,197,94,.25); }
.meta-badge.acima { color: var(--red);   background: rgba(239,68,68,.08);  border-color: rgba(239,68,68,.25); }

.page-header { display: flex; align-items: center; padding: 32px 40px 0; }
h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.page-sub { font-size: 13px; color: var(--text-3); margin-top: 4px; }

.page-body { padding: 28px 40px 40px; display: flex; flex-direction: column; gap: 24px; flex: 1; }

.section-heading {
  font-size: 12px; font-weight: 600; color: var(--text-3);
  text-transform: uppercase; letter-spacing: .06em;
  display: flex; align-items: center; gap: 12px;
}
.section-heading::after { content:''; flex:1; height:1px; background: var(--border-subtle); }

/* KPIs */
.kpis-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }
.kpi-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px 24px; display: flex; flex-direction: column; gap: 4px;
}
.kpi-red   { border-color: rgba(239,68,68,.3);  background: rgba(239,68,68,.04); }
.kpi-green { border-color: rgba(34,197,94,.3);  background: rgba(34,197,94,.04); }
.kpi-label { font-size: 11px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.kpi-value { font-size: 26px; font-weight: 700; color: var(--text); letter-spacing: -0.02em; line-height: 1.1; }
.kpi-value.mono { font-family: 'JetBrains Mono', monospace; font-size: 22px; }
.kpi-sub { font-size: 12px; color: var(--text-3); }
.red   { color: var(--red); }
.green { color: var(--green); }

/* Card genérico */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); margin-top: 2px; }

.empty { height: 160px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }

.footer { display: flex; padding: 16px 40px; border-top: 1px solid var(--border-subtle); font-size: 12px; color: var(--text-3); }

@media (max-width: 1100px) { .kpis-grid { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 680px) {
  .topbar, .page-header, .page-body, .footer { padding-left: 16px; padding-right: 16px; }
  .kpis-grid { grid-template-columns: 1fr 1fr; }
}
</style>
