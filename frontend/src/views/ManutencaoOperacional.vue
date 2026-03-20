<template>
  <div class="page">
    <header class="topbar">
      <div class="topbar-main">
        <div class="topbar-left">
          <span class="logo">
            GRITSCH <span class="divider">//</span>
            <div class="title-group">
              <span class="subtitle">Manutenção · Visão Operacional</span>
              <span class="page-subtitle">Detalhamento por filial e grupo de veículo</span>
            </div>
          </span>
        </div>
        <div class="topbar-center">
          <div class="fkm-filters">
            <div class="filter-group">
              <label>Mês</label>
              <select v-model="filtroMes" @change="loadAll">
                <option v-for="m in filtros.meses" :key="m" :value="m">{{ fmtMes(m) }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Filial</label>
              <select v-model="filtroFilial" @change="loadAll">
                <option value="">Todas</option>
                <option v-for="f in filtros.filiais" :key="f" :value="f">{{ f }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Grupo</label>
              <select v-model="filtroGrupo" @change="loadAll">
                <option value="">Todos</option>
                <option v-for="g in filtros.grupos" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
          </div>
        </div>
        <div class="topbar-right"></div>
      </div>
    </header>

    <div class="page-body">

      <!-- ━━━━━ KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Resumo · {{ fmtMes(filtroMes) }}</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro title="Total Manutenção" :value="kpis.total_geral || 0" format="currency" theme="primary" :trendValue="kpis.var_total_pct" :trendInvert="true" :description="`vs ${fmtMes(kpis.ano_mes_ant)}: ${fmtR(kpis.total_geral_ant)}`" />
          <KpiCardPro title="Custo/KM Manutenção" :value="kpis.custo_km || 0" format="currency" :decimals="4" :description="`${fmtN(kpis.total_km)} km · ${kpis.qtd_veiculos} veículos`" />
          <KpiCardPro title="Filiais com Manutenção" :value="porFilial.length" format="number" :description="`de ${filtros.filiais.length} filiais ativas`" />
          <KpiCardPro title="Grupos Monitorados" :value="porGrupo.length" format="number" :description="`tipos de veículo com custo`" />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- ━━━━━ GRÁFICOS ━━━━━ -->
      <div class="two-col">
        <section class="v-block">
          <div class="section-heading">Manutenção por Grupo de Veículo</div>
          <div v-if="lGrupo" class="skel" style="height:280px" />
          <div v-else-if="!porGrupo.length" class="empty">Sem dados</div>
          <apexchart v-else type="bar" height="280" :options="grupoBarOpts" :series="grupoBarSeries" />
        </section>

        <section class="v-block">
          <div class="section-heading">Manutenção por Filial</div>
          <div v-if="lFilial" class="skel" style="height:280px" />
          <div v-else-if="!porFilial.length" class="empty">Sem dados</div>
          <apexchart v-else type="bar" height="280" :options="filialBarOpts" :series="filialBarSeries" />
        </section>
      </div>

      <!-- ━━━━━ TABELA POR FILIAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Detalhamento por Filial · {{ fmtMes(filtroMes) }}</div>
        <div v-if="lFilial" class="skel" style="height:240px" />
        <div v-else-if="!porFilial.length" class="empty">Sem dados por filial</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Filial</th>
                <th class="right">Manutenção</th><th class="right">Pneus</th><th class="right">Lataria</th>
                <th class="right">Total</th><th class="right">% Frota</th>
                <th class="right">KM</th><th class="right">Custo/KM</th><th class="right">Veículos</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in porFilial" :key="row.filial">
                <td class="filial-cell">{{ row.filial }}</td>
                <td class="right mono">{{ fmtR(row.total_manutencao) }}</td>
                <td class="right mono">{{ fmtR(row.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(row.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(row.total_geral) }}</td>
                <td class="right">
                  <div class="pct-bar-wrap">
                    <div class="pct-bar" :style="{ width: row.pct_total + '%' }"></div>
                    <span class="pct-label">{{ row.pct_total }}%</span>
                  </div>
                </td>
                <td class="right mono">{{ fmtN(row.total_km) }}</td>
                <td class="right mono" :class="ckClass(row.custo_km)">{{ fmt4(row.custo_km) }}</td>
                <td class="right mono">{{ row.qtd_veiculos }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ━━━━━ TABELA POR GRUPO ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Detalhamento por Grupo de Veículo · {{ fmtMes(filtroMes) }}</div>
        <div v-if="lGrupo" class="skel" style="height:200px" />
        <div v-else-if="!porGrupo.length" class="empty">Sem dados por grupo</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Grupo</th>
                <th class="right">Manutenção</th><th class="right">Pneus</th><th class="right">Lataria</th>
                <th class="right">Total</th><th class="right">% Total</th>
                <th class="right">KM</th><th class="right">Custo/KM</th><th class="right">Veículos</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in porGrupo" :key="row.grupo">
                <td><span class="grupo-badge" :class="gbClass(row.grupo)">{{ row.grupo }}</span></td>
                <td class="right mono">{{ fmtR(row.total_manutencao) }}</td>
                <td class="right mono">{{ fmtR(row.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(row.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(row.total_geral) }}</td>
                <td class="right mono">{{ row.pct_total }}%</td>
                <td class="right mono">{{ fmtN(row.total_km) }}</td>
                <td class="right mono" :class="ckClass(row.custo_km)">{{ fmt4(row.custo_km) }}</td>
                <td class="right mono">{{ row.qtd_veiculos }}</td>
              </tr>
            </tbody>
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
  fetchManutencaoFiltros, fetchManutencaoKpis,
  fetchManutencaoPorFilial, fetchManutencaoPorGrupo,
} from '../api/manutencao.js'

const filtros     = ref({ meses: [], filiais: [], grupos: [] })
const filtroMes   = ref('')
const filtroFilial = ref('')
const filtroGrupo  = ref('')

const kpis     = ref({})
const porFilial = ref([])
const porGrupo  = ref([])

const lKpis   = ref(true)
const lFilial = ref(true)
const lGrupo  = ref(true)

const fmtR = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtN = (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
const fmt4 = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
const fmtMes = (ym) => {
  if (!ym) return '—'
  const [ano, mes] = ym.split('-')
  const n = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  return `${n[parseInt(mes)]}/${ano}`
}
const ckClass = (v) => v == null ? '' : v > 0.5 ? 'text-red' : v > 0.3 ? 'text-yellow' : 'text-green'
const gbClass = (g) => {
  if (!g) return ''
  const l = g.toLowerCase()
  if (l.includes('caminhão') || l.includes('caminhao')) return 'badge-truck'
  if (l.includes('pesado')) return 'badge-heavy'
  if (l.includes('médio') || l.includes('medio')) return 'badge-medium'
  return 'badge-light'
}

// Gráfico — por grupo (horizontal)
const grupoBarSeries  = computed(() => [{ name: 'Total Manutenção', data: porGrupo.value.map(g => g.total_geral) }])
const grupoBarOpts    = computed(() => ({
  chart: { type: 'bar', background: 'transparent', fontFamily: 'Inter', toolbar: { show: false } },
  plotOptions: { bar: { horizontal: true, barHeight: '60%' } },
  colors: ['#C41230'],
  xaxis: { labels: { formatter: (v) => 'R$ ' + (v / 1000).toFixed(0) + 'k', style: { colors: '#94a3b8', fontSize: '10px' } } },
  yaxis: { categories: porGrupo.value.map(g => g.grupo), labels: { style: { colors: '#475569', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
  dataLabels: { enabled: false },
}))

// Gráfico — por filial (horizontal, top 10)
const filialTop       = computed(() => porFilial.value.slice(0, 10))
const filialBarSeries = computed(() => [
  { name: 'Manutenção', data: filialTop.value.map(f => f.total_manutencao) },
  { name: 'Pneus',      data: filialTop.value.map(f => f.total_pneus) },
  { name: 'Lataria',    data: filialTop.value.map(f => f.total_lataria) },
])
const filialBarOpts   = computed(() => ({
  chart: { type: 'bar', stacked: true, background: 'transparent', fontFamily: 'Inter', toolbar: { show: false } },
  plotOptions: { bar: { horizontal: true, barHeight: '60%' } },
  colors: ['#C41230', '#3b82f6', '#10b981'],
  xaxis: { labels: { formatter: (v) => 'R$ ' + (v / 1000).toFixed(0) + 'k', style: { colors: '#94a3b8', fontSize: '10px' } } },
  yaxis: { categories: filialTop.value.map(f => f.filial.replace('Gritsch ', '')), labels: { style: { colors: '#475569', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  legend: { position: 'top', fontSize: '11px', labels: { colors: '#475569' } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
  dataLabels: { enabled: false },
}))

const params = () => {
  const p = {}
  if (filtroMes.value)    p.ano_mes = filtroMes.value
  if (filtroFilial.value) p.filial  = filtroFilial.value
  if (filtroGrupo.value)  p.grupo   = filtroGrupo.value
  return p
}

const loadAll = async () => {
  const p = params()
  lKpis.value = lFilial.value = lGrupo.value = true
  Promise.all([
    fetchManutencaoKpis(p).then(d => { kpis.value = d; lKpis.value = false }).catch(() => lKpis.value = false),
    fetchManutencaoPorFilial({ ano_mes: p.ano_mes, grupo: p.grupo }).then(d => { porFilial.value = d; lFilial.value = false }).catch(() => lFilial.value = false),
    fetchManutencaoPorGrupo({ ano_mes: p.ano_mes, filial: p.filial }).then(d => { porGrupo.value = d; lGrupo.value = false }).catch(() => lGrupo.value = false),
  ])
}

const init = async () => {
  const f = await fetchManutencaoFiltros()
  filtros.value = f
  if (f.meses.length) filtroMes.value = f.meses[0]
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
.two-col { display: grid; grid-template-columns: 1fr 1.4fr; gap: 20px; }

.section-heading { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 16px; }

.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.data-table th { background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 8px 12px; font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }
.data-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; color: #1e293b; white-space: nowrap; }
.data-table tbody tr:hover { background: #fafafa; }
.right { text-align: right; }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; }
.fw-bold { font-weight: 700; }
.filial-cell { color: #475569; max-width: 200px; }

.pct-bar-wrap { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
.pct-bar { height: 6px; background: #C41230; border-radius: 3px; min-width: 2px; max-width: 80px; opacity: 0.7; }
.pct-label { font-size: 11px; font-weight: 600; color: #64748b; min-width: 36px; text-align: right; font-family: 'JetBrains Mono', monospace; }

.text-red { color: #dc2626; font-weight: 700; }
.text-yellow { color: #d97706; font-weight: 600; }
.text-green { color: #059669; }

.grupo-badge { display: inline-block; padding: 2px 7px; border-radius: 5px; font-size: 10px; font-weight: 700; }
.badge-truck  { background: #fef3c7; color: #92400e; }
.badge-heavy  { background: #fee2e2; color: #991b1b; }
.badge-medium { background: #dbeafe; color: #1e40af; }
.badge-light  { background: #d1fae5; color: #065f46; }

.empty { text-align: center; color: #94a3b8; font-size: 13px; padding: 40px 0; }
.skel { background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; }
.kpi-skel { height: 120px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

@media (max-width: 1200px) { .two-col { grid-template-columns: 1fr; } .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
