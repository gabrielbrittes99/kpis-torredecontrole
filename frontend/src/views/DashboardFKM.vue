<template>
  <div class="page">
    <!-- ━━━━━ TOPBAR ━━━━━ -->
    <header class="topbar">
      <div class="topbar-main">
        <div class="topbar-left">
          <span class="logo">
            GRITSCH <span class="divider">//</span>
            <div class="title-group">
              <span class="subtitle">FKM · Fechamento Mensal</span>
              <span class="page-subtitle">Custo total da frota — combustível + manutenção + km rodado</span>
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

        <div class="topbar-right">
          <button class="btn-refresh" @click="refreshCache" :disabled="refreshing">
            {{ refreshing ? 'Atualizando...' : 'Recarregar Planilha' }}
          </button>
        </div>
      </div>
    </header>

    <div class="page-body">

      <!-- ━━━━━ SEÇÃO 1: KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Indicadores · {{ fmtMes(filtroMes) }}</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            title="Custo Total da Frota"
            :value="kpis.total_geral || 0"
            format="currency"
            theme="primary"
            :description="`${fmtN(kpis.qtd_veiculos)} veículos · ${fmtN(kpis.qtd_filiais)} filiais`"
          />
          <KpiCardPro
            title="Custo / KM Total"
            :value="kpis.custo_km_total || 0"
            format="currency"
            :decimals="4"
            :description="`Comb: R$ ${fmt4(kpis.custo_km_combustivel)} / km · Man: R$ ${fmt4(kpis.custo_km_manutencao)} / km`"
          />
          <KpiCardPro
            title="Total KM Rodado"
            :value="kpis.total_km || 0"
            format="number"
            unit="km"
            :description="`Média: ${fmtN(Math.round((kpis.total_km || 0) / Math.max(kpis.qtd_veiculos || 1, 1)))} km/veículo`"
          />
          <KpiCardPro
            title="Eficiência Média"
            :value="kpis.media_kml || 0"
            format="number"
            :decimals="2"
            unit="km/L"
            :description="`${fmtN(kpis.total_litros)} litros · ${fmtR(kpis.total_combustivel)} em combustível`"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>

        <!-- Sub-KPIs: categorias -->
        <div class="cat-kpis" v-if="!lKpis && kpis.total_geral">
          <div class="cat-kpi">
            <span class="cat-label">Combustível</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_combustivel) }}</span>
            <span class="cat-pct">{{ kpis.pct_combustivel }}%</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Manutenção Geral</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_geral_manutencao) }}</span>
            <span class="cat-pct">{{ kpis.pct_manutencao }}%</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Pneus</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_pneus) }}</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Lataria e Pintura</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_lataria) }}</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Arla</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_arla) }}</span>
          </div>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 2: GRÁFICOS ━━━━━ -->
      <div class="two-col">

        <!-- Distribuição por categoria -->
        <section class="v-block">
          <div class="section-heading">Composição do Custo</div>
          <div v-if="lCategorias" class="skel" style="height:280px" />
          <div v-else-if="!categorias.length" class="empty">Sem dados</div>
          <apexchart
            v-else
            type="donut"
            height="280"
            :options="donutOptions"
            :series="donutSeries"
          />
        </section>

        <!-- Evolução mensal -->
        <section class="v-block">
          <div class="section-heading">Evolução Mensal</div>
          <div v-if="lEvolucao" class="skel" style="height:280px" />
          <div v-else-if="!evolucao.length" class="empty">Sem dados históricos</div>
          <apexchart
            v-else
            type="line"
            height="280"
            :options="lineOptions"
            :series="lineSeries"
          />
        </section>
      </div>

      <!-- ━━━━━ SEÇÃO 3: RESUMO POR FILIAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Resumo por Filial · {{ fmtMes(filtroMes) }}</div>
        <div v-if="lFilial" class="skel" style="height:260px" />
        <div v-else-if="!porFilial.length" class="empty">Sem dados por filial</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Filial</th>
                <th class="right">KM Rodado</th>
                <th class="right">Combustível</th>
                <th class="right">Man. Geral</th>
                <th class="right">Pneus</th>
                <th class="right">Lataria</th>
                <th class="right">Total</th>
                <th class="right">Custo/KM</th>
                <th class="right">km/L</th>
                <th class="right">Veículos</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in porFilial" :key="row.filial">
                <td class="filial-cell">{{ row.filial }}</td>
                <td class="right mono">{{ fmtN(row.total_km) }}</td>
                <td class="right mono">{{ fmtR(row.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(row.total_geral_manutencao) }}</td>
                <td class="right mono">{{ fmtR(row.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(row.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(row.total_geral) }}</td>
                <td class="right mono" :class="custoKmClass(row.custo_km)">{{ fmt4(row.custo_km) }}</td>
                <td class="right mono">{{ row.media_kml ? row.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ row.qtd_veiculos }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td>TOTAL</td>
                <td class="right mono">{{ fmtN(kpis.total_km) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_geral_manutencao) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(kpis.total_geral) }}</td>
                <td class="right mono">{{ fmt4(kpis.custo_km_total) }}</td>
                <td class="right mono">{{ kpis.media_kml ? kpis.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ kpis.qtd_veiculos }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 4: TOP VEÍCULOS (TCO) ━━━━━ -->
      <section class="v-block">
        <div class="section-heading-row">
          <div class="section-heading">Top Veículos por Custo Total · {{ fmtMes(filtroMes) }}</div>
          <span class="section-badge">{{ veiculos.length }} veículos</span>
        </div>
        <div v-if="lVeiculos" class="skel" style="height:260px" />
        <div v-else-if="!veiculos.length" class="empty">Sem dados de veículos</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Placa</th>
                <th>Modelo</th>
                <th>Grupo</th>
                <th>Filial</th>
                <th>Motorista</th>
                <th class="right">KM</th>
                <th class="right">Combustível</th>
                <th class="right">Manutenção</th>
                <th class="right">Pneus</th>
                <th class="right">Total</th>
                <th class="right">Custo/KM</th>
                <th class="right">km/L</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(v, idx) in veiculos" :key="v.placa">
                <td class="idx-cell mono">{{ idx + 1 }}</td>
                <td class="placa-cell mono">{{ v.placa }}</td>
                <td>{{ v.modelo || '—' }}</td>
                <td><span class="grupo-badge" :class="grupoBadgeClass(v.grupo)">{{ v.grupo || '—' }}</span></td>
                <td class="filial-cell">{{ v.filial || '—' }}</td>
                <td>{{ v.motorista || '—' }}</td>
                <td class="right mono">{{ fmtN(v.total_km) }}</td>
                <td class="right mono">{{ fmtR(v.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(v.total_manutencao) }}</td>
                <td class="right mono">{{ fmtR(v.total_pneus) }}</td>
                <td class="right mono fw-bold">{{ fmtR(v.total_geral) }}</td>
                <td class="right mono" :class="custoKmClass(v.custo_km)">{{ fmt4(v.custo_km) }}</td>
                <td class="right mono">{{ v.media_kml ? v.media_kml.toFixed(2) : '—' }}</td>
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
  fetchFkmFiltros,
  fetchFkmKpis,
  fetchFkmResumoPorFilial,
  fetchFkmCustoPorVeiculo,
  fetchFkmEvolucaoMensal,
  fetchFkmDistribuicaoCategorias,
} from '../api/fkm.js'

// ── Estado ────────────────────────────────────────────────────────────────
const filtros   = ref({ meses: [], filiais: [], grupos: [], combustiveis: [] })
const filtroMes = ref('')
const filtroFilial = ref('')
const filtroGrupo  = ref('')

const kpis      = ref({})
const categorias = ref([])
const evolucao  = ref([])
const porFilial = ref([])
const veiculos  = ref([])

const lKpis      = ref(true)
const lCategorias = ref(true)
const lEvolucao  = ref(true)
const lFilial    = ref(true)
const lVeiculos  = ref(true)
const refreshing = ref(false)

// ── Formatadores ──────────────────────────────────────────────────────────
const fmtR = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtN = (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
const fmt4 = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })

const fmtMes = (ym) => {
  if (!ym) return '—'
  const [ano, mes] = ym.split('-')
  const nomes = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  return `${nomes[parseInt(mes)]}/${ano}`
}

const custoKmClass = (v) => {
  if (v == null) return ''
  if (v > 1.5) return 'text-red'
  if (v > 1.0) return 'text-yellow'
  return 'text-green'
}

const grupoBadgeClass = (g) => {
  if (!g) return ''
  const lower = g.toLowerCase()
  if (lower.includes('caminhão') || lower.includes('caminhao')) return 'badge-truck'
  if (lower.includes('pesado')) return 'badge-heavy'
  if (lower.includes('médio') || lower.includes('medio')) return 'badge-medium'
  return 'badge-light'
}

// ── Gráfico Donut ─────────────────────────────────────────────────────────
const donutSeries  = computed(() => categorias.value.map(c => c.valor))
const donutOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent', fontFamily: 'Inter' },
  labels: categorias.value.map(c => c.categoria),
  colors: ['#C41230', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'],
  legend: { position: 'bottom', fontSize: '12px', labels: { colors: '#475569' } },
  dataLabels: { enabled: true, formatter: (val) => val.toFixed(1) + '%', style: { fontSize: '11px' } },
  plotOptions: { pie: { donut: { size: '60%', labels: { show: true, total: { show: true, label: 'Total', formatter: () => fmtR(kpis.value.total_geral) } } } } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
}))

// ── Gráfico Linha ──────────────────────────────────────────────────────────
const lineSeries = computed(() => [
  { name: 'Total Geral', data: evolucao.value.map(e => e.total_geral) },
  { name: 'Combustível', data: evolucao.value.map(e => e.total_combustivel) },
  { name: 'Manutenção', data: evolucao.value.map(e => e.total_manutencao) },
])
const lineOptions = computed(() => ({
  chart: { type: 'line', background: 'transparent', fontFamily: 'Inter', toolbar: { show: false } },
  colors: ['#C41230', '#3b82f6', '#10b981'],
  stroke: { curve: 'smooth', width: [2.5, 2, 2] },
  xaxis: { categories: evolucao.value.map(e => fmtMes(e.ano_mes)), labels: { style: { colors: '#94a3b8', fontSize: '11px' } } },
  yaxis: { labels: { formatter: (v) => 'R$ ' + (v / 1000).toFixed(0) + 'k', style: { colors: '#94a3b8', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  legend: { position: 'top', fontSize: '12px', labels: { colors: '#475569' } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
}))

// ── Carga de dados ────────────────────────────────────────────────────────
const params = () => {
  const p = {}
  if (filtroMes.value)    p.ano_mes = filtroMes.value
  if (filtroFilial.value) p.filial  = filtroFilial.value
  if (filtroGrupo.value)  p.grupo   = filtroGrupo.value
  return p
}

const loadAll = async () => {
  const p = params()
  lKpis.value = lCategorias.value = lFilial.value = lVeiculos.value = true

  Promise.all([
    fetchFkmKpis(p).then(d => { kpis.value = d; lKpis.value = false }).catch(() => lKpis.value = false),
    fetchFkmDistribuicaoCategorias(p).then(d => { categorias.value = d; lCategorias.value = false }).catch(() => lCategorias.value = false),
    fetchFkmResumoPorFilial(p).then(d => { porFilial.value = d; lFilial.value = false }).catch(() => lFilial.value = false),
    fetchFkmCustoPorVeiculo({ ...p, limit: 50 }).then(d => { veiculos.value = d; lVeiculos.value = false }).catch(() => lVeiculos.value = false),
  ])
}

const loadEvolucao = async () => {
  lEvolucao.value = true
  const p = {}
  if (filtroFilial.value) p.filial = filtroFilial.value
  if (filtroGrupo.value)  p.grupo  = filtroGrupo.value
  fetchFkmEvolucaoMensal(p)
    .then(d => { evolucao.value = d; lEvolucao.value = false })
    .catch(() => lEvolucao.value = false)
}

const refreshCache = async () => {
  refreshing.value = true
  try {
    await fetch(`${import.meta.env.VITE_API_URL}/api/fkm/cache/refresh`, { method: 'POST' })
    await init()
  } finally {
    refreshing.value = false
  }
}

const init = async () => {
  const f = await fetchFkmFiltros()
  filtros.value = f
  if (f.meses.length && !filtroMes.value) filtroMes.value = f.meses[0]
  await Promise.all([loadAll(), loadEvolucao()])
}

onMounted(init)
</script>

<style scoped>
.page { min-height: 100vh; background: var(--void); }

/* ── Topbar ── */
.topbar {
  background: white; border-bottom: 1px solid #e2e8f0;
  position: sticky; top: 0; z-index: 1000;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.topbar-main {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 32px; height: 64px; gap: 24px;
}
.topbar-left { flex-shrink: 0; }
.logo { font-size: 16px; font-weight: 800; letter-spacing: 0.05em; color: #0f172a; display: flex; align-items: center; white-space: nowrap; }
.logo .divider { color: #C41230; margin: 0 12px; font-weight: 400; opacity: 0.5; }
.title-group { display: flex; flex-direction: column; line-height: 1.2; }
.logo .subtitle { color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
.page-subtitle { color: #94a3b8; font-size: 10px; font-weight: 500; }
.topbar-center { flex: 1; display: flex; justify-content: center; }
.topbar-right { flex-shrink: 0; }

.fkm-filters { display: flex; gap: 12px; align-items: flex-end; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 8px 12px; }
.filter-group { display: flex; flex-direction: column; gap: 3px; }
.filter-group label { font-size: 9px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
.filter-group select {
  background: white; border: 1px solid #e2e8f0; border-radius: 6px;
  font-size: 12px; font-weight: 600; color: #1e293b; padding: 5px 10px; outline: none; cursor: pointer;
  min-width: 130px;
}
.filter-group select:focus { border-color: #C41230; }

.btn-refresh {
  background: white; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 8px 16px; font-size: 12px; font-weight: 700; color: #475569;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.btn-refresh:hover:not(:disabled) { border-color: #C41230; color: #C41230; }
.btn-refresh:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── Page body ── */
.page-body {
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1600px;
}

/* ── KPI grid ── */
.kpi-pro-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

/* ── Sub KPIs de categoria ── */
.cat-kpis {
  display: flex; gap: 0; border-top: 1px solid #e2e8f0; padding-top: 16px;
  flex-wrap: wrap;
}
.cat-kpi {
  flex: 1; min-width: 120px;
  display: flex; flex-direction: column; gap: 3px;
  padding: 0 20px 0 0;
  border-right: 1px solid #f1f5f9;
}
.cat-kpi:last-child { border-right: none; }
.cat-label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.cat-value { font-size: 14px; font-weight: 700; color: #0f172a; font-family: 'JetBrains Mono', monospace; }
.cat-pct { font-size: 11px; font-weight: 600; color: #C41230; }

/* ── Two col ── */
.two-col { display: grid; grid-template-columns: 1fr 1.6fr; gap: 20px; }

/* ── Section heading ── */
.section-heading {
  font-size: 12px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: 16px;
}
.section-heading-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-heading-row .section-heading { margin-bottom: 0; }
.section-badge {
  background: #f1f5f9; border-radius: 6px; padding: 2px 8px;
  font-size: 11px; font-weight: 700; color: #64748b;
}

/* ── Table ── */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.data-table th {
  background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 8px 12px;
  font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;
  white-space: nowrap;
}
.data-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; color: #1e293b; white-space: nowrap; }
.data-table tbody tr:hover { background: #fafafa; }
.data-table tfoot tr { background: #f8fafc; }
.data-table tfoot td { padding: 10px 12px; font-weight: 700; font-size: 12px; border-top: 2px solid #e2e8f0; }
.right { text-align: right; }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; }
.fw-bold { font-weight: 700; }

.idx-cell { color: #94a3b8; font-size: 11px; width: 32px; }
.placa-cell { font-weight: 700; color: #0f172a; letter-spacing: 0.05em; }
.filial-cell { color: #475569; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }

.text-red { color: #dc2626; font-weight: 700; }
.text-yellow { color: #d97706; font-weight: 600; }
.text-green { color: #059669; }

/* Grupo badges */
.grupo-badge { display: inline-block; padding: 2px 7px; border-radius: 5px; font-size: 10px; font-weight: 700; }
.badge-truck   { background: #fef3c7; color: #92400e; }
.badge-heavy   { background: #fee2e2; color: #991b1b; }
.badge-medium  { background: #dbeafe; color: #1e40af; }
.badge-light   { background: #d1fae5; color: #065f46; }

/* ── Utilitários ── */
.empty { text-align: center; color: #94a3b8; font-size: 13px; padding: 40px 0; }
.skel { background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; }
.kpi-skel { height: 120px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

@media (max-width: 1200px) {
  .two-col { grid-template-columns: 1fr; }
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .page-body { padding: 16px; }
  .kpi-pro-grid { grid-template-columns: 1fr; }
  .fkm-filters { flex-wrap: wrap; }
  .topbar-main { flex-wrap: wrap; height: auto; padding: 12px 16px; gap: 12px; }
}
</style>
