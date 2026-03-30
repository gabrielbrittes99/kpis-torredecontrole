<template>
  <div class="page">
    <GlobalTopbar
      title="Gestão de Pedágios"
      subtitle="Análise consolidada de gastos e passagens com tags"
    />

    <div class="page-body">

      <!-- ━━━━━ SEÇÃO 1: HERO KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Indicadores de Pedágio</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            title="Gasto Total"
            :value="kpis.total_gasto || 0"
            format="currency"
            theme="primary"
          />
          <KpiCardPro
            title="Passagens"
            :value="kpis.qtd_passagens || 0"
            format="number"
          />
          <KpiCardPro
            title="Ticket Médio"
            :value="kpis.ticket_medio || 0"
            format="currency"
          />
          <KpiCardPro
            title="Maior Passagem"
            :value="kpis.max_passagem || 0"
            format="currency"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 2: GASTO POR GRUPO ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Gasto por Grupo de Veículo</div>
        <div class="card chart-full">
          <div v-if="lGrupo" class="skel" style="height:260px" />
          <div v-else-if="!porGrupo.length" class="empty">Sem dados para o período</div>
          <template v-else>
            <div class="grupo-table-wrap">
              <table class="grupo-table">
                <thead>
                  <tr>
                    <th>Grupo</th>
                    <th class="right">Passagens</th>
                    <th class="right">Veículos</th>
                    <th class="right">Ticket Médio</th>
                    <th class="right">Gasto Total</th>
                    <th style="width:160px">Barra</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="g in porGrupo" :key="g.grupo">
                    <td class="grupo-nome">{{ g.grupo || '—' }}</td>
                    <td class="right mono dim">{{ g.qtd_passagens }}</td>
                    <td class="right">
                      <span class="veic-badge">{{ g.qtd_veiculos }}</span>
                    </td>
                    <td class="right mono">{{ fmtR(g.ticket_medio) }}</td>
                    <td class="right mono bold">{{ fmtR(g.total_gasto) }}</td>
                    <td>
                      <div class="bar-wrap">
                        <div class="bar-track">
                          <div class="bar-fill bar-orange" :style="{ width: barWidth(g.total_gasto) + '%' }" />
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 3: GASTO POR FILIAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Gasto por Filial</div>
        <div class="card chart-full">
          <div v-if="lFilial" class="skel" style="height:260px" />
          <div v-else-if="!porFilial.length" class="empty">Sem dados para o período</div>
          <template v-else>
            <div class="grupo-table-wrap">
              <table class="grupo-table">
                <thead>
                  <tr>
                    <th>Filial</th>
                    <th class="right">Passagens</th>
                    <th class="right">Ticket Médio</th>
                    <th class="right">Gasto Total</th>
                    <th style="width:160px">Barra</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="f in porFilial" :key="f.filial">
                    <td class="grupo-nome">{{ f.filial || '—' }}</td>
                    <td class="right mono dim">{{ f.qtd_passagens }}</td>
                    <td class="right mono">{{ fmtR(f.ticket_medio) }}</td>
                    <td class="right mono bold">{{ fmtR(f.total_gasto) }}</td>
                    <td>
                      <div class="bar-wrap">
                        <div class="bar-track">
                          <div class="bar-fill bar-red" :style="{ width: barWidthFilial(f.total_gasto) + '%' }" />
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 4: RANKING DE VEÍCULOS ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Ranking de Veículos — Top 10</div>
        <div class="card chart-full">
          <div v-if="lRanking" class="skel" style="height:260px" />
          <div v-else-if="!ranking.length" class="empty">Nenhum registro para o período</div>
          <template v-else>
            <div class="grupo-table-wrap">
              <table class="grupo-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Placa</th>
                    <th class="right">Passagens</th>
                    <th class="right">Ticket Médio</th>
                    <th class="right">Gasto Total</th>
                    <th style="width:160px">Barra</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in ranking" :key="item.placa">
                    <td class="mono dim">{{ idx + 1 }}</td>
                    <td class="grupo-nome mono">{{ item.placa }}</td>
                    <td class="right mono dim">{{ item.qtd_passagens }}</td>
                    <td class="right mono">{{ fmtR(item.ticket_medio) }}</td>
                    <td class="right mono bold">{{ fmtR(item.total_gasto) }}</td>
                    <td>
                      <div class="bar-wrap">
                        <div class="bar-track">
                          <div class="bar-fill bar-orange" :style="{ width: barWidthRanking(item.total_gasto) + '%' }" />
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 5: EVOLUÇÃO MENSAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Evolução Histórica · Gasto Mensal</div>
        <div class="card">
          <div v-if="lHistorico" class="skel" style="height:240px" />
          <div v-else-if="!historico.length" class="empty">Sem histórico disponível</div>
          <template v-else>
            <div class="evolucao-summary">
              <div class="evo-stat">
                <span class="evo-label">Menor mês</span>
                <span class="evo-val green">{{ historicoMin ? fmtR(historicoMin) : '—' }}</span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Maior mês</span>
                <span class="evo-val red">{{ historicoMax ? fmtR(historicoMax) : '—' }}</span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Variação período</span>
                <span class="evo-val" :class="historicoVar >= 0 ? 'red' : 'green'">
                  {{ historicoVar != null ? (historicoVar > 0 ? '+' : '') + historicoVar.toFixed(1) + '%' : '—' }}
                </span>
              </div>
              <div class="evo-stat">
                <span class="evo-label">Total passagens</span>
                <span class="evo-val">{{ fmtN(historicoTotalPassagens) }}</span>
              </div>
            </div>
            <apexchart type="area" height="220" :options="chartOptions" :series="chartSeries" />
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
import VueApexCharts from 'vue3-apexcharts'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import { useFiltrosStore } from '../stores/filtros'
import {
  fetchPedagiosVisaoGeral,
  fetchPedagiosHistoricoMensal,
  fetchPedagiosRankingVeiculos,
  fetchPedagiosPorFilial,
  fetchPedagiosPorGrupo,
} from '../api/pedagios.js'

