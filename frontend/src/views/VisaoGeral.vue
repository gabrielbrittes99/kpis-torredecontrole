<template>
  <div class="page animate-in">

    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="logo">GRITSCH <span class="divider">//</span>
          <span class="subtitle">Visão Geral · Combustível</span>
        </span>
      </div>
      <div class="topbar-right">
        <div class="filter-group global-filters">
          <select v-model="filtro.regiao" @change="load" class="select-filter global-select">
            <option :value="null">Todas as Regiões</option>
            <option v-for="r in opcoesFiltro.regioes" :key="r" :value="r">{{ r }}</option>
          </select>
          <select v-model="filtro.estado" @change="load" class="select-filter global-select">
            <option :value="null">Todos os Estados</option>
            <option v-for="e in opcoesFiltro.estados" :key="e" :value="e">{{ e }}</option>
          </select>
          <select v-model="filtro.filial" @change="load" class="select-filter global-select">
            <option :value="null">Todas as Filiais</option>
            <option v-for="f in opcoesFiltro.filiais" :key="f" :value="f">{{ f }}</option>
          </select>
          <select v-model="filtro.grupo" @change="load" class="select-filter global-select">
            <option :value="null">Todos os Grupos</option>
            <option v-for="g in opcoesFiltro.grupos_veiculo" :key="g" :value="g">{{ g }}</option>
          </select>
          <select v-model="filtro.combustivel" @change="load" class="select-filter global-select">
            <option :value="null">Combustível (Todos)</option>
            <option v-for="c in opcoesFiltro.combustiveis" :key="c" :value="c">{{ c }}</option>
          </select>
          
          <button @click="limparFiltros" class="btn-clear-global" title="Limpar todos os filtros dinâmicos">
            Limpar Filtros
          </button>
        </div>
        
        <div class="filter-group">
          <select v-model="filtro.mes" @change="load" class="select-filter">
            <option v-for="(m, i) in MESES" :key="i" :value="i + 1">{{ m }}</option>
          </select>
          <select v-model="filtro.ano" @change="load" class="select-filter">
            <option v-for="y in anos" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div v-if="ultimaAtualiz" class="update-badge mono">{{ ultimaAtualiz }}</div>
      </div>
    </header>

    <div v-if="carregando" class="loading-state">
      <div class="spinner"></div>
      <span>Carregando dados...</span>
    </div>

    <div v-else class="page-body">

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  FAIXA HERO — KPIs Redesenhados (Moderno e Agradável)           -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div class="hero-grid">
        <!-- Card 1: Gasto do Mês (Destaque Principal) -->
        <div class="hero-card hero-primary">
          <div class="hc-header">
            <span class="hc-title">Gasto do Mês{{ filtroLabel }}</span>
            <div class="hc-badge" :class="varClass(hero.gasto_mes_var_pct)">
              {{ varIcon(hero.gasto_mes_var_pct) }} {{ Math.abs(hero.gasto_mes_var_pct ?? 0).toFixed(1) }}%
            </div>
          </div>
          <div class="hc-value mono">{{ fmtR(hero.gasto_mes) }}</div>
          <div class="hc-footer">
            <div class="hc-sub">
              <span class="hc-sub-label">Volume</span>
              <span class="hc-sub-val mono">{{ fmtN(hero.litros_mes) }} L</span>
            </div>
            <div class="hc-sub">
              <span class="hc-sub-label">Abastecimentos</span>
              <span class="hc-sub-val mono">{{ fmtN(hero.total_abastecimentos) }}</span>
            </div>
          </div>
        </div>

        <!-- Card 2: Indicadores de Custo -->
        <div class="hero-card">
          <div class="hc-header">
            <span class="hc-title">Variação de Custo</span>
            <span class="hc-icon kpi-green">💲</span>
          </div>
          <div class="hc-metrics">
            <div class="hc-metric">
              <span class="hc-metric-label">Preço Médio/L</span>
              <span class="hc-metric-val mono">{{ hero.preco_medio != null ? 'R$ ' + Number(hero.preco_medio).toFixed(3) : '—' }}</span>
            </div>
            <div class="hc-metric">
              <span class="hc-metric-label">Custo/km (Ano)</span>
              <span class="hc-metric-val mono">{{ hero.custo_km != null ? 'R$ ' + Number(hero.custo_km).toFixed(3) : '—' }}</span>
            </div>
          </div>
        </div>

        <!-- Card 3: Indicadores de Frota -->
        <div class="hero-card">
          <div class="hc-header">
            <span class="hc-title">Desempenho da Frota</span>
            <span class="hc-icon kpi-slate">🚛</span>
          </div>
          <div class="hc-metrics">
            <div class="hc-metric">
              <span class="hc-metric-label">Eficiência (Ano)</span>
              <span class="hc-metric-val mono">{{ hero.kml_medio ?? '—' }} <span class="hc-unit">km/L</span></span>
            </div>
            <div class="hc-metric">
              <span class="hc-metric-label">Frota Ativa</span>
              <span class="hc-metric-val mono">{{ hero.total_veiculos ?? '—' }} <span class="hc-unit">veíc.</span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  BREAKDOWNS — tabelas compactas lado a lado                     -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div class="breakdown-row">
        <!-- Por combustível -->
        <section class="bd-card">
          <div class="bd-header">
            <span class="bd-title">Por Combustível</span>
            <span class="bd-period mono">{{ mesMesLabel }}</span>
          </div>
          <table class="bd-table">
            <thead>
              <tr>
                <th></th>
                <th>Tipo</th>
                <th class="right">Valor</th>
                <th class="right">Litros</th>
                <th class="right">R$/L</th>
                <th style="width: 100px">
                  <div class="th-bar-label">Participação</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in mixCombustivel" :key="m.grupo" class="bd-row">
                <td><span class="bd-dot" :style="{ background: combustivelColor(m.grupo) }"></span></td>
                <td class="bd-name">{{ m.grupo }}</td>
                <td class="right mono bd-val">{{ fmtR(m.valor) }}</td>
                <td class="right mono bd-sub-val">{{ fmtN(m.litros) }}</td>
                <td class="right mono bd-sub-val">{{ m.litros > 0 ? (m.valor / m.litros).toFixed(3) : '—' }}</td>
                <td>
                  <div class="bd-bar-cell">
                    <div class="bd-bar-track">
                      <div class="bd-bar-fill" :style="{ width: m.pct + '%', background: combustivelColor(m.grupo) }"></div>
                    </div>
                    <span class="bd-pct mono">{{ m.pct }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Por grupo de veículo -->
        <section class="bd-card">
          <div class="bd-header">
            <span class="bd-title">Por Grupo de Veículo</span>
            <span class="bd-period mono">{{ mesMesLabel }}</span>
          </div>
          <table class="bd-table">
            <thead>
              <tr>
                <th></th>
                <th>Grupo</th>
                <th class="right">Valor</th>
                <th class="right">Litros</th>
                <th class="right">Veíc.</th>
                <th class="right">km/L</th>
                <th style="width: 100px">
                  <div class="th-bar-label">Participação</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in porGrupo" :key="g.grupo" class="bd-row">
                <td><span class="bd-dot" :style="{ background: grupoColor(g.grupo) }"></span></td>
                <td class="bd-name">
                  <span class="bd-name-icon">{{ grupoIcon(g.grupo) }}</span>
                  {{ g.grupo }}
                </td>
                <td class="right mono bd-val">{{ fmtR(g.gasto) }}</td>
                <td class="right mono bd-sub-val">{{ fmtN(g.litros) }}</td>
                <td class="right mono bd-sub-val">{{ g.veiculos }}</td>
                <td class="right mono bd-sub-val">{{ g.kml ?? '—' }}</td>
                <td>
                  <div class="bd-bar-cell">
                    <div class="bd-bar-track">
                      <div class="bd-bar-fill" :style="{ width: g.pct_gasto + '%', background: grupoColor(g.grupo) }"></div>
                    </div>
                    <span class="bd-pct mono">{{ g.pct_gasto }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  GRÁFICOS (Mensal 12m e Semanal 8w)                             -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div class="charts-grid-top">
        <section class="v-block charts-block">
          <div class="section-title">GASTO MENSAL (12 MESES){{ filtroLabel }}</div>
          <apexchart type="bar" height="220" :options="optMensal" :series="seriesMensal" />
        </section>
        <section class="v-block charts-block">
          <div class="section-title">GASTO SEMANAL (8 SEMANAS){{ filtroLabel }}</div>
          <apexchart type="bar" height="220" :options="optSemanal" :series="seriesSemanal" />
        </section>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  GRÁFICO DIÁRIO (30 dias)                                       -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div class="charts-grid-bottom">
        <section class="v-block charts-block" style="margin-bottom: 0;">
          <div class="section-title">GASTO DIÁRIO (30 DIAS){{ filtroLabel }}</div>
          <apexchart type="area" height="220" :options="optDiario" :series="seriesDiario" />
        </section>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  SEÇÕES RESTAURADAS A PEDIDO DO USUÁRIO                           -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <section class="v-block">
        <div class="section-title">KPIs POR GRUPO DE VEÍCULO — {{ mesMesLabel }}</div>
        <div class="grupos-grid">
          <div v-for="g in porGrupo" :key="g.grupo" class="grupo-card">
            <div class="grupo-header">
              <span class="grupo-icon">{{ grupoIcon(g.grupo) }}</span>
              <span class="grupo-nome">{{ g.grupo }}</span>
              <span class="grupo-pct mono">{{ g.pct_gasto }}%</span>
            </div>
            <div class="grupo-bar-wrap">
              <div class="grupo-bar" :style="{ width: g.pct_gasto + '%', background: grupoColor(g.grupo) }"></div>
            </div>
            <div v-if="g.kml_ref != null" class="kml-bench" :class="'bench-' + g.kml_status">
              <div class="bench-row">
                <span class="bench-label">km/L real</span>
                <span class="bench-real">{{ g.kml ?? '—' }}</span>
                <span class="bench-sep">vs</span>
                <span class="bench-ref">{{ g.kml_ref }} ref.</span>
                <span class="bench-delta" :class="'delta-' + g.kml_status">
                  {{ g.kml_variacao_pct != null ? (g.kml_variacao_pct > 0 ? '▲' : '▼') + ' ' + Math.abs(g.kml_variacao_pct) + '%' : '—' }}
                </span>
              </div>
              <div class="bench-track">
                <div class="bench-fill" :style="{ width: g.kml && g.kml_ref ? Math.min(g.kml / g.kml_ref * 100, 120) + '%' : '0%', background: benchColor(g.kml_status) }"></div>
                <div class="bench-marker" :style="{ left: '83.3%' }" title="80% ref"></div>
                <div class="bench-marker ref-line" :style="{ left: '100%' }" title="100% ref"></div>
              </div>
            </div>
            <div class="grupo-stats">
              <div class="gs-item"><span class="gs-label">Gasto</span><span class="gs-val">{{ fmtR(g.gasto) }}</span></div>
              <div class="gs-item"><span class="gs-label">Litros</span><span class="gs-val">{{ fmtN(g.litros) }} L</span></div>
              <div class="gs-item" v-if="g.kml_ref == null"><span class="gs-label">km/L</span><span class="gs-val">{{ g.kml ?? '—' }}</span></div>
              <div class="gs-item"><span class="gs-label">R$/km</span><span class="gs-val">{{ g.custo_km != null ? g.custo_km.toFixed(3) : '—' }}</span></div>
              <div class="gs-item"><span class="gs-label">Veículos</span><span class="gs-val">{{ g.veiculos }}</span></div>
              <div class="gs-item"><span class="gs-label">Abast.</span><span class="gs-val">{{ g.abs_count }}</span></div>
            </div>
          </div>
        </div>
      </section>

      <div class="bottom-row">
        <section class="v-block mix-block">
          <div class="section-title">MIX DE COMBUSTÍVEL — {{ mesMesLabel }}</div>
          <div class="mix-list">
            <div v-for="m in mixCombustivel" :key="m.grupo" class="mix-item">
              <div class="mix-header">
                <span class="mix-nome">{{ m.grupo }}</span>
                <span class="mix-pct mono">{{ m.pct }}%</span>
              </div>
              <div class="mix-bar-wrap">
                <div class="mix-bar" :style="{ width: m.pct + '%', background: combustivelColor(m.grupo) }"></div>
              </div>
              <div class="mix-vals mono">{{ fmtR(m.valor) }} · {{ fmtN(m.litros) }} L</div>
            </div>
          </div>
        </section>
        <section class="v-block filiais-block">
          <div class="section-title">GASTO POR FILIAL — {{ mesMesLabel }}</div>
          <div v-if="filiais.length === 0" class="empty-msg">Dados de filial não disponíveis</div>
          <table v-else class="filiais-table">
            <thead>
              <tr>
                <th>Filial</th><th>UF</th>
                <th class="right">Gasto</th><th class="right">Litros</th><th class="right">Veíc.</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in filiais" :key="f.filial">
                <td class="filial-nome">{{ f.filial }}</td>
                <td class="uf mono">{{ f.estado || '—' }}</td>
                <td class="right mono">{{ fmtR(f.gasto) }}</td>
                <td class="right mono">{{ fmtN(f.litros) }}</td>
                <td class="right mono">{{ f.veiculos }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import { fetchVisaoGeralDashboard, fetchFiltrosDisponiveis } from '../api/visaoGeral.js'

const apexchart = VueApexCharts

const MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
               'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
const anos  = [new Date().getFullYear(), new Date().getFullYear() - 1]

const filtro = ref({ 
  mes: new Date().getMonth() + 1, 
  ano: new Date().getFullYear(),
  estado: null,
  regiao: null,
  filial: null,
  grupo: null,
  combustivel: null
})

const opcoesFiltro = ref({
  estados: [],
  regioes: [],
  filiais: [],
  grupos_veiculo: [],
  combustiveis: []
})

function limparFiltros() {
  filtro.value.estado = null
  filtro.value.regiao = null
  filtro.value.filial = null
  filtro.value.grupo = null
  filtro.value.combustivel = null
  load()
}

async function loadFiltros() {
  try {
    const f = await fetchFiltrosDisponiveis()
    opcoesFiltro.value = {
      estados: f.estados || [],
      regioes: f.regioes || [],
      filiais: f.filiais || [],
      grupos_veiculo: f.grupos_veiculo || [],
      combustiveis: f.combustiveis || []
    }
  } catch (e) {
    console.error('[VisaoGeral] Erro carregando filtros', e)
  }
}
const carregando   = ref(true)
const ultimaAtualiz = ref('')
const hero          = ref({})
const porGrupo      = ref([])
const mixCombustivel = ref([])
const filiais        = ref([])
const grafMensal     = ref([])
const grafSemanal    = ref([])
const grafDiario     = ref([])

const mesMesLabel = computed(() =>
  MESES[(filtro.value.mes ?? 1) - 1] + '/' + filtro.value.ano
)

const filtroLabel = computed(() => {
  let labels = []
  if (filtro.value.filial) labels.push(filtro.value.filial.toUpperCase())
  else if (filtro.value.estado) labels.push(filtro.value.estado.toUpperCase())
  else if (filtro.value.regiao) labels.push(filtro.value.regiao.toUpperCase())
  
  if (filtro.value.grupo) labels.push(filtro.value.grupo.toUpperCase())
  if (filtro.value.combustivel) labels.push(filtro.value.combustivel.toUpperCase())
  
  return labels.length > 0 ? ` — ${labels.join(' | ')}` : ''
})

const fmtR = v => v != null
  ? 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
  : '—'
const fmtN = v => v != null
  ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
  : '—'

const varClass = v => v == null ? 'badge-neutral' : v > 0 ? 'badge-red' : 'badge-green'
const varIcon  = v => v == null ? '' : v > 0 ? '▲' : '▼'

const GRUPO_COLORS = {
  'Caminhão17Ton': '#991b1b', 'Caminhão12Ton': '#ef4444', 'Caminhão10.5Ton': '#f97316',
  'Caminhão9Ton': '#ea580c', 'Caminhão7.5Ton': '#d97706', 'Caminhão6Ton': '#eab308',
  'Caminhão5.5Ton': '#ca8a04', 'Caminhão5Ton': '#65a30d', 'Caminhão4.2Ton': '#16a34a',
  'Pesado': '#3b82f6', 'Médio': '#8b5cf6', 'Leve': '#10b981',
  'Kombi': '#06b6d4', 'Moto': '#ec4899', 'Outros': '#6b7280',
}
const FUEL_COLORS = {
  'Diesel': '#f97316', 'Gasolina': '#3b82f6',
  'Álcool': '#10b981', 'Arla': '#8b5cf6', 'Outros': '#6b7280',
}
const GRUPO_ICONS = {
  'Caminhão17Ton': '🚛', 'Caminhão12Ton': '🚛', 'Caminhão10.5Ton': '🚚',
  'Caminhão9Ton': '🚚', 'Caminhão7.5Ton': '🚚', 'Caminhão6Ton': '🚐',
  'Caminhão5.5Ton': '🚐', 'Caminhão5Ton': '🚐', 'Caminhão4.2Ton': '🚐',
  'Pesado': '🚌', 'Médio': '🛻', 'Leve': '🚗',
  'Kombi': '🚐', 'Moto': '🏍️', 'Outros': '🚘',
}
const grupoColor      = g => GRUPO_COLORS[g] ?? '#6b7280'
const combustivelColor = g => FUEL_COLORS[g] ?? '#6b7280'
const grupoIcon       = g => GRUPO_ICONS[g] ?? '🚘'
const benchColor      = s => s === 'ok' ? '#10b981' : s === 'alerta' ? '#f59e0b' : s === 'critico' ? '#ef4444' : '#6b7280'

const chartBase = {
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  tooltip: { theme: 'light', y: { formatter: v => 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) } },
  yaxis: { labels: { style: { colors: '#64748b', fontSize: '11px' }, formatter: v => 'R$ ' + (v >= 1000 ? (v/1000).toFixed(0)+'k' : v) } },
  xaxis: { labels: { style: { colors: '#64748b', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  dataLabels: { enabled: false },
}

const optMensal = computed(() => ({
  ...chartBase,
  colors: ['#f97316'],
  xaxis: { ...chartBase.xaxis, categories: grafMensal.value.map(d => d.label) },
  plotOptions: { bar: { borderRadius: 6 } },
}))
const seriesMensal = computed(() => [{ name: 'Gasto', data: grafMensal.value.map(d => d.valor) }])

const optSemanal = computed(() => ({
  ...chartBase,
  colors: ['#3b82f6'],
  xaxis: { ...chartBase.xaxis, categories: grafSemanal.value.map(d => d.label) },
  plotOptions: { bar: { borderRadius: 6 } },
}))
const seriesSemanal = computed(() => [{ name: 'Gasto', data: grafSemanal.value.map(d => d.valor) }])

const optDiario = computed(() => ({
  ...chartBase,
  colors: ['#10b981'],
  xaxis: { ...chartBase.xaxis, categories: grafDiario.value.map(d => d.label) },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0 } },
  stroke: { width: 2 },
}))
const seriesDiario = computed(() => [{ name: 'Gasto', data: grafDiario.value.map(d => d.valor) }])

async function load() {
  carregando.value = true
  try {
    const d = await fetchVisaoGeralDashboard(filtro.value)
    hero.value          = d.hero ?? {}
    porGrupo.value      = d.por_grupo_veiculo ?? []
    mixCombustivel.value = d.mix_combustivel ?? []
    filiais.value        = d.filiais ?? []
    grafMensal.value     = d.grafico_mensal ?? []
    grafSemanal.value    = d.grafico_semanal ?? []
    grafDiario.value     = d.grafico_diario ?? []
    ultimaAtualiz.value  = 'Atualizado ' + new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    console.error('[VisaoGeral]', e)
  } finally {
    carregando.value = false
  }
}

onMounted(() => {
  loadFiltros()
  load()
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════════════ */
/*  BASE                                                                     */
/* ═══════════════════════════════════════════════════════════════════════════ */
.page {
  min-height: 100vh;
  background: var(--void, #f8fafc);
  color: #0f172a;
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
}
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; }

/* ═══ Topbar ══════════════════════════════════════════════════════════════ */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 32px; height: 56px;
  background: white; border-bottom: 1px solid #e2e8f0;
  position: sticky; top: 0; z-index: 50;
}
.logo { font-size: 15px; font-weight: 800; letter-spacing: 0.05em; }
.logo .divider { color: #f97316; }
.logo .subtitle { color: #64748b; font-size: 11px; font-weight: 500; text-transform: uppercase; }
.topbar-right {
  display: flex; gap: 16px; align-items: center;
}

/* Base Topbar Global Filters */
.global-filters {
  display: flex;
  gap: 8px;
  align-items: center;
  background: white;
  padding: 4px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}

.global-select {
  border: none;
  background: #f8fafc;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #334155;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
  min-width: 140px;
}

.global-select:hover {
  background: #f1f5f9;
}

.global-select:focus {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.btn-clear-global {
  background: transparent;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear-global:hover {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fca5a5;
}

.filter-group { display: flex; gap: 8px; }
.select-filter {
  padding: 6px 12px; border: 1px solid #e2e8f0; border-radius: 8px;
  background: #f8fafc; color: #1e293b; font-size: 13px; font-weight: 600;
  cursor: pointer; outline: none; transition: border-color 0.15s;
}
.select-filter:hover { border-color: #f97316; }
.update-badge { font-size: 11px; color: #94a3b8; }

/* ═══ Loading ═════════════════════════════════════════════════════════════ */
.loading-state {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 16px; color: #64748b;
}
.spinner {
  width: 32px; height: 32px; border: 3px solid #e2e8f0;
  border-top-color: #f97316; border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.page-body { padding: 24px 32px; flex: 1; }

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  HERO GRID — Cards Principais Redesenhados                                */
/* ═══════════════════════════════════════════════════════════════════════════ */
.hero-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.hero-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  transition: transform 0.2s, box-shadow 0.2s;
}
.hero-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
}

.hero-primary {
  background: linear-gradient(135deg, #ffedd5 0%, #ffffff 100%);
  border-color: #fdba74;
  position: relative;
  overflow: hidden;
}
.hero-primary::before {
  content: '';
  position: absolute;
  top: 0; right: 0; width: 150px; height: 150px;
  background: radial-gradient(circle, rgba(249,115,22,0.1) 0%, rgba(255,255,255,0) 70%);
  border-radius: 50%;
  transform: translate(30%, -30%);
}

.hc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  position: relative;
  z-index: 1;
}

.hc-title {
  font-size: 13px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.hc-icon {
  width: 36px; height: 36px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
}

.hc-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 12px; border-radius: 20px;
  font-size: 13px; font-weight: 800;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.hero-primary .hc-title { color: #c2410c; }

.badge-green { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
.badge-red   { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.badge-neutral { background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; }

.hc-value {
  font-size: 42px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
}

.hc-footer {
  display: flex;
  gap: 24px;
  border-top: 1px solid rgba(249, 115, 22, 0.2);
  padding-top: 16px;
  position: relative;
  z-index: 1;
}

.hc-sub {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hc-sub-label {
  font-size: 11px;
  font-weight: 600;
  color: #9a3412;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.hc-sub-val {
  font-size: 18px;
  font-weight: 700;
  color: #431407;
}

.hc-metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  justify-content: center;
}

.hc-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}
.hc-metric:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.hc-metric-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.hc-metric-val {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.hc-unit {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}

/* Icons reuse from old kpi */
.kpi-blue   { background: #eff6ff; }
.kpi-orange { background: #fff7ed; }
.kpi-green  { background: #ecfdf5; }
.kpi-teal   { background: #f0fdfa; }
.kpi-purple { background: #f5f3ff; }
.kpi-slate  { background: #f1f5f9; }

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  BREAKDOWN — tabelas compactas                                           */
/* ═══════════════════════════════════════════════════════════════════════════ */
.breakdown-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.bd-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.bd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f8fafc;
}
.bd-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}
.bd-period {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  background: #f8fafc;
  padding: 3px 10px;
  border-radius: 6px;
}

.bd-table {
  width: 100%;
  border-collapse: collapse;
}
.bd-table th {
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0 10px 10px;
  border-bottom: 1px solid #f1f5f9;
  white-space: nowrap;
}
.bd-table td {
  padding: 10px;
  vertical-align: middle;
}
.bd-row {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.bd-row.clickable {
  cursor: pointer;
}
.bd-row:hover {
  background: #f8fafc;
}
.bd-row:not(:last-child) td {
  border-bottom: 1px solid #f8fafc;
}

/* Interactive Filter States */
tbody.has-filter .bd-row.dimmed {
  opacity: 0.4;
  filter: grayscale(80%);
}
tbody.has-filter .bd-row.dimmed:hover {
  opacity: 0.6;
}
.bd-row.active {
  background: #f1f5f9;
  box-shadow: inset 2px 0 0 #f97316;
}
.bd-row.active:hover {
  background: #e2e8f0;
}

.clear-filter-btn {
  background: #fef2f2;
  color: #ef4444;
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  margin-left: 8px;
  cursor: pointer;
  transition: all 0.15s;
}
.clear-filter-btn:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #b91c1c;
}
.right { text-align: right; }

.bd-dot {
  display: inline-block;
  width: 10px; height: 10px;
  border-radius: 3px;
}
.bd-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
}
.bd-name-icon {
  margin-right: 4px;
}
.bd-val {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}
.bd-sub-val {
  font-size: 12px;
  color: #64748b;
}

.bd-bar-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bd-bar-track {
  flex: 1;
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
}
.bd-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s cubic-bezier(0.4,0,0.2,1);
}
.bd-pct {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  min-width: 32px;
  text-align: right;
}
.th-bar-label {
  font-size: 10px;
  text-align: center;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  CHARTS GRID (Layout conforme Wireframe)                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */
.charts-grid-top {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}
.charts-grid-bottom {
  margin-bottom: 24px;
}
.charts-block { padding: 24px; }

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  SHARED                                                                   */
/* ═══════════════════════════════════════════════════════════════════════════ */
.v-block {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.section-title {
  font-size: 11px; font-weight: 700; color: #64748b;
  letter-spacing: 0.08em; text-transform: uppercase;
  border-left: 3px solid #f97316;
  padding-left: 10px;
  margin-bottom: 20px;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  ANIMATION & RESPONSIVE                                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */
.animate-in { animation: fadeIn 0.25s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 1200px) {
  .kpi-strip { flex-wrap: wrap; }
  .kpi-sep:nth-child(n+6) { display: none; }
  .kpi-item:nth-child(n+8) { border-top: 1px solid #f1f5f9; }
  .breakdown-row { grid-template-columns: 1fr; }
  .charts-row { grid-template-columns: 1fr; }
  .bottom-row { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .page-body { padding: 16px; }
  .topbar { padding: 0 16px; }
  .kpi-strip { flex-direction: column; }
  .kpi-sep { width: 100%; height: 1px; }
  .kpi-hero-value { font-size: 28px; }
}
/* ═══════════════════════════════════════════════════════════════════════════ */
/*  RESTAURADAS: GRUPOS, MIX E FILIAIS (Módulos antigos)                       */
/* ═══════════════════════════════════════════════════════════════════════════ */
.grupos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.grupo-card {
  background: white; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.grupo-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;
}
.grupo-icon { font-size: 18px; margin-right: 8px; }
.grupo-nome { font-weight: 600; color: #1e293b; font-size: 14px; flex-grow: 1; }
.grupo-pct { font-weight: 700; color: #64748b; font-size: 14px; }
.grupo-bar-wrap { height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; margin-bottom: 16px; }
.grupo-bar { height: 100%; border-radius: 3px; }
.grupo-stats { display: flex; flex-wrap: wrap; gap: 12px; row-gap: 8px; border-top: 1px dashed #e2e8f0; padding-top: 12px; }
.gs-item { display: flex; flex-direction: column; width: calc(33.3% - 12px); }
.gs-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px; }
.gs-val { font-size: 13px; font-weight: 600; color: #334155; }

.kml-bench {
  background: #f8fafc; border-radius: 8px; padding: 10px; margin-bottom: 16px; border: 1px solid #e2e8f0;
}
.kml-bench.bench-ok { border-color: #a7f3d0; background: #ecfdf5; }
.kml-bench.bench-alerta { border-color: #fde68a; background: #fffbeb; }
.kml-bench.bench-critico { border-color: #fecaca; background: #fef2f2; }
.bench-row { display: flex; justify-content: space-between; align-items: center; font-size: 11px; margin-bottom: 8px; }
.bench-label { font-weight: 600; color: #475569; }
.bench-real { font-weight: 700; color: #0f172a; font-size: 13px; margin-left: 4px; }
.bench-sep { color: #94a3b8; margin: 0 4px; }
.bench-ref { color: #64748b; }
.bench-delta { font-weight: 700; margin-left: auto; }
.delta-ok { color: #059669; } .delta-alerta { color: #d97706; } .delta-critico { color: #dc2626; }
.bench-track { height: 6px; background: #e2e8f0; border-radius: 3px; position: relative; }
.bench-fill { height: 100%; border-radius: 3px; }
.bench-marker { position: absolute; top: -2px; bottom: -2px; width: 2px; background: #cbd5e1; }
.bench-marker.ref-line { background: #64748b; z-index: 2; }

.bottom-row { display: flex; gap: 24px; align-items: flex-start; }
.mix-block, .filiais-block { flex: 1; }
.mix-list { display: flex; flex-direction: column; gap: 12px; }
.mix-item { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; justify-content: center; }
.mix-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.mix-nome { font-size: 13px; font-weight: 600; color: #334155; }
.mix-pct { font-size: 14px; font-weight: 700; color: #0f172a; }
.mix-bar-wrap { height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; margin-bottom: 8px; }
.mix-bar { height: 100%; border-radius: 3px; }
.mix-vals { font-size: 12px; color: #64748b; text-align: right; }

.filiais-table { width: 100%; border-collapse: collapse; background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.filiais-table th { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; padding: 12px; border-bottom: 1px solid #f1f5f9; text-align: left; }
.filiais-table th.right { text-align: right; }
.filiais-table td { padding: 12px; font-size: 13px; border-bottom: 1px solid #f8fafc; color: #334155; }
.filial-nome { font-weight: 600; color: #0f172a; }
.uf { color: #64748b; }
.empty-msg { font-size: 13px; color: #94a3b8; padding: 24px; text-align: center; border: 1px dashed #e2e8f0; border-radius: 8px; }

</style>
