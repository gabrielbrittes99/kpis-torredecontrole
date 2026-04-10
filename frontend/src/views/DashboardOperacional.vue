<template>
  <div class="page">
    <GlobalTopbar
      title="Gestão de Frota"
      subtitle="Acompanhamento operacional — eficiência, alertas e análise de postos"
    />

    <div class="page-body">

      <!-- ━━━━━ SELETOR DE FAMÍLIA ━━━━━ -->
      <div class="fuel-selector-bar">
        <button
          v-for="f in FAMILIAS_LIST"
          :key="f.key"
          class="fuel-tab"
          :class="{ active: familiaFiltro === f.key }"
          @click="familiaFiltro = f.key; loadAll()"
        >
          {{ f.label }}
        </button>
      </div>

      <!-- ━━━━━ HERO OPERACIONAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Resumo Operacional · {{ labelFamilia }}</div>
        <div class="kpi-pro-grid" v-if="!lAcao">
          <KpiCardPro
            title="Veículos em Alerta"
            :value="resumoAcao.total_acao ?? 0"
            format="number"
            theme="primary"
            :description="(resumoAcao.total_frota ?? 0) + ' veículos monitorados no total'"
          />
          <KpiCardPro
            title="Economia Possível"
            :value="resumoAcao.economia_total_possivel ?? 0"
            format="currency"
            :decimals="0"
            description="Potencial de redução de custo identificado"
          />
          <KpiCardPro
            title="Grupos Monitorados"
            :value="resumoAcao.grupos_monitorados ?? 0"
            format="number"
            description="Grupos de veículos com dados de hodômetro"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 3" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO: EVOLUÇÃO MENSAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Evolução Mensal · {{ labelFamilia }}</div>
        <div class="two-col">

          <!-- Custo/km -->
          <div class="chart-panel">
            <div class="chart-panel-header">
              <span class="chart-panel-title">Custo/km</span>
              <span class="chart-panel-unit">R$ por km rodado</span>
            </div>
            <div v-if="lEvolucao" class="skel" style="height:200px" />
            <div v-else-if="!evolucao.length" class="empty">Sem dados</div>
            <apexchart v-else type="area" height="200" :options="evolCustoOpts" :series="evolCustoSeries" />
          </div>

          <!-- km/L -->
          <div class="chart-panel">
            <div class="chart-panel-header">
              <span class="chart-panel-title">km/L médio</span>
              <span class="chart-panel-unit">Eficiência da frota</span>
            </div>
            <div v-if="lEvolucao" class="skel" style="height:200px" />
            <div v-else-if="!temKm" class="empty">Sem dados de hodômetro para este período</div>
            <apexchart v-else type="area" height="200" :options="evolKmlOpts" :series="evolKmlSeries" />
          </div>

        </div>
      </section>

      <!-- ━━━━━ SEÇÃO: VEÍCULOS SOB ALERTA ━━━━━ -->
      <section id="secao-acao" class="v-block">
        <div class="section-title-row">
          <div class="section-heading" style="flex:1;margin:0">Veículos sob Alerta · Comparação por Grupo</div>
          <div class="comb-tabs">
            <button :class="{ active: filtroAcao === null }" :style="pillStyle(null, filtroAcao)" @click="setFiltroAcao(null)">Todos</button>
            <button v-for="c in COMBUSTIVEIS" :key="c" :class="{ active: filtroAcao === c }" :style="pillStyle(c, filtroAcao)" @click="setFiltroAcao(c)">{{ c }}</button>
          </div>
        </div>
        <TabelaVeiculosAcao :data="veiculosAcao" :resumo="resumoAcao" :loading="lAcao" />
      </section>

      <!-- ━━━━━ SEÇÃO: ANÁLISE DE POSTOS ━━━━━ -->
      <section class="v-block">
        <div class="section-title-row">
          <div class="section-heading" style="flex:1;margin:0">Análise de Postos</div>
        </div>
        <div class="postos-stack">
          <div class="posto-panel">
            <div class="posto-panel-title">
              <div style="display:flex; align-items:center; gap:10px;">
                <span class="posto-icon posto-icon-red">$</span>
                Maior custo total — Top 10
              </div>
              <div class="comb-tabs" style="margin-left: auto;">
                <button :class="{ active: filtroPostosCusto === null }" :style="pillStyle(null, filtroPostosCusto)" @click="setFiltroPostosCusto(null)">Todos</button>
                <button v-for="c in COMBUSTIVEIS" :key="c" :class="{ active: filtroPostosCusto === c }" :style="pillStyle(c, filtroPostosCusto)" @click="setFiltroPostosCusto(c)">{{ c }}</button>
              </div>
            </div>
            <TabelaRankingPostos :data="postosMaiorCusto" :loading="lPostosCusto" ordem="maior_custo" />
          </div>
          <div class="posto-panel">
            <div class="posto-panel-title">
              <div style="display:flex; align-items:center; gap:10px;">
                <span class="posto-icon posto-icon-blue">⬆</span>
                Maior volumetria — Top 10
              </div>
              <div class="comb-tabs" style="margin-left: auto;">
                <button :class="{ active: filtroPostosVolume === null }" :style="pillStyle(null, filtroPostosVolume)" @click="setFiltroPostosVolume(null)">Todos</button>
                <button v-for="c in COMBUSTIVEIS" :key="c" :class="{ active: filtroPostosVolume === c }" :style="pillStyle(c, filtroPostosVolume)" @click="setFiltroPostosVolume(c)">{{ c }}</button>
              </div>
            </div>
            <TabelaRankingPostos :data="postosMaiorVolume" :loading="lPostosVolume" ordem="maior_volume" />
          </div>
          <div class="posto-panel">
            <div class="posto-panel-title">
              <div style="display:flex; align-items:center; gap:10px;">
                <span class="posto-icon posto-icon-orange">▲</span>
                Maior preço/L — Top 10
              </div>
              <div class="comb-tabs" style="margin-left: auto;">
                <button :class="{ active: filtroPostosPreco === null }" :style="pillStyle(null, filtroPostosPreco)" @click="setFiltroPostosPreco(null)">Todos</button>
                <button v-for="c in COMBUSTIVEIS" :key="c" :class="{ active: filtroPostosPreco === c }" :style="pillStyle(c, filtroPostosPreco)" @click="setFiltroPostosPreco(c)">{{ c }}</button>
              </div>
            </div>
            <TabelaRankingPostos :data="postosMaisCaros" :loading="lPostos" ordem="mais_caro" />
          </div>
        </div>
      </section>

    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useFiltrosStore } from '../stores/filtros'
