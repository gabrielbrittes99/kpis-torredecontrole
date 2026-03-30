<template>
  <div class="page">
    <!-- TOPBAR -->
    <header class="topbar">
      <div class="topbar-main">
        <div class="topbar-left">
          <span class="logo">
            GRITSCH <span class="divider">//</span>
            <div class="title-group">
              <span class="subtitle">Gestão de Pneus</span>
              <span class="page-subtitle">Controle e análise de pneus da frota</span>
            </div>
          </span>
        </div>

        <div class="topbar-center">
          <div class="filters">
                        <div class="filter-group">
              <label>Ano</label>
              <select v-model="filtroAno" @change="loadAll">
                <option value="">Todos</option>
                <option v-for="a in filtros.anos" :key="a" :value="a">{{ a }}</option>
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
              <label>Marca</label>
              <select v-model="filtroMarca" @change="loadAll">
                <option value="">Todas</option>
                <option v-for="m in filtros.marcas" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Fornecedor</label>
              <select v-model="filtroFornecedor" @change="loadAll">
                <option value="">Todos</option>
                <option v-for="f in filtros.fornecedores" :key="f" :value="f">{{ f }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Aro</label>
              <select v-model="filtroAro" @change="loadAll">
                <option value="">Todos</option>
                <option v-for="a in filtros.aros" :key="a" :value="a">{{ a }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Medida</label>
              <select v-model="filtroMedida" @change="loadAll">
                <option value="">Todas</option>
                <option v-for="m in filtros.medidas" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="page-body">

      <!-- SEÇÃO 1: KPIs -->
      <section class="v-block">
        <div class="section-heading">Indicadores Principais</div>
        <div class="kpi-grid" v-if="!lKpis">
          <div class="kpi-card">
            <div class="kpi-label">Total de Pneus</div>
            <div class="kpi-value">{{ kpis.total_pneus || 0 }}</div>
            <div class="kpi-sub">{{ kpis.placas || 0 }} placas</div>
          </div>
          <div class="kpi-card primary">
            <div class="kpi-label">Investimento Total</div>
            <div class="kpi-value">{{ fmtR(kpis.total_valor) }}</div>
            <div class="kpi-sub">Média: {{ fmtR(kpis.valor_medio) }}/pneu</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Pneus Novos</div>
            <div class="kpi-value">{{ kpis.novos || 0 }}</div>
            <div class="kpi-sub">{{ kpis.recapados || 0 }} recapados</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Fornecedores</div>
            <div class="kpi-value">{{ kpis.fornecedores || 0 }}</div>
            <div class="kpi-sub">{{ kpis.marcas || 0 }} marcas</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Ticket Pneus</div>
            <div class="kpi-value">{{ fmtR(kpis.ticket_medio_pneu) }}</div>
            <div class="kpi-sub">Preço médio por pneu</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Ticket Médio Veículos</div>
            <div class="kpi-value">{{ fmtR(kpis.ticket_medio_veiculo) }}</div>
            <div class="kpi-sub">Gasto médio por veículo</div>
          </div>
        </div>
        <div v-else class="kpi-grid">
          <div v-for="i in 6" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- SEÇÃO 2: GRÁFICOS PRINCIPAIS -->
      <div class="two-col">
        <!-- Tipo: Novo vs Recap -->
        <section class="v-block">
          <div class="section-heading">Tipo de Pneu</div>
          <div v-if="lTipo" class="skel" style="height:280px" />
          <div v-else-if="!porTipo.length" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="280" :options="donutTipoOptions" :series="donutTipoSeries" />
        </section>

        <!-- Distribuição por Marca -->
        <section class="v-block">
          <div class="section-heading">Investimento por Marca</div>
          <div v-if="lMarca" class="skel" style="height:280px" />
          <div v-else-if="!porMarca.length" class="empty">Sem dados</div>
          <apexchart v-else type="bar" height="280" :options="barMarcaOptions" :series="barMarcaSeries" />
        </section>
      </div>

      <!-- SEÇÃO 3: FORNECEDOR E EIXO -->
      <div class="two-col">
        <!-- Distribuição por Fornecedor -->
        <section class="v-block">
          <div class="section-heading">Investimento por Fornecedor</div>
          <div v-if="lFornecedor" class="skel" style="height:280px" />
          <div v-else-if="!porFornecedor.length" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="280" :options="donutFornecedorOptions" :series="donutFornecedorSeries" />
        </section>

        <!-- Distribuição por Eixo -->
        <section class="v-block">
          <div class="section-heading">Distribuição por Eixo</div>
          <div v-if="lEixo" class="skel" style="height:280px" />
          <div v-else-if="!porEixo.length" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="280" :options="donutEixoOptions" :series="donutEixoSeries" />
        </section>
      </div>

      <!-- SEÇÃO 4: INVESTIMENTO POR FILIAL -->
      <section class="v-block">
        <div class="section-heading">Investimento por Filial</div>
        <div v-if="lFilial" class="skel" style="height:300px" />
        <div v-else-if="!porFilial.length" class="empty">Sem dados</div>
        <apexchart v-else type="bar" height="300" :options="barFilialOptions" :series="barFilialSeries" />
      </section>

      <!-- SEÇÃO 5: DISTRIBUIÇÃO POR MEDIDA E ESTADO -->
      <div class="two-col">
        <!-- Por Medida -->
        <section class="v-block">
          <div class="section-heading">Distribuição por Aro</div>
          <div v-if="lMedida" class="skel" style="height:280px" />
          <div v-else-if="!porMedida.length" class="empty">Sem dados</div>
          <apexchart v-else type="bar" height="280" :options="barMedidaOptions" :series="barMedidaSeries" />
        </section>

        <!-- Por Estado -->
        <section class="v-block">
          <div class="section-heading">Distribuição por Estado (UF)</div>
          <div v-if="lEstado" class="skel" style="height:280px" />
          <div v-else-if="!porEstado.length" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="280" :options="donutEstadoOptions" :series="donutEstadoSeries" />
        </section>
      </div>

      <!-- SEÇÃO 6: GASTOS POR MÊS -->
      <section class="v-block">
        <div class="section-heading">Gastos por Mês</div>
        <div v-if="lTimeline" class="skel" style="height:300px" />
        <div v-else-if="!timeline.series?.length" class="empty">Sem dados</div>
        <apexchart v-else type="area" height="340" :options="areaTimelineOptions" :series="areaTimelineSeries" />
      </section>

      <!-- SEÇÃO 7: RANKING POR PLACA -->
      <section class="v-block">
        <div class="section-heading">Veículos com Mais Pneus</div>
        <div v-if="lPlaca" class="skel" style="height:300px" />
        <div v-else-if="!porPlaca.length" class="empty">Sem dados</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Placa</th>
                <th>Veículo</th>
                <th>Filial</th>
                <th class="right">Qtd Pneus</th>
                <th class="right">Valor Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in porPlaca" :key="i">
                <td class="mono fw-bold">{{ row.placa }}</td>
                <td>{{ row.veiculo }}</td>
                <td>{{ row.filial }}</td>
                <td class="right mono">{{ row.quantidade }}</td>
                <td class="right mono">{{ fmtR(row.valor) }}</td>
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
import {
  fetchPneusFiltros, fetchPneusKpis, fetchPneusTabela,
  fetchPneusPorFilial, fetchPneusPorMarca, fetchPneusPorFornecedor,
  fetchPneusPorEixo, fetchPneusPorMedida, fetchPneusPorEstado,
  fetchPneusPorTipo, fetchPneusTimeline, fetchPneusPorPlaca,
} from '../api/pneus.js'

// Estado dos filtros
const filtros = ref({ anos: [], filiais: [], marcas: [], fornecedores: [], eixos: [], medidas: [], aros: [] })
const filtroAno = ref('')
const filtroFilial = ref('')
const filtroMarca = ref('')
const filtroFornecedor = ref('')
const filtroAro = ref('')
const filtroMedida = ref('')

// Dados
const kpis = ref({})
const porTipo = ref([])
const porFilial = ref([])
const porMarca = ref([])
const porFornecedor = ref([])
const porEixo = ref([])
const porMedida = ref([])
const porEstado = ref([])
const timeline = ref({})
const porPlaca = ref([])


// Loading states
const lKpis = ref(true)
const lTipo = ref(true)
const lFilial = ref(true)
const lMarca = ref(true)
const lFornecedor = ref(true)
const lEixo = ref(true)
const lMedida = ref(true)
const lEstado = ref(true)
const lTimeline = ref(true)
const lPlaca = ref(true)


// Formatters
function fmtR(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
function fmtN(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR')
}

// Labels das colunas
const LABELS = {
  n_fogo: 'Nº Fogo', dot: 'DOT', data_envio: 'Data Envio', filial: 'Filial',
  placa: 'Placa', veiculo: 'Veículo', marca: 'Marca', modelo: 'Modelo',
  medida: 'Medida', eixo: 'Eixo', estado_pneu: 'Tipo', fornecedor: 'Fornecedor',
  nf: 'NF', valor_un: 'R$/Un', total: 'Total',
}
function colLabel(col) { return LABELS[col] || col }
function isNumeric(col) { return ['valor_un', 'total'].includes(col) }
function fmtCell(val, col) {
  if (val == null || val === '') return '—'
  if (['valor_un', 'total'].includes(col)) return fmtR(val)
  if (col === 'data_envio' && val) {
    const d = new Date(val)
    if (!isNaN(d)) return d.toLocaleDateString('pt-BR')
  }
  return val
}

// Params para API
const params = () => ({
  ano: filtroAno.value,
  filial: filtroFilial.value,
  marca: filtroMarca.value,
  fornecedor: filtroFornecedor.value,
  aro: filtroAro.value,
  medida: filtroMedida.value,
})

// Carregamento de dados
async function loadAll() {
  const p = params()
  lKpis.value = true; lTipo.value = true; lFilial.value = true
  lMarca.value = true; lFornecedor.value = true; lEixo.value = true
  lMedida.value = true; lEstado.value = true; lTimeline.value = true
  lPlaca.value = true

  try {
    const [k, t, fm, ma, fo, ex, me, es, tl, pl] = await Promise.all([
      fetchPneusKpis(p),
      fetchPneusPorTipo(p),
      fetchPneusPorFilial(p),
      fetchPneusPorMarca(p),
      fetchPneusPorFornecedor(p),
      fetchPneusPorEixo(p),
      fetchPneusPorMedida(p),
      fetchPneusPorEstado(p),
      fetchPneusTimeline({ filial: p.filial, marca: p.marca, fornecedor: p.fornecedor }),
      fetchPneusPorPlaca({ ...p, limit: 20 }),
    ])
    kpis.value = k
    porTipo.value = t
    porFilial.value = fm
    porMarca.value = ma
    porFornecedor.value = fo
    porEixo.value = ex
    porMedida.value = me
    porEstado.value = es
    timeline.value = tl
    porPlaca.value = pl
  } catch (e) {
    console.error('Pneus: erro ao carregar', e)
  }
  lKpis.value = false; lTipo.value = false; lFilial.value = false
  lMarca.value = false; lFornecedor.value = false; lEixo.value = false
  lMedida.value = false; lEstado.value = false; lTimeline.value = false
  lPlaca.value = false
}

onMounted(async () => {
  try {
    filtros.value = await fetchPneusFiltros()
  } catch (e) {
    console.error('Pneus: erro ao carregar filtros', e)
  }
  loadAll()
})

// Cores
const COLORS = ['#C41230', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#84CC16', '#6366F1']

// Gráficos

// Donut: Tipo (Novo vs Recap)
const donutTipoOptions = computed(() => ({
  labels: porTipo.value.map(t => t.estado_pneu),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: ['#10B981', '#F59E0B'],
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutTipoSeries = computed(() => porTipo.value.map(t => t.quantidade))

// Barra: Marca
const barMarcaOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  xaxis: { categories: porMarca.value.map(m => m.marca), labels: { style: { fontSize: '11px' }, formatter: v => fmtR(v) } },
  yaxis: { labels: { show: true } },
  colors: ['#C41230'],
  plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
  dataLabels: { enabled: false },
}))
const barMarcaSeries = computed(() => [{ name: 'Valor', data: porMarca.value.map(m => m.valor) }])

// Donut: Fornecedor
const donutFornecedorOptions = computed(() => ({
  labels: porFornecedor.value.map(f => f.fornecedor),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: COLORS,
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutFornecedorSeries = computed(() => porFornecedor.value.map(f => f.quantidade))

// Donut: Eixo
const donutEixoOptions = computed(() => ({
  labels: porEixo.value.map(e => e.eixo),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: ['#C41230', '#3B82F6', '#10B981', '#F59E0B'],
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutEixoSeries = computed(() => porEixo.value.map(e => e.quantidade))

// Barra: Filial
const barFilialOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  xaxis: { categories: porFilial.value.map(f => f.filial), labels: { style: { fontSize: '10px' }, rotate: -45 } },
  yaxis: [
    { title: { text: 'Valor (R$)' }, labels: { formatter: v => fmtR(v) } },
    { opposite: true, title: { text: 'Qtd' }, labels: { formatter: v => Math.round(v) } },
  ],
  colors: ['#C41230', '#3B82F6'],
  plotOptions: { bar: { borderRadius: 4 } },
  dataLabels: { enabled: false },
}))
const barFilialSeries = computed(() => [
  { name: 'Valor', type: 'column', data: porFilial.value.map(f => f.valor) },
  { name: 'Quantidade', type: 'column', data: porFilial.value.map(f => f.quantidade) },
])

// Barra: Medida
const barMedidaOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  xaxis: { categories: porMedida.value.map(m => m.medida), labels: { style: { fontSize: '11px' }, formatter: v => Math.round(v) } },
  yaxis: { labels: { show: true } },
  colors: ['#3B82F6'],
  plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
  dataLabels: { enabled: false },
}))
const barMedidaSeries = computed(() => [{ name: 'Quantidade', data: porMedida.value.map(m => m.quantidade) }])


// Donut: Estado (UF)
const donutEstadoOptions = computed(() => ({
  labels: porEstado.value.map(e => e.estado),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: COLORS,
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutEstadoSeries = computed(() => porEstado.value.map(e => e.valor))

// Área: Gastos por Mês (com comparação por ano)
const TIMELINE_COLORS = ['#C41230', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']
const areaTimelineOptions = computed(() => {
  const tl = timeline.value
  const meses = tl.meses || []
  const series = tl.series || []
  const lastIdx = series.length - 1
  // Último ano = linha grossa sólida + fill; anos anteriores = tracejado sem fill
  const dashArray = series.map((_, i) => i === lastIdx ? 0 : 5)
  const widths = series.map((_, i) => i === lastIdx ? 3 : 2)
  const fillOpacity = series.map((_, i) => i === lastIdx ? 0.3 : 0)
  // Cores: último ano (mais recente) = vermelho, anteriores = cores progressivas
  const colors = TIMELINE_COLORS.slice(0, series.length).reverse()
  return {
    chart: { toolbar: { show: false } },
    xaxis: { categories: meses, labels: { style: { fontSize: '11px' } } },
    yaxis: { labels: { formatter: v => fmtR(v) } },
    colors,
    stroke: { curve: 'smooth', width: widths, dashArray },
    fill: { type: 'solid', opacity: fillOpacity },
    dataLabels: { enabled: false },
    legend: { position: 'top', fontSize: '13px', fontWeight: 500 },
    tooltip: { y: { formatter: v => fmtR(v) } },
  }
})
const areaTimelineSeries = computed(() => {
  const tl = timeline.value
  if (!tl.series) return []
  return tl.series.map(s => ({
    name: `${s.ano}`,
    data: s.dados.map(d => d.valor),
  }))
})

</script>

<style scoped>
.page { min-height: 100vh; background: var(--void); }

.topbar {
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  padding: 12px 24px;
  position: sticky;
  top: 0;
  z-index: 50;
}
.topbar-main { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.topbar-left { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.logo {
  font-size: 13px; font-weight: 700; color: #1e293b;
  display: flex; align-items: center; gap: 8px;
}
.divider { color: #cbd5e1; font-weight: 400; }
.title-group { display: flex; flex-direction: column; gap: 1px; }
.subtitle { font-size: 14px; font-weight: 600; color: #1e293b; }
.page-subtitle { font-size: 11px; color: #94a3b8; font-weight: 400; }

.topbar-center { flex: 1; }
.filters { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 2px; }
.filter-group label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.filter-group select {
  padding: 5px 10px; border: 1px solid #e2e8f0; border-radius: 6px;
  font-size: 12px; color: #1e293b; background: #fff; min-width: 120px;
  cursor: pointer;
}
.filter-group select:focus { outline: none; border-color: #C41230; }

.page-body { padding: 24px; }

.v-block {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 20px; margin-bottom: 20px;
}
.section-heading {
  font-size: 13px; font-weight: 700; color: #1e293b;
  margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.04em;
}

/* KPI Grid */
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.kpi-card {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 16px; text-align: center;
}
.kpi-card.primary { background: #fef2f2; border-color: #fecaca; }
.kpi-label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.kpi-value { font-size: 24px; font-weight: 700; color: #1e293b; }
.kpi-card.primary .kpi-value { color: #C41230; }
.kpi-sub { font-size: 11px; color: #94a3b8; margin-top: 4px; }

.kpi-skel { height: 90px; border-radius: 8px; background: #f1f5f9; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

/* Table */
.table-wrap { overflow-x: auto; }
.data-table {
  width: 100%; border-collapse: collapse; font-size: 12px;
}
.data-table th {
  text-align: left; padding: 8px 10px; border-bottom: 2px solid #e2e8f0;
  font-size: 10px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;
}
.data-table td {
  padding: 8px 10px; border-bottom: 1px solid #f1f5f9; color: #1e293b;
}
.data-table tbody tr:hover { background: #fafbfc; }
.right { text-align: right; }
.mono { font-variant-numeric: tabular-nums; }
.fw-bold { font-weight: 700; }

.empty {
  text-align: center; padding: 40px; color: #94a3b8; font-size: 13px;
}
.skel {
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}
</style>
