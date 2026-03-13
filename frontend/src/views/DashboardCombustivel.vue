<template>
  <div class="page">

    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="section-name">Visão Gerencial · Combustível</span>
      </div>
      <div class="topbar-right">
        <span class="last-update refresh-info" v-if="refreshInfo">{{ refreshInfo }}</span>
        <span class="last-update" v-else-if="ultimaAtt">Atualizado às {{ ultimaAtt }}</span>
        <button class="btn-ghost" @click="refreshCache" :disabled="refreshing">
          <span :class="{ spin: refreshing }">↻</span>
          {{ refreshing ? 'Atualizando…' : 'Atualizar' }}
        </button>
      </div>
    </header>

    <!-- Page title -->
    <div class="page-header">
      <div>
        <h1>Visão Gerencial</h1>
        <p class="page-sub">Análise de abastecimentos · {{ dataRange }}</p>
      </div>
      <div class="month-badge" v-if="kpis.mes_ref">
        {{ MESES[kpis.mes_ref - 1] }} {{ kpis.ano_ref }}
      </div>
    </div>

    <!-- Filtros -->
    <div class="filters">
      <div class="filter-item">
        <label>Mês</label>
        <select v-model="filtroMes" @change="loadAll">
          <option v-for="m in filtros.meses_disponiveis" :key="m" :value="m">{{ fmtMesSel(m) }}</option>
        </select>
      </div>
      <div class="filter-item">
        <label>Combustível</label>
        <select v-model="filtroCombustivel" @change="loadAll">
          <option value="">Todos</option>
          <option v-for="c in filtros.combustiveis" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <div class="filter-item">
        <label>Placa</label>
        <select v-model="filtroPlaca" @change="loadAll">
          <option value="">Todas</option>
          <option v-for="p in filtros.placas" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
    </div>

    <div class="page-body">
      <!-- KPIs -->
      <div class="kpis-grid">
        <KpiCard label="Total do mês"    :value="kpis.total_valor"        format="currency" :loading="lKpis" />
        <KpiCard label="Total litros"    :value="kpis.total_litros"       format="integer"  :loading="lKpis" />
        <KpiCard label="Preço médio / L" :value="kpis.preco_medio"        format="decimal"  :loading="lKpis" :delta="kpis.variacao_preco_pct" :delta-invert="true" />
        <KpiCard label="Abastecimentos"  :value="kpis.qtd_abastecimentos" format="integer"  :loading="lKpis" />
      </div>

      <div class="section-heading" style="margin-top: 12px; margin-bottom: 12px;">KPIs Estratégicos</div>
      <div class="kpis-grid">
        <KpiCard label="Custo por KM rodado"   :value="kpis_est.custo_por_km"             format="decimal"  :loading="lKpisEst" sub="KMs válidos apurados" />
        <KpiCard label="Saving do Mês vs ANP"  :value="kpis_est.saving_real"              format="currency" :loading="lKpisEst" sub="Economia gerada" />
        <KpiCard label="Fora de Rota"          :value="kpis_est.fora_de_rota_qtd"         format="integer"  :loading="lKpisEst" :sub="kpis_est.fora_de_rota_pct + '% dos abastecimentos'" />
        <KpiCard label="Inflação Rede"         :value="kpis_est.var_forn_pct"             format="decimal"  :loading="lKpisEst" :delta="kpis_est.var_forn_pct" :delta-invert="true" sub="var. mês anterior" />
      </div>

      <!-- Gráficos -->
      <div class="charts-top">
        <GraficoDiario :data="diario" :loading="lDiario" />
        <GraficoRosca  :data="porTipo" :loading="lPorTipo" />
      </div>
      <GraficoHistorico :data="historico" :loading="lHistorico" />

      <!-- Dia útil vs Fim de semana -->
      <GraficoDiaSemana :data="diaSemana" :loading="lDiaSemana" />

      <!-- Resumo por período -->
      <section>
        <div class="section-heading">Custo por período · por tipo de combustível</div>
        <SecaoResumoPeriodo :filtros="getF()" />
      </section>

      <!-- Projeção -->
      <section>
        <div class="section-heading">Projeção de fechamento</div>
        <SecaoProjecao :kpis="kpis" :loading="lKpis" />
      </section>

      <!-- Histórico real + Simulador -->
      <section>
        <div class="section-heading">Histórico real · projeção e simulação de preços</div>
        <SecaoImpactoPreco :filtros="getF()" />
      </section>

      <!-- Tabela -->
      <section>
        <div class="section-heading">Top postos</div>
        <TabelaPostos :data="topPostos" :loading="lPostos" />
      </section>

    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle</span>
    </footer>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import KpiCard         from '../components/KpiCard.vue'
