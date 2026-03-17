<template>
  <div class="page animate-in">

    <!-- Topbar -->
    <GlobalTopbar
      title="Visão Geral"
      subtitle="Indicadores Mensais de Combustível"
      :ultima-atualizacao="ultimaAtualiz"
    />

    <div v-if="carregando" class="loading-state">
      <div class="spinner"></div>
      <span>Carregando dados...</span>
    </div>

    <div v-else class="page-body">

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!-- AVISO DE VEÍCULOS SEM FILIAL -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div v-if="veiculosSemFilial.length" class="alert-box alert-warning" style="margin-bottom: 24px; padding: 16px; border-radius: 12px; border: 1px solid #f59e0b; background: #fffbeb; color: #b45309; display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 20px;">⚠️</span>
        <div>
          <div style="font-weight: 700; font-size: 13px; margin-bottom: 2px;">Atenção: Falta de Alocação de Filial para {{ veiculosSemFilial.length }} Veículos</div>
          <div style="font-size: 12px; opacity: 0.9;">As seguintes placas registraram abastecimento mas estão sem filial definida na base: <span style="font-family: monospace; font-weight: 600;">{{ veiculosSemFilial.join(', ') }}</span></div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  FAIXA HERO — KPIs Redesenhados (Moderno e Agradável)           -->
      <div class="kpi-pro-grid">
        <KpiCardPro
          title="Gasto Total"
          :value="hero.gasto_mes || 0"
          format="currency"
          :trendValue="hero.gasto_mes_var_pct"
          :trendInvert="true"
          theme="primary"
          :description="hero.trend_label ? 'vs ' + hero.trend_label : ''"
        />
        <KpiCardPro
          title="Volume (Litros)"
          :value="hero.litros_mes || 0"
          format="number"
          unit="L"
        />
        <KpiCardPro
          title="Preço Médio"
          :value="hero.preco_medio || 0"
          format="currency"
          :decimals="3"
          unit="/ L"
        />
        <KpiCardPro
          title="Abastecimentos"
          :value="hero.total_abastecimentos || 0"
          format="number"
        />
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
                    <button class="btn-drill" @click="irParaOperacionalCombustivel(m.grupo)" title="Ver placas deste combustível">
                      <span class="icon-drill">→</span>
                    </button>
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
                    <button class="btn-drill" @click="irParaOperacional(g.grupo)" title="Ver placas deste grupo">
                      <span class="icon-drill">→</span>
                    </button>
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
      <!--  PREÇO MÉDIO POR ESTADO POR COMBUSTÍVEL                        -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <section class="v-block" style="margin-bottom: 24px;">
        <div class="section-title-row">
          <div class="section-title" style="margin-bottom:0">PREÇO MÉDIO POR ESTADO (UF)</div>
          <div class="uf-comb-tabs">
            <button :class="{ active: filtroUFComb === null }" @click="setFiltroUF(null)">Todos</button>
            <button
              v-for="c in opcoesUFComb"
              :key="c"
              :class="{ active: filtroUFComb === c }"
              :style="filtroUFComb === c ? { background: combustivelColor(c), borderColor: combustivelColor(c), color: 'white' } : { borderColor: combustivelColor(c), color: combustivelColor(c) }"
              @click="setFiltroUF(c)"
            >{{ c }}</button>
          </div>
        </div>
        <GraficoPrecoPorUF :data="precoPorUF" :loading="lUF" />
      </section>

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
              <div class="gh-main">
                <span class="grupo-nome">{{ g.grupo }}</span>
                <span class="grupo-pct mono">{{ g.pct_gasto }}%</span>
              </div>
              <button class="btn-drill-card" @click="irParaOperacional(g.grupo)" title="Monitorar Operacional deste grupo">
                OPERACIONAL <span class="icon-drill">→</span>
              </button>
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
                <div class="bench-fill" :style="{ width: g.kml && g.kml_ref ? Math.min(g.kml / g.kml_ref * 100, 100) + '%' : '0%', background: benchColor(g.kml_status) }"></div>
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
          <div v-if="filiaisVisiveis.length === 0" class="empty-msg">Dados de filial não disponíveis</div>
          <div v-else class="filiais-cards">
            <div v-for="f in filiaisVisiveis" :key="f.filial" class="filial-row">
              <div class="filial-row-top">
                <div class="filial-info">
                  <span class="filial-dot" :style="{ background: combustivelColor(f.combustivel_pred) }"></span>
                  <span class="filial-nome">{{ f.filial.replace('Gritsch ', '') }}</span>
                  <span class="filial-uf mono">{{ f.estado || '—' }}</span>
                </div>
                <div class="filial-nums">
                  <span class="filial-gasto mono">{{ fmtR(f.gasto) }}</span>
                  <span class="filial-pct mono">{{ filiaisTotalGasto > 0 ? (f.gasto / filiaisTotalGasto * 100).toFixed(1) + '%' : '—' }}</span>
                  <button class="btn-drill" @click="irParaOperacionalFilial(f.filial)" title="Ver operacional desta filial">
                    <span class="icon-drill">→</span>
                  </button>
                </div>
              </div>
              <div class="filial-bar-wrap">
                <div
                  class="filial-bar-fill"
                  :style="{
                    width: filiaisTotalGasto > 0 ? Math.min((f.gasto / filiaisTotalGasto * 100), 100) + '%' : '0%',
                    background: combustivelColor(f.combustivel_pred)
                  }"
                ></div>
              </div>
              <div class="filial-meta mono">
                {{ fmtN(f.litros) }} L · {{ f.veiculos }} veíc.
                <span v-if="f.combustivel_pred" class="comb-badge" :style="{ color: combustivelColor(f.combustivel_pred) }">{{ f.combustivel_pred }}</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import VueApexCharts from 'vue3-apexcharts'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import GraficoPrecoPorUF from '../components/GraficoPrecoPorUF.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import { fetchVisaoGeralDashboard } from '../api/visaoGeral.js'