import { useRoute } from 'vue-router'
import VueApexCharts from 'vue3-apexcharts'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import TabelaVeiculosAcao from '../components/TabelaVeiculosAcao.vue'
import TabelaRankingPostos from '../components/TabelaRankingPostos.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import { fetchVeiculosAcao, fetchEvolucaoMensal } from '../api/operacional.js'
import { fetchRankingPostosPreco } from '../api/precos.js'

const apexchart = VueApexCharts

const store = useFiltrosStore()
const route = useRoute()

const familiaFiltro = ref(route.query.familia || 'todos')
const FAMILIAS_LIST = [
  { key: 'todos',    label: 'Geral' },
  { key: 'diesel',   label: 'Diesel' },
  { key: 'gasolina', label: 'Gasolina' },
  { key: 'etanol',   label: 'Etanol' },
]
const labelFamilia = computed(() => FAMILIAS_LIST.find(f => f.key === familiaFiltro.value)?.label ?? familiaFiltro.value)

const COMBUSTIVEIS = ['Diesel', 'Gasolina', 'Álcool', 'Arla']

const COMB_COLORS = {
  'Diesel':   '#2563EB',
  'Gasolina': '#7C3AED',
  'Álcool':   '#0891B2',
  'Arla':     '#64748B',
}
const TODOS_COLOR = '#334155'

function pillStyle(comb, activeRef) {
  if (comb === null) {
    if (activeRef === null) return { background: TODOS_COLOR, borderColor: TODOS_COLOR, color: 'white' }
    return { borderColor: TODOS_COLOR, color: TODOS_COLOR }
  }
  const color = COMB_COLORS[comb] ?? '#64748b'
  if (activeRef === comb) return { background: color, borderColor: color, color: 'white' }
  return { borderColor: color, color: color }
}

const COMB_TO_FAM = { 'Diesel': 'diesel', 'Gasolina': 'gasolina', 'Álcool': 'etanol', 'Arla': 'arla' }
const FAM_TO_COMB = { 'diesel': 'Diesel', 'gasolina': 'Gasolina', 'etanol': 'Álcool' }

function getFamilia(combFilter) {
  if (combFilter) return COMB_TO_FAM[combFilter] || familiaFiltro.value
  return familiaFiltro.value
}

function getCombustivel(combFilter) {
  if (combFilter) return combFilter
  const fam = familiaFiltro.value
  return fam !== 'todos' ? FAM_TO_COMB[fam] : undefined
}

// ── Filtros locais por seção ─────────────────────────────────────────────────
const filtroPostosCusto  = ref(null)
const filtroPostosVolume = ref(null)
const filtroPostosPreco  = ref(null)
const filtroAcao         = ref(null)

// ── Dados ────────────────────────────────────────────────────────────────────
const veiculosAcao   = ref([])
const resumoAcao     = ref({})
const postosMaisCaros   = ref([])
const postosMaiorVolume = ref([])
const postosMaiorCusto  = ref([])
const evolucao       = ref([])