import GraficoDiario   from '../components/GraficoDiario.vue'
import GraficoRosca    from '../components/GraficoRosca.vue'
import GraficoHistorico from '../components/GraficoHistorico.vue'
import SecaoProjecao     from '../components/SecaoProjecao.vue'
import SecaoResumoPeriodo from '../components/SecaoResumoPeriodo.vue'
import SecaoImpactoPreco from '../components/SecaoImpactoPreco.vue'
import TabelaPostos     from '../components/TabelaPostos.vue'
import GraficoDiaSemana from '../components/GraficoDiaSemana.vue'
import AlertasList      from '../components/AlertasList.vue'
import { fetchFiltros, fetchKpis, fetchDiario, fetchPorTipo, fetchHistoricoMensal, fetchTopPostos, forceRefresh, fetchCustoDiaSemana, fetchKpisEstrategicos } from '../api/combustivel.js'
import { fetchAlertas } from '../api/alertas.js'

const MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

const filtros          = ref({ combustiveis: [], placas: [], meses_disponiveis: [] })
const filtroMes        = ref('')
const filtroCombustivel = ref('')
const filtroPlaca      = ref('')
const refreshing       = ref(false)
const refreshInfo      = ref('')

const kpis      = ref({})
const kpis_est  = ref({})
const alertas   = ref([])
const diario    = ref([])
const porTipo   = ref([])
const historico = ref([])
const topPostos   = ref([])
const diaSemana   = ref([])

const lKpis      = ref(true)
const lKpisEst   = ref(true)
const lDiario    = ref(true)
const lPorTipo   = ref(true)
const lHistorico = ref(true)
const lPostos    = ref(true)
const lDiaSemana = ref(true)

const fmtMesSel = s => { const [y, m] = s.split('-'); return `${MESES[+m-1]} ${y}` }

const ultimaAtt = computed(() => {
  if (!kpis.value.ultima_atualizacao) return ''
  return new Date(kpis.value.ultima_atualizacao).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
})

const dataRange = computed(() => {
  const ms = filtros.value.meses_disponiveis
  if (!ms?.length) return '...'
  const [ay, am] = ms[0].split('-')
  const [by, bm] = ms.at(-1).split('-')
  return `${MESES[+am-1]} ${ay} → ${MESES[+bm-1]} ${by}`
})

function getF() {
  return {
    combustivel: filtroCombustivel.value || undefined,
    placa: filtroPlaca.value || undefined,
  }
}

function getMesAno() {
  if (!filtroMes.value) return {}
  const [ano, mes] = filtroMes.value.split('-')
  return { mes: +mes, ano: +ano }
}

async function loadAll() {
  const f = getF()
  const { mes, ano } = getMesAno()
  lKpis.value = lKpisEst.value = lDiario.value = lPorTipo.value = lHistorico.value = lPostos.value = lDiaSemana.value = true

  await Promise.allSettled([
    fetchKpis({ mes, ano, ...f }).then(d => kpis.value = d).finally(() => lKpis.value = false),
    fetchKpisEstrategicos({ mes, ano, ...f }).then(d => kpis_est.value = d).finally(() => lKpisEst.value = false),
    fetchAlertas().then(d => alertas.value = d),
    fetchDiario(mes, ano, f).then(d => diario.value = d).finally(() => lDiario.value = false),
    fetchPorTipo(f).then(d => porTipo.value = d).finally(() => lPorTipo.value = false),
    fetchHistoricoMensal(f, true).then(d => historico.value = d).finally(() => lHistorico.value = false),
    fetchTopPostos(10, f).then(d => topPostos.value = d).finally(() => lPostos.value = false),
    fetchCustoDiaSemana(f).then(d => diaSemana.value = d).finally(() => lDiaSemana.value = false),
  ])
}