const apexchart = VueApexCharts
const store = useFiltrosStore()

const kpis     = ref({})
const historico = ref([])
const ranking  = ref([])
const porFilial = ref([])
const porGrupo  = ref([])

const lKpis     = ref(true)
const lHistorico = ref(true)
const lRanking  = ref(true)
const lFilial   = ref(true)
const lGrupo    = ref(true)

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

function buildParams() {
  return {
    ...store.paramsTempo,
    filial: store.selecao.filial,
    grupo:  store.selecao.grupo,
    estado: store.selecao.estado,
    regiao: store.selecao.regiao,
  }
}

async function loadAll() {
  const p = buildParams()
  lKpis.value = lHistorico.value = lRanking.value = lFilial.value = lGrupo.value = true

  await Promise.allSettled([
    fetchPedagiosVisaoGeral(p).then(d => kpis.value = d ?? {}).finally(() => lKpis.value = false),
    fetchPedagiosHistoricoMensal(p).then(d => historico.value = d ?? []).finally(() => lHistorico.value = false),
    fetchPedagiosRankingVeiculos({ ...p, limit: 10 }).then(d => ranking.value = d ?? []).finally(() => lRanking.value = false),
    fetchPedagiosPorFilial(p).then(d => porFilial.value = d ?? []).finally(() => lFilial.value = false),
    fetchPedagiosPorGrupo(p).then(d => porGrupo.value = d ?? []).finally(() => lGrupo.value = false),
  ])
}

watch(() => store.selecao, () => loadAll(), { deep: true })
onMounted(() => loadAll())

// Métricas de evolução
const historicoVals = computed(() => historico.value.map(d => d.total_gasto).filter(v => v != null))
const historicoMin  = computed(() => historicoVals.value.length ? Math.min(...historicoVals.value) : null)
const historicoMax  = computed(() => historicoVals.value.length ? Math.max(...historicoVals.value) : null)
const historicoTotalPassagens = computed(() => historico.value.reduce((s, d) => s + (d.qtd_passagens || 0), 0))
const historicoVar  = computed(() => {
  const v = historicoVals.value
  if (v.length < 2) return null
  return +((v[v.length - 1] - v[0]) / v[0] * 100).toFixed(1)
})

