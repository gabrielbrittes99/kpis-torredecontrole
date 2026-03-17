<template>
  <div class="page">
    <GlobalTopbar
      title="Gestão de Frota"
      subtitle="Acompanhamento operacional — custo/km, eficiência, preços e alertas por grupo"
    />

    <div class="page-body">

      <!-- ━━━━━ BANNER DE ALERTA ━━━━━ -->
      <div
        v-if="!lAcao && resumoAcao.total_acao > 0"
        class="alert-banner"
        :class="alertaSeveridade"
      >
        <div class="alert-icon">{{ alertaSeveridade === 'critico' ? '🔴' : '🟡' }}</div>
        <div class="alert-text">
          <strong>{{ resumoAcao.total_acao }} veículo{{ resumoAcao.total_acao > 1 ? 's' : '' }} fora do padrão do seu grupo</strong>
          · economia possível: <span class="alert-valor">{{ fmtR(resumoAcao.economia_total_possivel) }}</span>
          · {{ resumoAcao.grupos_monitorados }} grupos monitorados
        </div>
        <a class="alert-link" href="#secao-acao">Ver veículos ↓</a>
      </div>

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
                    <th style="width:140px">Custo/KM</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="g in custoPorGrupo" :key="g.grupo">
                    <td class="grupo-nome">{{ formatGrupo(g.grupo) }}</td>
                    <td class="right mono bold">{{ g.custo_km ? `R$ ${g.custo_km.toFixed(4)}` : '—' }}</td>
                    <td class="right mono dim">{{ g.km_litro?.toFixed(2) ?? '—' }}</td>
                    <td class="right mono dim">{{ g.kml_referencia?.toFixed(2) ?? '—' }}</td>
                    <td class="right mono" :class="pctClass(g.pct_vs_referencia)">
                      {{ g.pct_vs_referencia != null ? (g.pct_vs_referencia > 0 ? '+' : '') + g.pct_vs_referencia.toFixed(1) + '%' : '—' }}
                    </td>
                    <td class="right mono dim">{{ fmtR(g.total_valor) }}</td>
                    <td class="right mono dim">{{ fmtN(g.total_litros) }}</td>
                    <td class="right mono dim">{{ g.qtd_veiculos }}</td>
                    <td>
                      <div class="bar-track">
                        <div class="bar-fill" :class="barColor(g)" :style="{ width: barWidth(g.custo_km) + '%' }" />
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

      <!-- ━━━━━ SEÇÃO 4: PREÇOS NOS POSTOS ━━━━━ -->
      <div class="postos-grid">
        <div class="v-block">
          <div class="section-heading">Top 10 Postos Mais Caros</div>
          <TabelaRankingPostos :data="postosMaisCaros" :loading="lPostos" ordem="mais_caro" />
        </div>
        <div class="v-block">
          <div class="section-heading">Top 10 Postos Mais Baratos</div>
          <TabelaRankingPostos :data="postosMaisBaratos" :loading="lPostosBaratos" ordem="mais_barato" />
        </div>
      </div>

      <!-- ━━━━━ SEÇÃO 5: VARIAÇÃO DE PREÇO POR MÊS ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Variação de Preço Médio por Mês</div>
        <GraficoVariacaoMensal :data="variacao" :loading="lVariacao" />
      </section>

      <!-- ━━━━━ SEÇÃO 6: MONITORAMENTO + ETANOL/GASOLINA ━━━━━ -->
      <div id="secao-acao" class="action-section">
        <div class="v-block">
          <div class="section-heading">Veículos sob Alerta · Comparação por Grupo</div>
          <TabelaVeiculosAcao :data="veiculosAcao" :resumo="resumoAcao" :loading="lAcao" />
        </div>

        <div class="v-block">
          <div class="section-heading">Etanol vs Gasolina · Decisão por Filial</div>
          <TabelaEtanolGasolina :data="etanolGasolina" :loading="lEtGas" />
        </div>
      </div>

      <!-- ━━━━━ SEÇÃO 7: EVOLUÇÃO HISTÓRICA (eixo Y duplo) ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Evolução Histórica · Custo/KM vs Preço/L (12 meses)</div>
        <div class="card">
          <div v-if="lEvolucao" class="skel" style="height:280px" />
          <div v-else-if="!evolucao.length" class="empty">Sem dados históricos</div>
          <apexchart v-else type="line" height="280" :options="optEvolucao" :series="seriesEvolucao" />
        </div>
      </section>

    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle do Futuro</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useFiltrosStore } from '../stores/filtros'
