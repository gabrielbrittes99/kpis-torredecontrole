<template>
  <div class="page">
    <header class="topbar">
      <div class="topbar-main">
        <div class="topbar-left">
          <span class="logo">
            GRITSCH <span class="divider">//</span>
            <div class="title-group">
              <span class="subtitle">Manutenção · Visão Geral</span>
              <span class="page-subtitle">Custos de manutenção, pneus e lataria — consolidado frota</span>
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
        <div class="section-heading">Indicadores · {{ fmtMes(filtroMes) }}</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            title="Total Manutenção Geral"
            :value="kpis.total_geral || 0"
            format="currency"
            theme="primary"
            :trendValue="kpis.var_total_pct"
            :trendInvert="true"
            :description="`vs ${fmtMes(kpis.ano_mes_ant)}: ${fmtR(kpis.total_geral_ant)}`"
          />
          <KpiCardPro
            title="Custo / KM Manutenção"
            :value="kpis.custo_km || 0"
            format="currency"
            :decimals="4"
            :description="`${fmtN(kpis.total_km)} km rodados · ${kpis.qtd_veiculos} veículos`"
          />
          <KpiCardPro
            title="Custo Médio / Veículo"
            :value="kpis.custo_veiculo || 0"
            format="currency"
            :description="`${kpis.qtd_veiculos} veículos com manutenção no mês`"
          />
          <KpiCardPro
            title="Manutenção (03.03)"
            :value="kpis.total_manutencao || 0"
            format="currency"
            :description="`${kpis.pct_manutencao}% do total · Peças + MO`"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>

        <!-- Sub-KPIs categorias -->
        <div class="cat-kpis" v-if="!lKpis && kpis.total_geral">
          <div class="cat-kpi">
            <span class="cat-dot" style="background:#C41230"></span>
            <div>
              <span class="cat-label">Manutenção (03.03)</span>
              <span class="cat-value mono">{{ fmtR(kpis.total_manutencao) }}</span>
              <span class="cat-pct">{{ kpis.pct_manutencao }}%</span>
            </div>
          </div>
          <div class="cat-kpi">
            <span class="cat-dot" style="background:#3b82f6"></span>
            <div>
              <span class="cat-label">Pneus (03.05)</span>
              <span class="cat-value mono">{{ fmtR(kpis.total_pneus) }}</span>
              <span class="cat-pct">{{ kpis.pct_pneus }}%</span>
            </div>
          </div>
          <div class="cat-kpi">
            <span class="cat-dot" style="background:#10b981"></span>
            <div>
              <span class="cat-label">Lataria e Pintura (03.02)</span>
              <span class="cat-value mono">{{ fmtR(kpis.total_lataria) }}</span>
              <span class="cat-pct">{{ kpis.pct_lataria }}%</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ━━━━━ GRÁFICOS ━━━━━ -->
      <div class="two-col">
        <section class="v-block">
          <div class="section-heading">Composição do Custo</div>
          <div v-if="lKpis" class="skel" style="height:260px" />
          <div v-else-if="!kpis.total_geral" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="260" :options="donutOptions" :series="donutSeries" />
        </section>

        <section class="v-block">
          <div class="section-heading">Evolução Mensal</div>
          <div v-if="lEvolucao" class="skel" style="height:260px" />
          <div v-else-if="!evolucao.length" class="empty">Sem dados</div>
          <apexchart v-else type="bar" height="260" :options="barOptions" :series="barSeries" />
        </section>
      </div>

      <!-- ━━━━━ TOP VEÍCULOS ━━━━━ -->
      <section class="v-block">
        <div class="section-heading-row">
          <div class="section-heading">Top Veículos por Custo de Manutenção · {{ fmtMes(filtroMes) }}</div>
          <span class="section-badge">{{ topVeiculos.length }} veículos</span>
        </div>
        <div v-if="lVeiculos" class="skel" style="height:240px" />
        <div v-else-if="!topVeiculos.length" class="empty">Sem dados</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th><th>Placa</th><th>Modelo</th><th>Grupo</th><th>Filial</th><th>Motorista</th>
                <th class="right">Manutenção</th><th class="right">Pneus</th><th class="right">Lataria</th>
                <th class="right">Total</th><th class="right">KM</th><th class="right">Custo/KM</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(v, i) in topVeiculos" :key="v.placa">
                <td class="idx">{{ i + 1 }}</td>
                <td class="placa mono">{{ v.placa }}</td>
                <td>{{ v.modelo || '—' }}</td>
                <td><span class="grupo-badge" :class="gbClass(v.grupo)">{{ v.grupo || '—' }}</span></td>
                <td class="filial-cell">{{ v.filial || '—' }}</td>
                <td>{{ v.motorista || '—' }}</td>
                <td class="right mono">{{ fmtR(v.total_manutencao) }}</td>
                <td class="right mono">{{ fmtR(v.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(v.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(v.total_geral) }}</td>
                <td class="right mono">{{ fmtN(v.total_km) }}</td>
                <td class="right mono" :class="ckClass(v.custo_km)">{{ fmt4(v.custo_km) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ━━━━━ TOP FORNECEDORES ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Top Fornecedores (SQL Server — histórico completo)</div>
        <div v-if="lForn" class="skel" style="height:160px" />
        <div v-else-if="!topForn.length" class="empty">Sem dados de fornecedores</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th><th>Fornecedor</th><th class="right">Total Gasto</th><th class="right">Qtd OS</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(f, i) in topForn" :key="f.fornecedor">
                <td class="idx">{{ i + 1 }}</td>
                <td>{{ f.fornecedor || '—' }}</td>
                <td class="right mono fw-bold">{{ fmtR(f.total_valor) }}</td>
                <td class="right mono">{{ f.qtd_os }}</td>
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
  fetchManutencaoFiltros, fetchManutencaoKpis, fetchManutencaoEvolucaoMensal,
  fetchManutencaoTopVeiculos, fetchManutencaoTopFornecedores,
} from '../api/manutencao.js'

const filtros     = ref({ meses: [], filiais: [], grupos: [] })
const filtroMes   = ref('')
const filtroFilial = ref('')
const filtroGrupo  = ref('')

const kpis       = ref({})
const evolucao   = ref([])
const topVeiculos = ref([])
const topForn    = ref([])

const lKpis    = ref(true)
const lEvolucao = ref(true)
const lVeiculos = ref(true)
const lForn    = ref(true)

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

const donutSeries  = computed(() => [kpis.value.total_manutencao || 0, kpis.value.total_pneus || 0, kpis.value.total_lataria || 0])
const donutOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent', fontFamily: 'Inter' },
  labels: ['Manutenção (03.03)', 'Pneus (03.05)', 'Lataria/Pintura (03.02)'],
  colors: ['#C41230', '#3b82f6', '#10b981'],
  legend: { position: 'bottom', fontSize: '12px', labels: { colors: '#475569' } },
  dataLabels: { enabled: true, formatter: (v) => v.toFixed(1) + '%', style: { fontSize: '11px' } },
  plotOptions: { pie: { donut: { size: '60%', labels: { show: true, total: { show: true, label: 'Total', formatter: () => fmtR(kpis.value.total_geral) } } } } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
}))

const barSeries = computed(() => [
  { name: 'Manutenção', data: evolucao.value.map(e => e.total_manutencao) },
  { name: 'Pneus',      data: evolucao.value.map(e => e.total_pneus) },
  { name: 'Lataria',    data: evolucao.value.map(e => e.total_lataria) },
])
const barOptions = computed(() => ({
  chart: { type: 'bar', stacked: true, background: 'transparent', fontFamily: 'Inter', toolbar: { show: false } },
  colors: ['#C41230', '#3b82f6', '#10b981'],
  xaxis: { categories: evolucao.value.map(e => fmtMes(e.ano_mes)), labels: { style: { colors: '#94a3b8', fontSize: '11px' } } },
  yaxis: { labels: { formatter: (v) => 'R$ ' + (v / 1000).toFixed(0) + 'k', style: { colors: '#94a3b8', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  legend: { position: 'top', fontSize: '12px', labels: { colors: '#475569' } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
  plotOptions: { bar: { columnWidth: '65%' } },
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
  lKpis.value = lVeiculos.value = true
  Promise.all([
    fetchManutencaoKpis(p).then(d => { kpis.value = d; lKpis.value = false }).catch(() => lKpis.value = false),
    fetchManutencaoTopVeiculos({ ...p, limit: 30 }).then(d => { topVeiculos.value = d; lVeiculos.value = false }).catch(() => lVeiculos.value = false),
  ])
}

const init = async () => {
  const f = await fetchManutencaoFiltros()
  filtros.value = f
  if (f.meses.length) filtroMes.value = f.meses[0]

  lEvolucao.value = lForn.value = true
  Promise.all([
    fetchManutencaoEvolucaoMensal().then(d => { evolucao.value = d; lEvolucao.value = false }).catch(() => lEvolucao.value = false),
    fetchManutencaoTopFornecedores().then(d => { topForn.value = d; lForn.value = false }).catch(() => lForn.value = false),
    loadAll(),
  ])
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
.topbar-right { flex-shrink: 0; min-width: 120px; }
.fkm-filters { display: flex; gap: 12px; align-items: flex-end; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 8px 12px; }
.filter-group { display: flex; flex-direction: column; gap: 3px; }
.filter-group label { font-size: 9px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
.filter-group select { background: white; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; font-weight: 600; color: #1e293b; padding: 5px 10px; outline: none; cursor: pointer; min-width: 120px; }
.filter-group select:focus { border-color: #C41230; }

.page-body { padding: 24px 32px; display: flex; flex-direction: column; gap: 20px; max-width: 1600px; }

.kpi-pro-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }

.cat-kpis { display: flex; gap: 24px; border-top: 1px solid #e2e8f0; padding-top: 16px; flex-wrap: wrap; }
.cat-kpi { display: flex; align-items: flex-start; gap: 10px; }
.cat-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 3px; }
.cat-kpi > div { display: flex; flex-direction: column; gap: 2px; }
.cat-label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.cat-value { font-size: 15px; font-weight: 700; color: #0f172a; font-family: 'JetBrains Mono', monospace; }
.cat-pct { font-size: 11px; font-weight: 600; color: #C41230; }

.two-col { display: grid; grid-template-columns: 1fr 1.6fr; gap: 20px; }

.section-heading { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 16px; }
.section-heading-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-heading-row .section-heading { margin-bottom: 0; }
.section-badge { background: #f1f5f9; border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 700; color: #64748b; }

.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.data-table th { background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 8px 12px; font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }
.data-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; color: #1e293b; white-space: nowrap; }
.data-table tbody tr:hover { background: #fafafa; }
.right { text-align: right; }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; }
.fw-bold { font-weight: 700; }
.idx { color: #94a3b8; font-size: 11px; width: 28px; }
.placa { font-weight: 700; color: #0f172a; letter-spacing: 0.05em; }
.filial-cell { color: #475569; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }

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
@media (max-width: 768px) { .page-body { padding: 16px; } .kpi-pro-grid { grid-template-columns: 1fr; } .fkm-filters { flex-wrap: wrap; } .topbar-main { flex-wrap: wrap; height: auto; padding: 12px 16px; } }
</style>
