<template>
  <div class="page">
    <header class="topbar">
      <div class="topbar-main">
        <div class="topbar-left">
          <span class="logo">
            GRITSCH <span class="divider">//</span>
            <div class="title-group">
              <span class="subtitle">Manutenção · Visão da Diretoria</span>
              <span class="page-subtitle">KPIs estratégicos, tendência e ranking de filiais</span>
            </div>
          </span>
        </div>
        <div class="topbar-center">
          <div class="fkm-filters">
            <div class="filter-group">
              <label>Mês</label>
              <select v-model="filtroMes" @change="loadAll">
                <option v-for="m in meses" :key="m" :value="m">{{ fmtMes(m) }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Filial</label>
              <select v-model="filtroFilial" @change="loadAll">
                <option value="">Todas</option>
                <option v-for="f in filiais" :key="f" :value="f">{{ f }}</option>
              </select>
            </div>
          </div>
        </div>
        <div class="topbar-right"></div>
      </div>
    </header>

    <div class="page-body">

      <!-- ━━━━━ KPIs ESTRATÉGICOS ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">KPIs Estratégicos · {{ fmtMes(filtroMes) }}</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            title="Total Manutenção"
            :value="kpis.total_manutencao || 0"
            format="currency"
            theme="primary"
            :trendValue="kpis.var_mes_ant_pct"
            :trendInvert="true"
            :description="`vs ${fmtMes(kpis.ano_mes_ant)}: ${fmtR(kpis.total_mes_ant)}`"
          />
          <KpiCardPro
            title="% do Custo Total Frota"
            :value="kpis.pct_custo_frota || 0"
            format="percent"
            :description="`Participação da manutenção no custo total`"
          />
          <KpiCardPro
            title="Custo/KM Manutenção"
            :value="kpis.custo_km || 0"
            format="currency"
            :decimals="4"
            :description="`Custo por km rodado com manutenção`"
          />
          <KpiCardPro
            title="vs Média 6 Meses"
            :value="kpis.var_media_6m_pct || 0"
            format="percent"
            :trendValue="kpis.var_media_6m_pct"
            :trendInvert="true"
            :description="`Média 6m: ${fmtR(kpis.media_6m)}`"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- ━━━━━ TENDÊNCIA ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Tendência de Custo de Manutenção</div>
        <div v-if="lTendencia" class="skel" style="height:300px" />
        <div v-else-if="!tendencia.length" class="empty">Sem dados de tendência</div>
        <apexchart v-else type="line" height="300" :options="tendOpts" :series="tendSeries" />
      </section>

      <!-- ━━━━━ PARTICIPAÇÃO NO CUSTO FROTA ━━━━━ -->
      <div class="two-col">
        <section class="v-block">
          <div class="section-heading">Manutenção como % do Custo Total Frota</div>
          <div v-if="lTendencia" class="skel" style="height:240px" />
          <div v-else-if="!tendencia.length" class="empty">Sem dados</div>
          <apexchart v-else type="area" height="240" :options="pctOpts" :series="pctSeries" />
        </section>

        <section class="v-block">
          <div class="section-heading">Custo/KM Manutenção por Mês</div>
          <div v-if="lTendencia" class="skel" style="height:240px" />
          <div v-else-if="!tendencia.length" class="empty">Sem dados</div>
          <apexchart v-else type="line" height="240" :options="ckOpts" :series="ckSeries" />
        </section>
      </div>

      <!-- ━━━━━ RANKING FILIAIS ━━━━━ -->
      <section class="v-block">
        <div class="section-heading-row">
          <div class="section-heading">Ranking Filiais — Custo/KM Manutenção · {{ fmtMes(filtroMes) }}</div>
          <div class="legend-flags">
            <span class="flag flag-alto">ALTO</span>
            <span class="flag flag-normal">NORMAL</span>
            <span class="flag flag-baixo">BAIXO</span>
          </div>
        </div>
        <div v-if="lRanking" class="skel" style="height:240px" />
        <div v-else-if="!ranking.length" class="empty">Sem dados de ranking</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Filial</th>
                <th class="right">Total Manutenção</th>
                <th class="right">KM Total</th>
                <th class="right">Custo/KM Man.</th>
                <th class="right">vs Média</th>
                <th class="right">% Custo Frota</th>
                <th class="right">Veículos</th>
                <th class="center">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in ranking" :key="row.filial">
                <td class="idx">{{ i + 1 }}</td>
                <td class="filial-cell">{{ row.filial }}</td>
                <td class="right mono fw-bold">{{ fmtR(row.total_geral) }}</td>
                <td class="right mono">{{ fmtN(row.total_km) }}</td>
                <td class="right mono" :class="ckClass(row.custo_km_man)">{{ fmt4(row.custo_km_man) }}</td>
                <td class="right mono" :class="varClass(row.pct_vs_media)">
                  {{ row.pct_vs_media != null ? (row.pct_vs_media > 0 ? '+' : '') + row.pct_vs_media + '%' : '—' }}
                </td>
                <td class="right mono">{{ row.pct_man_frota != null ? row.pct_man_frota + '%' : '—' }}</td>
                <td class="right mono">{{ row.qtd_veiculos }}</td>
                <td class="center">
                  <span class="flag" :class="`flag-${(row.flag || 'NORMAL').toLowerCase()}`">{{ row.flag }}</span>
                </td>
              </tr>
            </tbody>
            <tfoot v-if="ranking[0]?.media_geral_custo_km">
              <tr>
                <td colspan="4" class="tfoot-label">Média Geral (Frota)</td>
                <td class="right mono tfoot-val">{{ fmt4(ranking[0].media_geral_custo_km) }}</td>
                <td colspan="4"></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import {
  fetchManutencaoFiltros,
  fetchManutencaoKpisEstrategicos,
  fetchManutencaoTendencia,
  fetchManutencaoRankingFiliais,
} from '../api/manutencao.js'

const meses   = ref([])
const filiais = ref([])
const filtroMes    = ref('')
const filtroFilial = ref('')

const kpis     = ref({})
const tendencia = ref([])
const ranking  = ref([])

const lKpis     = ref(true)
const lTendencia = ref(true)
const lRanking  = ref(true)

const fmtR = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtN = (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
const fmt4 = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
const fmtMes = (ym) => {
  if (!ym) return '—'
  const [ano, mes] = ym.split('-')
  const n = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  return `${n[parseInt(mes)]}/${ano}`
}
const ckClass  = (v) => v == null ? '' : v > 0.5 ? 'text-red' : v > 0.3 ? 'text-yellow' : 'text-green'
const varClass = (v) => v == null ? '' : v > 10 ? 'text-red' : v < -10 ? 'text-green' : 'text-muted'

// ── Tendência: custo total manutenção
const tendSeries = computed(() => [{
  name: 'Manutenção',
  data: tendencia.value.map(t => t.total_manutencao),
}])
const tendOpts = computed(() => ({
  chart: { type: 'line', background: 'transparent', fontFamily: 'Inter', toolbar: { show: false }, sparkline: { enabled: false } },
  stroke: { curve: 'smooth', width: 3 },
  colors: ['#C41230'],
  markers: { size: 4, colors: ['#C41230'], strokeColors: '#fff', strokeWidth: 2 },
  xaxis: {
    categories: tendencia.value.map(t => fmtMes(t.ano_mes)),
    labels: { style: { colors: '#94a3b8', fontSize: '11px' } },
  },
  yaxis: { labels: { formatter: (v) => 'R$ ' + (v / 1000).toFixed(0) + 'k', style: { colors: '#94a3b8', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
  annotations: {
    yaxis: tendencia.value.length > 0 ? [{
      y: tendencia.value.reduce((s, t) => s + (t.total_manutencao || 0), 0) / tendencia.value.length,
      borderColor: '#94a3b8',
      strokeDashArray: 4,
      label: { text: 'Média', style: { color: '#94a3b8', fontSize: '10px', background: 'transparent' } },
    }] : [],
  },
}))

// ── % manutenção no custo total frota
const pctSeries = computed(() => [{
  name: '% Manutenção/Frota',
  data: tendencia.value.map(t => t.pct_man_frota),
}])
const pctOpts = computed(() => ({
  chart: { type: 'area', background: 'transparent', fontFamily: 'Inter', toolbar: { show: false } },
  stroke: { curve: 'smooth', width: 2 },
  colors: ['#3b82f6'],
  fill: { type: 'gradient', gradient: { shadeIntensity: 0.5, opacityFrom: 0.4, opacityTo: 0.05 } },
  xaxis: { categories: tendencia.value.map(t => fmtMes(t.ano_mes)), labels: { style: { colors: '#94a3b8', fontSize: '10px' } } },
  yaxis: { labels: { formatter: (v) => (v || 0).toFixed(1) + '%', style: { colors: '#94a3b8', fontSize: '10px' } } },
  grid: { borderColor: '#e2e8f0' },
  tooltip: { y: { formatter: (v) => (v || 0).toFixed(2) + '%' } },
  dataLabels: { enabled: false },
}))

// ── Custo/KM manutenção por mês
const ckSeries = computed(() => [{
  name: 'R$/KM',
  data: tendencia.value.map(t => t.custo_km_man),
}])
const ckOpts = computed(() => ({
  chart: { type: 'line', background: 'transparent', fontFamily: 'Inter', toolbar: { show: false } },
  stroke: { curve: 'smooth', width: 2 },
  colors: ['#10b981'],
  markers: { size: 3, colors: ['#10b981'], strokeColors: '#fff', strokeWidth: 2 },
  xaxis: { categories: tendencia.value.map(t => fmtMes(t.ano_mes)), labels: { style: { colors: '#94a3b8', fontSize: '10px' } } },
  yaxis: { labels: { formatter: (v) => 'R$ ' + (v || 0).toFixed(4), style: { colors: '#94a3b8', fontSize: '10px' } } },
  grid: { borderColor: '#e2e8f0' },
  tooltip: { y: { formatter: (v) => fmt4(v) } },
  dataLabels: { enabled: false },
}))

const loadAll = async () => {
  const p = {}
  if (filtroMes.value)    p.ano_mes = filtroMes.value
  if (filtroFilial.value) p.filial  = filtroFilial.value

  lKpis.value = lRanking.value = true
  Promise.all([
    fetchManutencaoKpisEstrategicos(p).then(d => { kpis.value = d; lKpis.value = false }).catch(() => lKpis.value = false),
    fetchManutencaoRankingFiliais({ ano_mes: p.ano_mes }).then(d => { ranking.value = d; lRanking.value = false }).catch(() => lRanking.value = false),
  ])
}

const init = async () => {
  const f = await fetchManutencaoFiltros()
  meses.value   = f.meses   || []
  filiais.value = f.filiais || []
  if (f.meses.length) filtroMes.value = f.meses[0]

  lTendencia.value = true
  fetchManutencaoTendencia({ filial: filtroFilial.value || undefined })
    .then(d => { tendencia.value = d; lTendencia.value = false })
    .catch(() => lTendencia.value = false)

  await loadAll()
}

onMounted(init)
</script>

<style scoped>
.page { min-height: 100vh; background: var(--void); }
.topbar { background: white; border-bottom: 1px solid #e2e8f0; position: sticky; top: 0; z-index: 1000; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
.topbar-main { display: flex; align-items: center; justify-content: space-between; padding: 0 32px; height: 64px; gap: 24px; }
.topbar-left { flex-shrink: 0; }
.logo { font-size: 16px; font-weight: 800; letter-spacing: 0.05em; color: #0f172a; display: flex; align-items: center; white-space: nowrap; }
.logo .divider { color: #C41230; margin: 0 12px; font-weight: 400; opacity: 0.5; }
.title-group { display: flex; flex-direction: column; line-height: 1.2; }
.logo .subtitle { color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
.page-subtitle { color: #94a3b8; font-size: 10px; font-weight: 500; }
.topbar-center { flex: 1; display: flex; justify-content: center; }
.topbar-right { flex-shrink: 0; min-width: 80px; }
.fkm-filters { display: flex; gap: 12px; align-items: flex-end; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 8px 12px; }
.filter-group { display: flex; flex-direction: column; gap: 3px; }
.filter-group label { font-size: 9px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
.filter-group select { background: white; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; font-weight: 600; color: #1e293b; padding: 5px 10px; outline: none; cursor: pointer; min-width: 120px; }
.filter-group select:focus { border-color: #C41230; }

.page-body { padding: 24px 32px; display: flex; flex-direction: column; gap: 20px; max-width: 1600px; }
.kpi-pro-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.section-heading { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 16px; }
.section-heading-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.section-heading-row .section-heading { margin-bottom: 0; }

.legend-flags { display: flex; gap: 8px; }
.flag { display: inline-flex; align-items: center; justify-content: center; padding: 2px 8px; border-radius: 5px; font-size: 10px; font-weight: 800; letter-spacing: 0.04em; }
.flag-alto   { background: #fee2e2; color: #991b1b; }
.flag-normal { background: #f1f5f9; color: #475569; }
.flag-baixo  { background: #d1fae5; color: #065f46; }

.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.data-table th { background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 8px 12px; font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }
.data-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; color: #1e293b; white-space: nowrap; }
.data-table tbody tr:hover { background: #fafafa; }
.data-table tfoot td { background: #f8fafc; border-top: 2px solid #e2e8f0; padding: 10px 12px; }
.tfoot-label { color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
.tfoot-val { font-family: 'JetBrains Mono', monospace; font-weight: 800; color: #0f172a; }

.right  { text-align: right; }
.center { text-align: center; }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; }
.fw-bold { font-weight: 700; }
.idx { color: #94a3b8; font-size: 11px; width: 28px; }
.filial-cell { color: #475569; }

.text-red    { color: #dc2626; font-weight: 700; }
.text-yellow { color: #d97706; font-weight: 600; }
.text-green  { color: #059669; font-weight: 600; }
.text-muted  { color: #94a3b8; }

.empty { text-align: center; color: #94a3b8; font-size: 13px; padding: 40px 0; }
.skel { background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; }
.kpi-skel { height: 120px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

@media (max-width: 1200px) { .two-col { grid-template-columns: 1fr; } .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .page-body { padding: 16px; } .kpi-pro-grid { grid-template-columns: 1fr; } .topbar-main { flex-wrap: wrap; height: auto; padding: 12px 16px; } }
</style>