import VueApexCharts from 'vue3-apexcharts'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import GraficoBarrasFilial from '../components/GraficoBarrasFilial.vue'
import GraficoVariacaoMensal from '../components/GraficoVariacaoMensal.vue'
import TabelaVeiculosAcao from '../components/TabelaVeiculosAcao.vue'
import TabelaEtanolGasolina from '../components/TabelaEtanolGasolina.vue'
import TabelaRankingPostos from '../components/TabelaRankingPostos.vue'
import KpiCardPro from '../components/KpiCardPro.vue'

import {
  fetchKpisOperacional, fetchCustoPorGrupo, fetchCustoPorFilial,
  fetchEvolucaoMensal, fetchVeiculosAcao, fetchEtanolGasolinaFilial,
} from '../api/operacional.js'
import { fetchRankingPostosPreco, fetchVariacaoMensal } from '../api/precos.js'

const apexchart = VueApexCharts
const store = useFiltrosStore()

// Seletor de família — local, não afeta store global
const familiaFiltro = ref('todos')
const FAMILIAS_LIST = [
  { key: 'todos',    label: 'Geral' },
  { key: 'diesel',   label: 'Diesel' },
  { key: 'gasolina', label: 'Gasolina' },
  { key: 'etanol',   label: 'Etanol' },
]
const labelFamilia = computed(() => FAMILIAS_LIST.find(f => f.key === familiaFiltro.value)?.label ?? familiaFiltro.value)

// Estado
const kpis           = ref({})
const custoPorGrupo  = ref([])
const custoPorFilial = ref({ filiais: [], media_geral: null })
const evolucao       = ref([])
const veiculosAcao   = ref([])
const resumoAcao     = ref({})
const etanolGasolina = ref([])
const postosMaisCaros   = ref([])
const postosMaisBaratos = ref([])
const variacao       = ref([])

const lKpis    = ref(true)
const lGrupo   = ref(true)
const lFilial  = ref(true)
const lEvolucao = ref(true)
const lAcao    = ref(true)
const lEtGas   = ref(true)
const lPostos  = ref(true)
const lPostosBaratos = ref(true)
const lVariacao = ref(true)

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

const alertaSeveridade = computed(() => {
  const pct = resumoAcao.value.total_acao / (resumoAcao.value.total_frota || 1)
  return pct >= 0.3 ? 'critico' : 'atencao'
})

const filialData = computed(() => custoPorFilial.value.filiais || [])

// Formatação de grupo
function formatGrupo(g) {
  return g.replace('Caminhão', 'Caminhão ').replace('Ton', 'T').replace('10.5', '10,5').replace('4.2', '4,2').replace('5.5', '5,5').replace('7.5', '7,5')
}

// Barra visual custo/km grupo
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
  if (pct == null) return 'dim'
  return pct >= 0 ? 'green' : pct > -15 ? 'orange' : 'red'
}

// Data loading
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
  lKpis.value = lGrupo.value = lFilial.value = lEvolucao.value = lAcao.value = lEtGas.value = lPostos.value = lPostosBaratos.value = lVariacao.value = true

  await Promise.allSettled([
    fetchKpisOperacional(p).then(d => kpis.value = d).finally(() => lKpis.value = false),
    fetchCustoPorGrupo(p).then(d => custoPorGrupo.value = d).finally(() => lGrupo.value = false),
    fetchCustoPorFilial(p).then(d => custoPorFilial.value = d).finally(() => lFilial.value = false),
    fetchEvolucaoMensal(p).then(d => evolucao.value = d).finally(() => lEvolucao.value = false),
    fetchVeiculosAcao(p).then(d => { veiculosAcao.value = d.veiculos ?? []; resumoAcao.value = d.resumo ?? {} }).finally(() => lAcao.value = false),
    fetchEtanolGasolinaFilial(p).then(d => etanolGasolina.value = d).finally(() => lEtGas.value = false),
    fetchRankingPostosPreco({ ...p, combustivel: fam !== 'todos' ? fam : undefined, ordem: 'mais_caro', limit: 10 })
      .then(d => postosMaisCaros.value = d).finally(() => lPostos.value = false),
    fetchRankingPostosPreco({ ...p, combustivel: fam !== 'todos' ? fam : undefined, ordem: 'mais_barato', limit: 10 })
      .then(d => postosMaisBaratos.value = d).finally(() => lPostosBaratos.value = false),
    fetchVariacaoMensal({ ...p, combustivel: fam !== 'todos' ? fam : undefined })
      .then(d => variacao.value = d).finally(() => lVariacao.value = false),
  ])
}

watch(() => store.selecao, () => loadAll(), { deep: true })
onMounted(() => loadAll())

