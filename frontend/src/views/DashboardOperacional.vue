<template>
  <div class="page">
    <GlobalTopbar
      title="Gestão de Frota"
      subtitle="Acompanhamento operacional — custo/km, eficiência, preços e alertas por grupo"
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

      <!-- ━━━━━ SEÇÃO 1: HERO KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Indicadores · {{ labelFamilia }}</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            :title="'Gasto Total — ' + labelFamilia"
            :value="kpis.total_valor || 0"
            format="currency"
            :description="fmtN(kpis.total_litros) + ' litros · ' + (kpis.qtd_veiculos || 0) + ' veículos'"
          />
          <KpiCardPro
            :title="'Custo/KM — ' + labelFamilia"
            :value="kpis.custo_km || 0"
            format="currency"
            :decimals="4"
            theme="primary"
            :description="kpis.total_km ? fmtN(kpis.total_km) + ' km rodados' : 'Sem dados de hodômetro'"
          />
          <KpiCardPro
            title="Eficiência Média"
            :value="kpis.km_litro || 0"
            format="number"
            :decimals="2"
            unit="km/L"
            :description="kpis.qtd_com_km + '/' + kpis.qtd_veiculos + ' veículos com hodômetro'"
          />
          <KpiCardPro
            title="Preço Médio / Litro"
            :value="kpis.preco_litro || 0"
            format="currency"
            :decimals="3"
            :description="kpis.economia_anp != null ? ('Econ. vs ANP: ' + fmtR(kpis.economia_anp)) : 'Volume: ' + fmtN(kpis.total_litros) + ' L'"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 2: CUSTO/KM POR GRUPO DE VEÍCULO ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Custo/KM por Grupo de Veículo</div>
        <div class="card chart-full">
          <div v-if="lGrupo" class="skel" style="height:300px" />
          <div v-else-if="!custoPorGrupo.length" class="empty">Sem dados de custo/km por grupo</div>
          <template v-else>
            <div class="grupo-table-wrap">
              <table class="grupo-table">
                <thead>
                  <tr>
                    <th>Grupo</th>
                    <th class="right">Custo/KM</th>
                    <th class="right">km/L Real</th>
                    <th class="right">km/L Ref.</th>
                    <th class="right">vs Ref.</th>
                    <th class="right">Gasto</th>
                    <th class="right">Litros</th>
                    <th class="right">Veículos</th>
                    <th style="width:160px">Barra</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="g in custoPorGrupo" :key="g.grupo">
                    <td class="grupo-nome">{{ formatGrupo(g.grupo) }}</td>
                    <td class="right mono bold">{{ g.custo_km ? `R$ ${g.custo_km.toFixed(4)}` : '—' }}</td>
                    <td class="right mono dim">{{ g.km_litro?.toFixed(2) ?? '—' }}</td>
                    <td class="right mono dim">{{ g.kml_referencia?.toFixed(2) ?? '—' }}</td>
                    <td class="right">
                      <span v-if="g.pct_vs_referencia != null" class="pct-badge" :class="pctClass(g.pct_vs_referencia)">
                        {{ (g.pct_vs_referencia > 0 ? '+' : '') + g.pct_vs_referencia.toFixed(1) + '%' }}
                      </span>
                      <span v-else class="dim">—</span>
                    </td>
                    <td class="right mono">
                      <span class="valor-cell">{{ fmtR(g.total_valor) }}</span>
                    </td>
                    <td class="right mono dim">{{ fmtN(g.total_litros) }}</td>
                    <td class="right">
                      <span class="veic-badge">{{ g.qtd_veiculos }}</span>
                    </td>
                    <td>
                      <div class="bar-wrap">
                        <div class="bar-track">
                          <div class="bar-fill" :class="barColor(g)" :style="{ width: barWidth(g.custo_km) + '%' }" />
                        </div>
                        <span class="bar-label mono" :class="pctClass(g.pct_vs_referencia)">
                          {{ g.custo_km ? `R$ ${g.custo_km.toFixed(2)}` : '' }}
                        </span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 3: CUSTO/KM POR FILIAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Custo/KM por Filial</div>
        <GraficoBarrasFilial
          :data="filialData"
          :familia="familiaFiltro"
          :loading="lFilial"
        />
      </section>

      <!-- ━━━━━ SEÇÃO 4: POSTOS ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Análise de Postos</div>
        <div class="postos-stack">

          <!-- Maior Custo Total -->
          <div class="posto-panel">
            <div class="posto-panel-title">
              <span class="posto-icon posto-icon-red">$</span>
              Maior custo total — Top 10
            </div>
            <TabelaRankingPostos :data="postosMaiorCusto" :loading="lPostosCusto" ordem="maior_custo" />
          </div>

          <!-- Maior Volume -->
          <div class="posto-panel">
            <div class="posto-panel-title">
              <span class="posto-icon posto-icon-blue">⬆</span>
              Maior volumetria — Top 10
            </div>
            <TabelaRankingPostos :data="postosMaiorVolume" :loading="lPostosVolume" ordem="maior_volume" />
          </div>

          <!-- Mais Caros (preço/L) -->
          <div class="posto-panel">
            <div class="posto-panel-title">
              <span class="posto-icon posto-icon-orange">▲</span>
              Maior preço/L — Top 10
            </div>
            <TabelaRankingPostos :data="postosMaisCaros" :loading="lPostos" ordem="mais_caro" />
          </div>

        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 5: VARIAÇÃO DE PREÇO POR MÊS ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Variação de Preço Médio por Mês</div>
        <GraficoVariacaoMensal :data="variacao" :loading="lVariacao" />
      </section>

      <!-- ━━━━━ SEÇÃO 6: MONITORAMENTO DE FROTA ━━━━━ -->
      <section id="secao-acao" class="v-block">
        <div class="section-heading">Veículos sob Alerta · Comparação por Grupo</div>
        <TabelaVeiculosAcao :data="veiculosAcao" :resumo="resumoAcao" :loading="lAcao" />
      </section>

      <!-- ━━━━━ SEÇÃO 7A: EVOLUÇÃO CUSTO/KM ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Evolução Histórica · Custo/KM (12 meses)</div>
        <div class="card">
          <div v-if="lEvolucao" class="skel" style="height:240px" />
          <div v-else-if="!evolucao.length" class="empty">Sem dados históricos</div>
          <template v-else>
            <div class="evolucao-summary">
              <div class="evo-stat">
                <span class="evo-label">Menor custo</span>
                <span class="evo-val green">{{ evolucaoMin ? `R$ ${evolucaoMin.toFixed(4)}` : '—' }}</span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Maior custo</span>
                <span class="evo-val red">{{ evolucaoMax ? `R$ ${evolucaoMax.toFixed(4)}` : '—' }}</span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Variação período</span>
                <span class="evo-val" :class="evolucaoVar >= 0 ? 'red' : 'green'">
                  {{ evolucaoVar != null ? (evolucaoVar > 0 ? '+' : '') + evolucaoVar.toFixed(1) + '%' : '—' }}
                </span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Tendência (3m)</span>
                <span class="evo-val" :class="tendenciaCustoKm >= 0 ? 'red' : 'green'">
                  {{ tendenciaCustoKm != null ? (tendenciaCustoKm > 0 ? '▲ Alta' : '▼ Queda') : '—' }}
                </span>
              </div>
            </div>
            <apexchart type="area" height="220" :options="optCustoKm" :series="seriesCustoKm" />
          </template>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 7B: EVOLUÇÃO PREÇO/L ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Evolução Histórica · Preço/Litro (12 meses)</div>
        <div class="card">
          <div v-if="lEvolucao" class="skel" style="height:240px" />
          <div v-else-if="!evolucao.length" class="empty">Sem dados históricos</div>
          <template v-else>
            <div class="evolucao-summary">
              <div class="evo-stat">
                <span class="evo-label">Menor preço</span>
                <span class="evo-val green">{{ precoMin ? `R$ ${precoMin.toFixed(3)}` : '—' }}</span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Maior preço</span>
                <span class="evo-val red">{{ precoMax ? `R$ ${precoMax.toFixed(3)}` : '—' }}</span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Variação período</span>
                <span class="evo-val" :class="precoVar >= 0 ? 'red' : 'green'">
                  {{ precoVar != null ? (precoVar > 0 ? '+' : '') + precoVar.toFixed(1) + '%' : '—' }}
                </span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Volume total</span>
                <span class="evo-val">{{ fmtN(evolucaoVolTotal) }} L</span>
              </div>
            </div>
            <apexchart type="area" height="220" :options="optPrecoL" :series="seriesPrecoL" />
          </template>
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
import GraficoBarrasFilial from '../components/GraficoBarrasFilial.vue'
import GraficoVariacaoMensal from '../components/GraficoVariacaoMensal.vue'
import TabelaVeiculosAcao from '../components/TabelaVeiculosAcao.vue'
import TabelaRankingPostos from '../components/TabelaRankingPostos.vue'
import KpiCardPro from '../components/KpiCardPro.vue'

