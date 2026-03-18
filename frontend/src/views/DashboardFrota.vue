<template>
  <div class="page">

    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="section-name">Eficiência de Frota</span>
      </div>
      <div class="topbar-right">
        <div class="filter-inline">
          <label>Combustível</label>
          <select v-model="filtroCombustivel" @change="loadAll">
            <option value="">Todos</option>
            <option v-for="c in combustiveis" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
      </div>
    </header>

    <div class="page-header">
      <div>
        <h1>Eficiência de Frota</h1>
        <p class="page-sub">Custo por veículo, km/L, motoristas e alertas de uso</p>
      </div>
    </div>

    <div class="page-body">

      <!-- KPIs rápidos da frota -->
      <div class="kpis-grid" v-if="!lCusto">
        <div class="kpi-card">
          <div class="kpi-label">Veículos ativos</div>
          <div class="kpi-value">{{ custoPorPlaca.length }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Maior gasto (placa)</div>
          <div class="kpi-value">{{ custoPorPlaca[0]?.placa || '—' }}</div>
          <div class="kpi-sub">{{ fmtR(custoPorPlaca[0]?.total_valor) }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Melhor km/L</div>
          <div class="kpi-value mono">{{ eficiencia[0]?.km_litro?.toFixed(1) || '—' }}</div>
          <div class="kpi-sub">{{ eficiencia[0]?.placa || 'aguardando hodômetro' }}</div>
        </div>
        <div class="kpi-card alert" v-if="alertas.length > 0">
          <div class="kpi-label">Alertas detectados</div>
          <div class="kpi-value red">{{ alertas.length }}</div>
          <div class="kpi-sub">abastecimentos suspeitos</div>
        </div>
        <div class="kpi-card" v-else>
          <div class="kpi-label">Alertas detectados</div>
          <div class="kpi-value green">0</div>
          <div class="kpi-sub">nenhuma anomalia</div>
        </div>
      </div>
      <div v-else class="kpis-grid">
        <div v-for="i in 4" :key="i" class="kpi-card skel" style="height:80px" />
      </div>

      <!-- Custo por placa + km/L -->
      <div class="two-col">
        <section>
          <div class="section-heading">Custo por veículo (placa)</div>
          <TabelaCustoPorPlaca :data="custoPorPlaca" :loading="lCusto" />
        </section>
        <section>
          <div class="section-heading">Eficiência km/L</div>
          <TabelaEficiencia :data="eficiencia" :loading="lEficiencia" />
        </section>
      </div>

      <!-- Ranking motoristas -->
      <section>
        <div class="section-heading">Motoristas — preço médio pago</div>
        <GraficoMotoristas :data="motoristas" :loading="lMotoristas" />
      </section>

      <!-- Evolução mensal custo frota -->
      <section>
        <div class="section-heading">Evolução mensal da frota</div>
        <GraficoCustoFrota :data="custoMensal" :loading="lCustoMensal" />
      </section>

      <!-- Tendência de km/L por veículo -->
      <section>
        <div class="section-heading">Tendência de km/L por veículo</div>
        <GraficoTendenciaKml :data="tendenciaKml" :loading="lTendenciaKml" />
      </section>

      <!-- Frota por filial (BlueFleet) -->
      <section>
        <div class="section-heading">Distribuição por filial operacional</div>
        <FrotaPorFilial :data="frotaFilial" :loading="lFilial" />
      </section>

      <!-- Alertas -->
      <section v-if="alertas.length > 0 || lAlertas">
        <div class="section-heading">Alertas de uso — abastecimentos suspeitos</div>
        <TabelaAlertas :data="alertas" :loading="lAlertas" />
      </section>

    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchEficienciaKmLitro, fetchCustoPorPlaca, fetchRankingMotoristas, fetchAbastecimentosSuspeitos, fetchCustoMensalFrota, fetchVeiculosPorFilial, fetchTendenciaKml } from '../api/frota.js'
import { fetchFiltros } from '../api/combustivel.js'
import TabelaCustoPorPlaca from '../components/TabelaCustoPorPlaca.vue'
import TabelaEficiencia    from '../components/TabelaEficiencia.vue'
import GraficoMotoristas   from '../components/GraficoMotoristas.vue'
import GraficoTendenciaKml from '../components/GraficoTendenciaKml.vue'
import GraficoCustoFrota   from '../components/GraficoCustoFrota.vue'
import TabelaAlertas       from '../components/TabelaAlertas.vue'
import FrotaPorFilial      from '../components/FrotaPorFilial.vue'

const filtroCombustivel = ref('')
const combustiveis = ref([])

const custoPorPlaca = ref([])
const eficiencia    = ref([])
const motoristas    = ref([])
const alertas       = ref([])
const custoMensal   = ref([])
const frotaFilial   = ref([])
const tendenciaKml  = ref([])

const lCusto       = ref(true)
const lEficiencia  = ref(true)
const lMotoristas  = ref(true)
const lAlertas     = ref(true)
const lCustoMensal  = ref(true)
const lFilial       = ref(true)
const lTendenciaKml = ref(true)

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'

function getF() {
  return { combustivel: filtroCombustivel.value || undefined }
}

async function loadAll() {
  const f = getF()
  lCusto.value = lEficiencia.value = lMotoristas.value = lAlertas.value = lCustoMensal.value = lTendenciaKml.value = true

  await Promise.allSettled([
    fetchCustoPorPlaca(f).then(d => custoPorPlaca.value = d).finally(() => lCusto.value = false),
    fetchEficienciaKmLitro(f).then(d => eficiencia.value = d).finally(() => lEficiencia.value = false),
    fetchRankingMotoristas(f).then(d => motoristas.value = d).finally(() => lMotoristas.value = false),
    fetchAbastecimentosSuspeitos().then(d => alertas.value = d).finally(() => lAlertas.value = false),
    fetchCustoMensalFrota(f).then(d => custoMensal.value = d).finally(() => lCustoMensal.value = false),
    fetchVeiculosPorFilial().then(d => frotaFilial.value = d).finally(() => lFilial.value = false),
    fetchTendenciaKml().then(d => tendenciaKml.value = d).finally(() => lTendenciaKml.value = false),
  ])
}

onMounted(async () => {
  const filtros = await fetchFiltros()
  combustiveis.value = filtros.combustiveis || []
  await loadAll()
})
</script>

<style scoped>
.page { min-height: 100vh; display: flex; flex-direction: column; }

.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 40px; height: 52px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  position: sticky; top: 0; z-index: 10;
}
.topbar-left { display: flex; align-items: center; }
.section-name { font-size: 14px; font-weight: 500; color: var(--text-2); }
.topbar-right { display: flex; align-items: center; gap: 12px; }