// Barras
const maxGrupo   = computed(() => Math.max(...porGrupo.value.map(g => g.total_gasto || 0), 1))
const maxFilial  = computed(() => Math.max(...porFilial.value.map(f => f.total_gasto || 0), 1))
const maxRanking = computed(() => Math.max(...ranking.value.map(r => r.total_gasto || 0), 1))
const barWidth       = v => v ? Math.round((v / maxGrupo.value) * 100) : 0
const barWidthFilial = v => v ? Math.round((v / maxFilial.value) * 100) : 0
const barWidthRanking = v => v ? Math.round((v / maxRanking.value) * 100) : 0

// Gráfico
const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]}/${y.slice(2)}` }

const chartSeries = computed(() => [{
  name: 'Gasto R$',
  data: historico.value.map(d => d.total_gasto != null ? +d.total_gasto.toFixed(2) : null),
}])

const chartOptions = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  colors: ['#F59E0B'],
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2.5 },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.02 } },
  markers: { size: 4, strokeWidth: 0 },
  grid: { borderColor: '#f1f5f9', strokeDashArray: 4 },
  xaxis: {
    categories: historico.value.map(d => fmtMes(d.ano_mes)),
    labels: { style: { colors: '#94a3b8', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' } },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: { colors: '#F59E0B', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
      formatter: v => v != null ? `R$ ${Number(v).toFixed(0)}` : '',
    },
    min: 0,
  },
  tooltip: {
    theme: 'light',
    y: { formatter: v => v != null ? fmtR(v) : '—' },
  },
}))
</script>

<style scoped>
.page { background-color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; color: #0f172a; }
.page-body { padding: 24px 32px; display: flex; flex-direction: column; gap: 32px; }

.v-block { display: flex; flex-direction: column; gap: 16px; }
.section-heading {
  font-size: 12px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: .1em;
  display: flex; align-items: center; gap: 16px;
}
.section-heading::after { content: ''; flex: 1; height: 1px; background: #e2e8f0; }

.kpi-pro-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.card { background: linear-gradient(white, white) padding-box, linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box; border: 1px solid transparent; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
.chart-full { padding: 32px; }

/* Tabela */
.grupo-table-wrap { overflow-x: auto; }
.grupo-table { width: 100%; border-collapse: collapse; }
.grupo-table thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 10px 12px;
  border-bottom: 2px solid rgba(0,0,0,0.07); white-space: nowrap;
}
.grupo-table th.right, .grupo-table td.right { text-align: right; }
.grupo-table tbody td {
  font-size: 13px; color: #334155; padding: 13px 12px;
  border-bottom: 1px solid rgba(0,0,0,0.03); white-space: nowrap; vertical-align: middle;
}
.grupo-table tbody tr:last-child td { border-bottom: none; }
.grupo-table tbody tr:hover { background: #fafafa; }

.grupo-nome { font-weight: 700; color: #0f172a; }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.bold { font-weight: 700; color: #0f172a; }
.dim  { color: #94a3b8; }

.veic-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 28px; padding: 2px 8px; border-radius: 12px;
  background: #f1f5f9; color: #475569; font-size: 12px; font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

/* Barras */
.bar-wrap { display: flex; align-items: center; gap: 8px; }
.bar-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.bar-orange { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.bar-red    { background: linear-gradient(90deg, #C41230, #ef4444); }

/* Evolução summary */
.evolucao-summary {
  display: flex; gap: 32px; margin-bottom: 16px;
  padding: 12px 16px; background: #f8fafc;
  border-radius: 10px; flex-wrap: wrap;
}
.evo-stat { display: flex; flex-direction: column; gap: 2px; }
.evo-label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; }
.evo-val { font-size: 15px; font-weight: 700; color: #1e293b; font-family: 'JetBrains Mono', monospace; }
.green { color: #059669; font-weight: 700; }
.red   { color: #dc2626; font-weight: 700; }

.empty { height: 200px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.5s infinite; }
.kpi-skel { height: 130px; }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

.footer { padding: 32px; border-top: 1px solid rgba(0,0,0,0.07); font-size: 12px; color: #94a3b8; text-align: center; }

@media (max-width: 1200px) {
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