import {
  fetchKpisOperacional, fetchCustoPorGrupo, fetchCustoPorFilial,
  fetchEvolucaoMensal, fetchVeiculosAcao,
} from '../api/operacional.js'
import { fetchRankingPostosPreco, fetchVariacaoMensal } from '../api/precos.js'

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

const kpis            = ref({})
const custoPorGrupo   = ref([])
const custoPorFilial  = ref({ filiais: [], media_geral: null })
const evolucao        = ref([])
const veiculosAcao    = ref([])
const resumoAcao      = ref({})
const postosMaisCaros    = ref([])
const postosMaiorVolume  = ref([])
const postosMaiorCusto   = ref([])
const variacao        = ref([])

const lKpis    = ref(true)
const lGrupo   = ref(true)
const lFilial  = ref(true)
const lEvolucao = ref(true)
const lAcao    = ref(true)
const lPostos  = ref(true)
const lPostosVolume = ref(true)
const lPostosCusto  = ref(true)
const lVariacao = ref(true)

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

const filialData = computed(() => custoPorFilial.value.filiais || [])

function formatGrupo(g) {
  return g.replace('Caminhão', 'Caminhão ').replace('Ton', 'T').replace('10.5', '10,5').replace('4.2', '4,2').replace('5.5', '5,5').replace('7.5', '7,5')
}