import { fetchPrecoPorUF } from '../api/precos.js'
import { useFiltrosStore } from '../stores/filtros'

const apexchart = VueApexCharts
const router = useRouter()
const store = useFiltrosStore()

function irParaOperacional(grupo) {
  store.selecao.grupo = grupo
  router.push({ name: 'operacional' })
}

function irParaOperacionalFilial(filial) {
  store.selecao.filial = filial
  router.push({ name: 'operacional' })
}

function irParaOperacionalCombustivel(comb) {
  const map = { 'Diesel': 'diesel', 'Gasolina': 'gasolina', 'Álcool': 'etanol' }
  router.push({ name: 'operacional', query: { familia: map[comb] || 'todos' } })
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

const precoPorUF     = ref([])
const lUF            = ref(true)
const filtroUFComb   = ref(null)

// Combustíveis disponíveis para os tabs do gráfico UF (fixos pois são os grupos padrão)
const opcoesUFComb = ['Diesel', 'Gasolina', 'Álcool', 'Arla']

async function setFiltroUF(comb) {
  filtroUFComb.value = comb
  lUF.value = true
  try {
    precoPorUF.value = await fetchPrecoPorUF({
      combustivel: comb ?? store.selecao.combustivel ?? undefined,
    })
  } finally {
    lUF.value = false
  }
}

// Filiais — exclui "Sem filial identificada" da tabela (já aparece no alerta)
const filiaisVisiveis = computed(() =>
  filiais.value.filter(f => f.filial !== 'Sem filial identificada')
)

const filiaisTotalGasto = computed(() =>
  filiaisVisiveis.value.reduce((s, f) => s + (f.gasto || 0), 0)
)

const veiculosSemFilial = computed(() => {
  const sf = filiais.value.find(f => f.filial === "Sem filial identificada")
  return sf && sf.placas_pendentes ? sf.placas_pendentes : []
})

const mesMesLabel = computed(() => {
  const s = store.selecao
  if (s.modoTempo === 'mes') return store.opcoes.meses[(s.mes ?? 1) - 1] + '/' + s.ano
  if (s.modoTempo === 'bimestre') return store.opcoes.bimestres[(s.bimestre ?? 1) - 1] + '/' + s.ano
  if (s.modoTempo === 'semestre') return store.opcoes.semestres[(s.semestre ?? 1) - 1] + '/' + s.ano
  if (s.modoTempo === 'ano') return 'Ano ' + s.ano
  if (s.modoTempo === 'personalizado') return `${s.data_inicio} a ${s.data_fim}`
  return '—'
})

const filtroLabel = computed(() => {
  let labels = []
  if (store.selecao.modoTempo !== 'mes') labels.push(store.selecao.modoTempo.toUpperCase())
  
  if (store.selecao.filial) labels.push(store.selecao.filial.toUpperCase())
  else if (store.selecao.estado) labels.push(store.selecao.estado.toUpperCase())
  else if (store.selecao.regiao) labels.push(store.selecao.regiao.toUpperCase())
  
  if (store.selecao.grupo) labels.push(store.selecao.grupo.toUpperCase())
  if (store.selecao.combustivel) labels.push(store.selecao.combustivel.toUpperCase())
  
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
const grupoColor      = g => GRUPO_COLORS[g] ?? '#6b7280'
const combustivelColor = g => FUEL_COLORS[g] ?? '#6b7280'
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
    const d = await fetchVisaoGeralDashboard(store.selecao)
    hero.value          = d.hero ?? {}
    porGrupo.value      = d.por_grupo_veiculo ?? []
    mixCombustivel.value = d.mix_combustivel ?? []
    filiais.value        = d.filiais ?? []
    grafMensal.value     = d.grafico_mensal ?? []
    grafSemanal.value    = d.grafico_semanal ?? []
    grafDiario.value     = d.grafico_diario ?? []
    ultimaAtualiz.value  = 'Atualizado ' + new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

    // Busca o gráfico de estado — reseta tab local ao trocar filtro global
    filtroUFComb.value = null
    lUF.value = true
    try {
      precoPorUF.value = await fetchPrecoPorUF({
        combustivel: store.selecao.combustivel ?? undefined,
      })
    } catch (e) {
      console.error('[VisaoGeral] Erro Preço UF', e)
    } finally {
      lUF.value = false
    }

  } catch (e) {
    console.error('[VisaoGeral]', e)
  } finally {
    carregando.value = false
  }
}

watch(
  () => store.selecao,
  () => {
    load()
  },
  { deep: true }
)

onMounted(() => {
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

/* Icons reuse from old kpi */
.kpi-blue   { background: #eff6ff; }
.kpi-orange { background: #fff7ed; }
.kpi-green  { background: #ecfdf5; }
.kpi-teal   { background: #f0fdfa; }
.kpi-purple { background: #f5f3ff; }
.kpi-slate  { background: #f1f5f9; }

.kpi-pro-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

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
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
  .kpi-sep:nth-child(n+6) { display: none; }
  .kpi-item:nth-child(n+8) { border-top: 1px solid #f1f5f9; }
  .breakdown-row { grid-template-columns: 1fr; }
  .charts-row { grid-template-columns: 1fr; }
  .bottom-row { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .kpi-pro-grid { grid-template-columns: 1fr; }
  .page-body { padding: 16px; }
  .topbar { padding: 0 16px; }
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

.btn-drill {
  background: none; border: none; padding: 0 4px; cursor: pointer;
  color: #94a3b8; display: flex; align-items: center; justify-content: center;
  margin-left: 4px; opacity: 0; transition: all 0.2s;
}
.bd-row:hover .btn-drill { opacity: 1; color: var(--orange); }

.grupo-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.gh-main { display: flex; flex-direction: column; gap: 2px; }

.btn-drill-card {
  background: rgba(249, 115, 22, 0.08); border: 1px solid rgba(249, 115, 22, 0.15);
  padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: 700;
  color: var(--orange); cursor: pointer; transition: all 0.2s;
  letter-spacing: 0.05em;
}
.btn-drill-card:hover { background: var(--orange); color: white; border-color: var(--orange); }
.icon-drill { font-size: 14px; line-height: 1; }

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

/* ── Tabs UF Combustível ─────────────────────────────────────────────────── */
.section-title-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px; gap: 16px; flex-wrap: wrap;
}
.uf-comb-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.uf-comb-tabs button {
  background: transparent; border: 1.5px solid #e2e8f0; color: #64748b;
  font-size: 11px; font-weight: 700; padding: 4px 14px; border-radius: 20px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all .15s;
  letter-spacing: 0.03em;
}
.uf-comb-tabs button.active { color: white; }
.uf-comb-tabs button:not(.active):hover { border-color: #94a3b8; }

/* ── Filiais Cards ───────────────────────────────────────────────────────── */
.filiais-cards { display: flex; flex-direction: column; gap: 10px; }
.filial-row { padding: 10px 0; border-bottom: 1px solid #f1f5f9; }
.filial-row:last-child { border-bottom: none; }
.filial-row-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.filial-info { display: flex; align-items: center; gap: 8px; }
.filial-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.filial-nome { font-size: 13px; font-weight: 600; color: #1e293b; }
.filial-uf { font-size: 11px; color: #94a3b8; margin-left: 2px; }
.filial-nums { display: flex; align-items: center; gap: 12px; }
.filial-gasto { font-size: 13px; font-weight: 700; color: #0f172a; }
.filial-pct { font-size: 12px; color: #64748b; min-width: 36px; text-align: right; }
.filial-bar-wrap { height: 5px; background: #f1f5f9; border-radius: 3px; overflow: hidden; margin-bottom: 5px; }
.filial-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
.filial-meta { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 8px; }
.comb-badge { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 10px; background: #f8fafc; }
.filiais-block .btn-drill { opacity: 0.4; }
.filial-row:hover .btn-drill { opacity: 1; }

.empty-msg { font-size: 13px; color: #94a3b8; padding: 24px; text-align: center; border: 1px dashed #e2e8f0; border-radius: 8px; }

</style>