const lAcao          = ref(true)
const lPostos        = ref(true)
const lPostosVolume  = ref(true)
const lPostosCusto   = ref(true)
const lEvolucao      = ref(true)

// ── Gráfico evolução mensal ──────────────────────────────────────────────────
const evolMeses    = computed(() => evolucao.value.map(r => {
  const [ano, mes] = r.ano_mes.split('-')
  const nomes = ['','Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
  return `${nomes[+mes]}/${ano.slice(2)}`
}))

const evolCustoKm  = computed(() => evolucao.value.map(r => r.custo_km != null ? +r.custo_km.toFixed(4) : null))
const evolKmLitro  = computed(() => evolucao.value.map(r => r.km_litro  != null ? +r.km_litro.toFixed(2)  : null))
const temKm        = computed(() => evolucao.value.some(r => r.km_litro != null))

const _chartBase = {
  chart: { toolbar: { show: false }, zoom: { enabled: false }, background: 'transparent', fontFamily: 'Inter, sans-serif' },
  grid: { borderColor: '#f1f5f9', strokeDashArray: 4 },
  tooltip: { theme: 'light', x: { show: true } },
  xaxis: { categories: [], labels: { style: { fontSize: '11px', colors: '#94a3b8' } }, axisBorder: { show: false }, axisTicks: { show: false } },
  yaxis: { labels: { style: { fontSize: '11px', colors: '#94a3b8' } } },
}

const evolCustoOpts = computed(() => ({
  ..._chartBase,
  chart: { ..._chartBase.chart, id: 'evolCusto', type: 'area' },
  stroke: { curve: 'smooth', width: 2.5 },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.25, opacityTo: 0.02 } },
  colors: ['#ef4444'],
  xaxis: { ..._chartBase.xaxis, categories: evolMeses.value },
  yaxis: { ...(_chartBase.yaxis), labels: { ..._chartBase.yaxis.labels, formatter: v => v != null ? `R$ ${v.toFixed(4)}` : '' } },
  markers: { size: 3, colors: ['#ef4444'], strokeWidth: 0 },
}))

const evolCustoSeries = computed(() => [{ name: 'Custo/km', data: evolCustoKm.value }])

const evolKmlOpts = computed(() => ({
  ..._chartBase,
  chart: { ..._chartBase.chart, id: 'evolKml', type: 'area' },
  stroke: { curve: 'smooth', width: 2.5 },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.25, opacityTo: 0.02 } },
  colors: ['#22c55e'],
  xaxis: { ..._chartBase.xaxis, categories: evolMeses.value },
  yaxis: { ...(_chartBase.yaxis), labels: { ..._chartBase.yaxis.labels, formatter: v => v != null ? `${v.toFixed(2)} km/L` : '' } },
  markers: { size: 3, colors: ['#22c55e'], strokeWidth: 0 },
}))

const evolKmlSeries = computed(() => [{ name: 'km/L', data: evolKmLitro.value }])

function buildParams(overrides = {}) {
  return {
    ...store.paramsTempo,
    familia: overrides.familia ?? familiaFiltro.value,
    grupo: store.selecao.grupo,
    filial: store.selecao.filial,
    estado: store.selecao.estado,
    regiao: store.selecao.regiao,
    ...overrides,
  }
}

async function loadAll() {
  filtroPostosCusto.value = filtroPostosVolume.value = filtroPostosPreco.value = filtroAcao.value = null

  const p = buildParams()
  const combustivelFiltro = familiaFiltro.value !== 'todos' ? FAM_TO_COMB[familiaFiltro.value] : undefined
  lAcao.value = lPostos.value = lPostosVolume.value = lPostosCusto.value = lEvolucao.value = true

  await Promise.allSettled([
    fetchVeiculosAcao(p).then(d => { veiculosAcao.value = d.veiculos ?? []; resumoAcao.value = d.resumo ?? {} }).finally(() => lAcao.value = false),
    fetchEvolucaoMensal(p).then(d => { evolucao.value = Array.isArray(d) ? d : [] }).finally(() => lEvolucao.value = false),
    fetchRankingPostosPreco({ ...p, combustivel: combustivelFiltro, ordem: 'mais_caro',    limit: 10 }).then(d => postosMaisCaros.value = d).finally(() => lPostos.value = false),
    fetchRankingPostosPreco({ ...p, combustivel: combustivelFiltro, ordem: 'maior_volume', limit: 10 }).then(d => postosMaiorVolume.value = d).finally(() => lPostosVolume.value = false),
    fetchRankingPostosPreco({ ...p, combustivel: combustivelFiltro, ordem: 'maior_custo',  limit: 10 }).then(d => postosMaiorCusto.value = d).finally(() => lPostosCusto.value = false),
  ])
}