const maxCustoGrupo = computed(() => {
  const vals = custoPorGrupo.value.map(g => g.custo_km).filter(Boolean)
  return vals.length ? Math.max(...vals) : 1
})
function barWidth(ck) { return ck ? Math.round((ck / maxCustoGrupo.value) * 100) : 0 }
function barColor(g) {
  if (!g.pct_vs_referencia) return 'bar-gray'
  if (g.pct_vs_referencia >= 0) return 'bar-green'
  if (g.pct_vs_referencia > -15) return 'bar-orange'
  return 'bar-red'
}
function pctClass(pct) {
  if (pct == null) return 'neutral'
  return pct >= 0 ? 'ok' : pct > -15 ? 'warn' : 'crit'
}

// Métricas de evolução
const evolucaoVals = computed(() => evolucao.value.map(d => d.custo_km).filter(v => v != null))
const precoVals    = computed(() => evolucao.value.map(d => d.preco_litro).filter(v => v != null))
const evolucaoMin  = computed(() => evolucaoVals.value.length ? Math.min(...evolucaoVals.value) : null)
const evolucaoMax  = computed(() => evolucaoVals.value.length ? Math.max(...evolucaoVals.value) : null)
const precoMin     = computed(() => precoVals.value.length ? Math.min(...precoVals.value) : null)
const precoMax     = computed(() => precoVals.value.length ? Math.max(...precoVals.value) : null)
const evolucaoVolTotal = computed(() => evolucao.value.reduce((s, d) => s + (d.total_litros || 0), 0))

const evolucaoVar = computed(() => {
  const v = evolucaoVals.value
  if (v.length < 2) return null
  return +((v[v.length - 1] - v[0]) / v[0] * 100).toFixed(1)
})
const precoVar = computed(() => {
  const v = precoVals.value
  if (v.length < 2) return null
  return +((v[v.length - 1] - v[0]) / v[0] * 100).toFixed(1)
})
const tendenciaCustoKm = computed(() => {
  const v = evolucaoVals.value
  if (v.length < 3) return null
  const last3 = v.slice(-3)
  return last3[last3.length - 1] - last3[0]
})

function buildParams() {
  return {
    ...store.paramsTempo,
    familia: familiaFiltro.value,
    grupo: store.selecao.grupo,
    filial: store.selecao.filial,
    estado: store.selecao.estado,
    regiao: store.selecao.regiao,
  }
}