// ── Gráfico de evolução com eixo Y duplo ──
const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]} ${y.slice(2)}` }

const seriesEvolucao = computed(() => {
  const dados = evolucao.value
  return [
    { name: 'Custo/km (R$/km)', type: 'line', data: dados.map(d => d.custo_km != null ? +d.custo_km.toFixed(4) : null) },
    { name: 'Preço/L (R$/L)',   type: 'line', data: dados.map(d => d.preco_litro != null ? +d.preco_litro.toFixed(3) : null) },
    { name: 'Volume (L)',       type: 'column', data: dados.map(d => Math.round(d.total_litros || 0)) },
  ]
})

const optEvolucao = computed(() => {
  const dados = evolucao.value
  return {
    chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', stacked: false },
    theme: { mode: 'light' },
    colors: ['#f97316', '#3b82f6', '#e2e8f0'],
    stroke: { curve: 'smooth', width: [3, 2, 0] },
    markers: { size: [4, 3, 0], strokeWidth: 0 },
    dataLabels: { enabled: false },
    legend: { show: true, position: 'top', horizontalAlign: 'right' },
    fill: { opacity: [1, 1, 0.3] },
    plotOptions: { bar: { borderRadius: 4, columnWidth: '45%' } },
    xaxis: {
      categories: dados.map(d => fmtMes(d.ano_mes)),
      labels: { style: { colors: '#94a3b8', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' } },
      axisBorder: { show: false }, axisTicks: { show: false },
    },
    yaxis: [
      {
        title: { text: 'R$/km', style: { fontSize: '11px', color: '#f97316' } },
        labels: { style: { colors: '#f97316', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }, formatter: v => `${Number(v).toFixed(2)}` },
        min: 0,
      },
      {
        opposite: true,
        title: { text: 'R$/L', style: { fontSize: '11px', color: '#3b82f6' } },
        labels: { style: { colors: '#3b82f6', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }, formatter: v => `${Number(v).toFixed(2)}` },
        min: 0,
      },
      {
        opposite: true,
        show: false,
        min: 0,
      },
    ],
    grid: { borderColor: '#f1f5f9', strokeDashArray: 4 },
    tooltip: {
      shared: true, intersect: false,
      y: { formatter: (v, { seriesIndex }) => {
        if (seriesIndex === 2) return v != null ? fmtN(v) + ' L' : '—'
        return v != null ? `R$ ${Number(v).toFixed(seriesIndex === 0 ? 4 : 3)}` : '—'
      }},
    },
  }
})
</script>

<style scoped>
.page { background-color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; color: #0f172a; }
.page-body { padding: 24px 32px; display: flex; flex-direction: column; gap: 32px; }

/* ── Banner de Alerta ── */
.alert-banner {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 20px; border-radius: 12px;
  font-size: 13px; font-weight: 500;
}
.alert-banner.critico { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
.alert-banner.atencao { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; }
.alert-icon { font-size: 16px; flex-shrink: 0; }
.alert-text { flex: 1; }
.alert-valor { font-family: 'JetBrains Mono', monospace; font-weight: 700; }
.alert-link {
  font-size: 12px; font-weight: 700; padding: 6px 14px;
  border-radius: 8px; text-decoration: none; flex-shrink: 0;
  background: white; border: 1px solid currentColor; color: inherit;
  transition: opacity 0.2s;
}
.alert-link:hover { opacity: 0.7; }

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

.action-section { display: grid; grid-template-columns: 1.4fr 1fr; gap: 32px; align-items: start; }
.postos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }

/* ── Tabela de Grupo ── */
.grupo-table-wrap { overflow-x: auto; }
.grupo-table { width: 100%; border-collapse: collapse; }
.grupo-table thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 10px 10px;
  border-bottom: 1px solid #f1f5f9; white-space: nowrap;
}
.grupo-table th.right, .grupo-table td.right { text-align: right; }
.grupo-table tbody td {
  font-size: 13px; color: #334155; padding: 12px 10px;
  border-bottom: 1px solid #f8fafc; white-space: nowrap; vertical-align: middle;
}
.grupo-table tbody tr:last-child td { border-bottom: none; }
.grupo-table tbody tr:hover { background: #fcfcfc; }

.grupo-nome { font-weight: 600; color: #0f172a; }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.bold { font-weight: 700; color: #0f172a; }
.dim { color: #94a3b8; }
.green  { color: #059669; font-weight: 600; }
.orange { color: #ea580c; font-weight: 600; }
.red    { color: #ef4444; font-weight: 600; }

/* Mini bar */
.bar-track { height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
.bar-green  { background: #10b981; }
.bar-orange { background: #f59e0b; }
.bar-red    { background: #ef4444; }
.bar-gray   { background: #94a3b8; }

.empty { height: 200px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.5s infinite; }
.kpi-skel { height: 130px; }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

.footer { padding: 32px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; }

@media (max-width: 1200px) {
  .action-section, .postos-grid { grid-template-columns: 1fr; }
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