async function setFiltroPostosCusto(comb) {
  filtroPostosCusto.value = comb
  lPostosCusto.value = true
  const combustivel = getCombustivel(comb)
  try {
    postosMaiorCusto.value = await fetchRankingPostosPreco({ ...buildParams({ familia: getFamilia(comb) }), combustivel, ordem: 'maior_custo', limit: 10 })
  } finally { lPostosCusto.value = false }
}

async function setFiltroPostosVolume(comb) {
  filtroPostosVolume.value = comb
  lPostosVolume.value = true
  const combustivel = getCombustivel(comb)
  try {
    postosMaiorVolume.value = await fetchRankingPostosPreco({ ...buildParams({ familia: getFamilia(comb) }), combustivel, ordem: 'maior_volume', limit: 10 })
  } finally { lPostosVolume.value = false }
}

async function setFiltroPostosPreco(comb) {
  filtroPostosPreco.value = comb
  lPostos.value = true
  const combustivel = getCombustivel(comb)
  try {
    postosMaisCaros.value = await fetchRankingPostosPreco({ ...buildParams({ familia: getFamilia(comb) }), combustivel, ordem: 'mais_caro', limit: 10 })
  } finally { lPostos.value = false }
}

async function setFiltroAcao(comb) {
  filtroAcao.value = comb
  lAcao.value = true
  try {
    const d = await fetchVeiculosAcao(buildParams({ familia: getFamilia(comb) }))
    veiculosAcao.value = d.veiculos ?? []
    resumoAcao.value = d.resumo ?? {}
  } finally { lAcao.value = false }
}

watch(() => store.selecao, () => loadAll(), { deep: true })
onMounted(() => loadAll())
</script>

<style scoped>
.page { background-color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; color: #0f172a; }
.page-body { padding: 24px 32px; display: flex; flex-direction: column; gap: 32px; }

/* ── Fuel Selector ── */
.fuel-selector-bar {
  display: flex; gap: 12px;
  background: #f1f5f9; padding: 6px; border-radius: 12px;
  align-self: flex-start;
}
.fuel-tab {
  background: transparent; border: none;
  padding: 8px 20px; border-radius: 8px;
  font-size: 13px; font-weight: 700; color: #64748b;
  cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.fuel-tab:hover { color: #334155; background: rgba(255,255,255,0.5); }
.fuel-tab.active {
  background: white; color: #0f172a;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
}

/* ── Layout ── */
.v-block { display: flex; flex-direction: column; gap: 16px; }
.section-heading {
  font-size: 12px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: .1em;
  display: flex; align-items: center; gap: 16px;
}
.section-heading::after { content:''; flex:1; height:1px; background: #e2e8f0; }

/* ── Filtros por seção (combustível pills) ── */
.section-title-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
}
.comb-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.comb-tabs button {
  background: transparent; border: 1.5px solid #e2e8f0; color: #64748b;
  font-size: 11px; font-weight: 700; padding: 4px 14px; border-radius: 20px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all .15s;
  letter-spacing: 0.03em;
}
.comb-tabs button.active { color: white; }
.comb-tabs button:not(.active):hover { opacity: 0.8; }

.kpi-pro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }

/* ── Postos empilhados ── */
.postos-stack { display: flex; flex-direction: column; gap: 24px; }
.posto-panel { background: linear-gradient(white, white) padding-box, linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box; border: 1px solid transparent; border-radius: 16px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
.posto-panel-title {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; font-weight: 700; color: #1e293b;
  margin-bottom: 16px; padding-bottom: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}
.posto-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 6px;
  font-size: 11px; font-weight: 900; flex-shrink: 0;
}
.posto-icon-red    { background: #fef2f2; color: #dc2626; }
.posto-icon-blue   { background: #eff6ff; color: #2563eb; }
.posto-icon-orange { background: #fff7ed; color: #ea580c; }

.empty { height: 200px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-style: italic; }

/* ── Two-col layout ── */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }

/* ── Chart panels ── */
.chart-panel {
  background: linear-gradient(white, white) padding-box,
    linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box;
  border: 1px solid transparent; border-radius: 16px; padding: 20px;
}
.chart-panel-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 8px; }
.chart-panel-title  { font-size: 13px; font-weight: 700; color: #1e293b; }
.chart-panel-unit   { font-size: 11px; color: #94a3b8; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.5s infinite; }
.kpi-skel { height: 130px; }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

.footer { padding: 32px; border-top: 1px solid rgba(0,0,0,0.07); font-size: 12px; color: #94a3b8; text-align: center; }

@media (max-width: 1000px) {
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .kpi-pro-grid { grid-template-columns: 1fr; }
}
</style>