async function loadAll() {
  const p = buildParams()
  const fam = familiaFiltro.value
  const combustivelFiltro = fam !== 'todos' ? fam : undefined
  lKpis.value = lGrupo.value = lFilial.value = lEvolucao.value = lAcao.value = lPostos.value = lPostosVolume.value = lPostosCusto.value = lVariacao.value = true

  await Promise.allSettled([
    fetchKpisOperacional(p).then(d => kpis.value = d).finally(() => lKpis.value = false),
    fetchCustoPorGrupo(p).then(d => custoPorGrupo.value = d).finally(() => lGrupo.value = false),
    fetchCustoPorFilial(p).then(d => custoPorFilial.value = d).finally(() => lFilial.value = false),
    fetchEvolucaoMensal(p).then(d => evolucao.value = d).finally(() => lEvolucao.value = false),
    fetchVeiculosAcao(p).then(d => { veiculosAcao.value = d.veiculos ?? []; resumoAcao.value = d.resumo ?? {} }).finally(() => lAcao.value = false),
    fetchRankingPostosPreco({ ...p, combustivel: combustivelFiltro, ordem: 'mais_caro',    limit: 10 }).then(d => postosMaisCaros.value = d).finally(() => lPostos.value = false),
    fetchRankingPostosPreco({ ...p, combustivel: combustivelFiltro, ordem: 'maior_volume', limit: 10 }).then(d => postosMaiorVolume.value = d).finally(() => lPostosVolume.value = false),
    fetchRankingPostosPreco({ ...p, combustivel: combustivelFiltro, ordem: 'maior_custo',  limit: 10 }).then(d => postosMaiorCusto.value = d).finally(() => lPostosCusto.value = false),
    fetchVariacaoMensal({ ...p, combustivel: combustivelFiltro }).then(d => variacao.value = d).finally(() => lVariacao.value = false),
  ])
}

watch(() => store.selecao, () => loadAll(), { deep: true })
onMounted(() => loadAll())