.filter-inline { display: flex; align-items: center; gap: 8px; }
.filter-inline label { font-size: 11px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .03em; }
.filter-inline select {
  background: var(--surface); border: 1px solid var(--border); color: var(--text);
  font-size: 12px; padding: 5px 10px; border-radius: 7px; cursor: pointer;
  font-family: 'Inter', sans-serif; outline: none; min-width: 140px;
}

.page-header { display: flex; align-items: center; padding: 32px 40px 0; }
h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.page-sub { font-size: 13px; color: var(--text-3); margin-top: 4px; }

.page-body { padding: 28px 40px 40px; display: flex; flex-direction: column; gap: 28px; flex: 1; }

.section-heading {
  font-size: 12px; font-weight: 600; color: var(--text-3);
  text-transform: uppercase; letter-spacing: .06em;
  margin-bottom: 12px;
  display: flex; align-items: center; gap: 12px;
}
.section-heading::after { content:''; flex:1; height:1px; background: var(--border-subtle); }

.kpis-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }
.kpi-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px 24px; display: flex; flex-direction: column; gap: 4px;
}
.kpi-card.alert { border-color: rgba(239,68,68,.3); background: rgba(239,68,68,.04); }
.kpi-label { font-size: 11px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.kpi-value { font-size: 26px; font-weight: 700; color: var(--text); letter-spacing: -0.02em; line-height: 1.1; }
.kpi-value.red { color: var(--red); }
.kpi-value.green { color: var(--green); }
.kpi-value.mono { font-family: 'JetBrains Mono', monospace; }
.kpi-sub { font-size: 12px; color: var(--text-3); }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.footer {
  display: flex; padding: 16px 40px;
  border-top: 1px solid var(--border-subtle);
  font-size: 12px; color: var(--text-3);
}

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }

@media (max-width: 1100px) {
  .kpis-grid { grid-template-columns: repeat(2,1fr); }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 680px) {
  .topbar, .page-header, .page-body, .footer { padding-left: 16px; padding-right: 16px; }
  .kpis-grid { grid-template-columns: 1fr 1fr; }
}
</style>