async function refreshCache() {
  refreshing.value = true
  refreshInfo.value = ''
  try {
    const r = await forceRefresh()
    const dataMaisRecente = r.data_mais_recente
      ? new Date(r.data_mais_recente).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
      : '—'
    refreshInfo.value = `${r.total_registros?.toLocaleString('pt-BR')} registros · último: ${dataMaisRecente}`
  } catch {}
  await loadAll()
  refreshing.value = false
}

onMounted(async () => {
  filtros.value = await fetchFiltros()
  if (filtros.value.meses_disponiveis?.length)
    filtroMes.value = filtros.value.meses_disponiveis.at(-1)
  await loadAll()
})
</script>

<style scoped>
.page { min-height: 100vh; display: flex; flex-direction: column; }

/* Topbar */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 40px; height: 52px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  position: sticky; top: 0; z-index: 10;
}
.topbar-left { display: flex; align-items: center; gap: 10px; }
.section-name { font-size: 14px; font-weight: 500; color: var(--text-2); }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.last-update { font-size: 12px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; }
.btn-ghost {
  display: flex; align-items: center; gap: 6px;
  background: transparent; border: 1px solid var(--border); color: var(--text-2);
  font-size: 12px; padding: 6px 12px; border-radius: 7px; cursor: pointer;
  font-family: 'Inter', sans-serif; transition: border-color .15s, color .15s;
}
.btn-ghost:hover:not(:disabled) { border-color: var(--text-3); color: var(--text); }
.btn-ghost:disabled { opacity: .4; cursor: not-allowed; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Page header */
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 32px 40px 0;
}
h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.page-sub { font-size: 13px; color: var(--text-3); margin-top: 4px; }
.month-badge {
  font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 500;
  color: var(--accent); background: var(--accent-bg); border: 1px solid rgba(249,115,22,.2);
  padding: 5px 14px; border-radius: 20px;
}

/* Filtros */
.filters {
  display: flex; gap: 16px; align-items: flex-end;
  padding: 20px 40px 0; flex-wrap: wrap;
}
.filter-item { display: flex; flex-direction: column; gap: 5px; }
.filter-item label { font-size: 11px; font-weight: 500; color: var(--text-3); letter-spacing: .03em; text-transform: uppercase; }
.filter-item select {
  background: var(--surface); border: 1px solid var(--border); color: var(--text);
  font-size: 13px; padding: 7px 12px; border-radius: 8px; cursor: pointer;
  font-family: 'Inter', sans-serif; outline: none; transition: border-color .15s;
  min-width: 140px;
}
.filter-item select:focus { border-color: var(--accent); }

/* Body */
.page-body { padding: 28px 40px 40px; display: flex; flex-direction: column; gap: 28px; flex: 1; }

/* Section heading */
.section-heading {
  font-size: 12px; font-weight: 600; color: var(--text-3);
  text-transform: uppercase; letter-spacing: .06em;
  margin-bottom: 12px;
  display: flex; align-items: center; gap: 12px;
}
.section-heading::after { content:''; flex:1; height:1px; background: var(--border-subtle); }

/* KPIs */
.kpis-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }

/* Charts */
.charts-top { display: grid; grid-template-columns: 2fr 1fr; gap: 12px; }

/* Footer */
.footer {
  display: flex; justify-content: space-between;
  padding: 16px 40px; border-top: 1px solid var(--border-subtle);
  font-size: 12px; color: var(--text-3);
}

@media (max-width: 1100px) {
  .kpis-grid { grid-template-columns: repeat(2,1fr); }
  .charts-top { grid-template-columns: 1fr; }
}
@media (max-width: 680px) {
  .topbar, .page-header, .filters, .page-body, .footer { padding-left: 16px; padding-right: 16px; }
  .kpis-grid { grid-template-columns: 1fr; }
}
</style>