// ── Gráficos separados ──
const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]}/${y.slice(2)}` }

const chartBaseOpt = {
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2.5 },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.02 } },
  markers: { size: 4, strokeWidth: 0 },
  grid: { borderColor: '#f1f5f9', strokeDashArray: 4 },
  xaxis: { labels: { style: { colors: '#94a3b8', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' } }, axisBorder: { show: false }, axisTicks: { show: false } },
}

const optCustoKm = computed(() => ({
  ...chartBaseOpt,
  colors: ['#f97316'],
  xaxis: { ...chartBaseOpt.xaxis, categories: evolucao.value.map(d => fmtMes(d.ano_mes)) },
  yaxis: {
    labels: {
      style: { colors: '#f97316', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
      formatter: v => v != null ? `R$ ${Number(v).toFixed(2)}` : '',
    },
    min: 0,
  },
  tooltip: {
    theme: 'light',
    y: { formatter: v => v != null ? `R$ ${Number(v).toFixed(4)}/km` : '—' },
  },
  annotations: evolucaoMin.value ? {
    yaxis: [{
      y: evolucaoMin.value,
      borderColor: '#10b981',
      borderWidth: 1,
      strokeDashArray: 4,
      label: { text: `Mín R$ ${evolucaoMin.value.toFixed(4)}`, style: { color: '#10b981', fontSize: '10px', background: '#ecfdf5' } },
    }, {
      y: evolucaoMax.value,
      borderColor: '#ef4444',
      borderWidth: 1,
      strokeDashArray: 4,
      label: { text: `Máx R$ ${evolucaoMax.value.toFixed(4)}`, style: { color: '#ef4444', fontSize: '10px', background: '#fef2f2' } },
    }],
  } : {},
}))

const seriesCustoKm = computed(() => [{
  name: 'Custo/km (R$/km)',
  data: evolucao.value.map(d => d.custo_km != null ? +d.custo_km.toFixed(4) : null),
}])

const optPrecoL = computed(() => ({
  ...chartBaseOpt,
  colors: ['#3b82f6'],
  xaxis: { ...chartBaseOpt.xaxis, categories: evolucao.value.map(d => fmtMes(d.ano_mes)) },
  yaxis: {
    labels: {
      style: { colors: '#3b82f6', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
      formatter: v => v != null ? `R$ ${Number(v).toFixed(2)}` : '',
    },
    min: 0,
  },
  tooltip: {
    theme: 'light',
    y: [
      { formatter: v => v != null ? `R$ ${Number(v).toFixed(3)}/L` : '—' },
      { formatter: v => v != null ? fmtN(v) + ' L' : '—' },
    ],
  },
}))

const seriesPrecoL = computed(() => [
  {
    name: 'Preço/L (R$/L)',
    type: 'area',
    data: evolucao.value.map(d => d.preco_litro != null ? +d.preco_litro.toFixed(3) : null),
  },
])
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

.kpi-pro-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
.chart-full { padding: 32px; }

/* ── Tabela de Grupo ── */
.grupo-table-wrap { overflow-x: auto; }
.grupo-table { width: 100%; border-collapse: collapse; }
.grupo-table thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 10px 12px;
  border-bottom: 2px solid #f1f5f9; white-space: nowrap;
}
.grupo-table th.right, .grupo-table td.right { text-align: right; }
.grupo-table tbody td {
  font-size: 13px; color: #334155; padding: 13px 12px;
  border-bottom: 1px solid #f8fafc; white-space: nowrap; vertical-align: middle;
}
.grupo-table tbody tr:last-child td { border-bottom: none; }
.grupo-table tbody tr:hover { background: #fafafa; }

.grupo-nome { font-weight: 700; color: #0f172a; }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.bold { font-weight: 700; color: #0f172a; }
.dim { color: #94a3b8; }

/* Porcentagem colorida com badge */
.pct-badge {
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 20px;
  font-family: 'JetBrains Mono', monospace; white-space: nowrap;
}
.pct-badge.ok   { background: #ecfdf5; color: #059669; border: 1px solid rgba(5,150,105,.15); }
.pct-badge.warn { background: #fffbeb; color: #d97706; border: 1px solid rgba(217,119,6,.15); }
.pct-badge.crit { background: #fef2f2; color: #dc2626; border: 1px solid rgba(220,38,38,.15); }
.pct-badge.neutral { background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; }

.valor-cell { font-weight: 600; color: #1e293b; font-size: 12px; font-family: 'JetBrains Mono', monospace; }
.veic-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 28px; padding: 2px 8px; border-radius: 12px;
  background: #f1f5f9; color: #475569; font-size: 12px; font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

/* Barra com label */
.bar-wrap { display: flex; align-items: center; gap: 8px; }
.bar-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.bar-label { font-size: 10px; white-space: nowrap; min-width: 52px; }
.bar-green  { background: linear-gradient(90deg, #10b981, #34d399); }
.bar-orange { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.bar-red    { background: linear-gradient(90deg, #ef4444, #f87171); }
.bar-gray   { background: #94a3b8; }

/* Cores inline para texto */
.ok   { color: #059669; font-weight: 600; }
.warn { color: #d97706; font-weight: 600; }
.crit { color: #dc2626; font-weight: 600; }
.green { color: #059669; font-weight: 700; }
.red   { color: #dc2626; font-weight: 700; }

/* ── Postos empilhados ── */
.postos-stack { display: flex; flex-direction: column; gap: 24px; }
.posto-panel { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
.posto-panel-title {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; font-weight: 700; color: #1e293b;
  margin-bottom: 16px; padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}
.posto-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 6px;
  font-size: 11px; font-weight: 900; flex-shrink: 0;
}
.posto-icon-red    { background: #fef2f2; color: #dc2626; }
.posto-icon-blue   { background: #eff6ff; color: #2563eb; }
.posto-icon-orange { background: #fff7ed; color: #ea580c; }

/* ── Evolução summary strip ── */
.evolucao-summary {
  display: flex; gap: 32px; margin-bottom: 16px;
  padding: 12px 16px; background: #f8fafc;
  border-radius: 10px; flex-wrap: wrap;
}
.evo-stat { display: flex; flex-direction: column; gap: 2px; }
.evo-label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; }
.evo-val { font-size: 15px; font-weight: 700; color: #1e293b; font-family: 'JetBrains Mono', monospace; }

.empty { height: 200px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.5s infinite; }
.kpi-skel { height: 130px; }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

.footer { padding: 32px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; }

@media (max-width: 1200px) {
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
