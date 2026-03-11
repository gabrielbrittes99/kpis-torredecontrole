<template>
  <div class="page">

    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="section-name">Visão da Diretoria</span>
      </div>
      <div class="topbar-right">
        <span class="last-update" v-if="kpis.ano_atual">Ano {{ kpis.ano_atual }}</span>
      </div>
    </header>

    <div class="page-header">
      <div>
        <h1>Visão da Diretoria</h1>
        <p class="page-sub">KPIs estratégicos, tendências anuais e potencial de economia</p>
      </div>
    </div>

    <div class="page-body">

      <!-- KPIs estratégicos -->
      <div class="kpis-exec" v-if="!lKpis">
        <div class="kpi-big">
          <div class="kpi-label">Gasto acumulado {{ kpis.ano_atual }}</div>
          <div class="kpi-value accent">{{ fmtR(kpis.gasto_ano) }}</div>
          <div class="kpi-sub">{{ fmtN(kpis.litros_ano) }} L · {{ kpis.meses_completos }} meses fechados</div>
        </div>
        <div class="kpi-big">
          <div class="kpi-label">Projeção anual</div>
          <div class="kpi-value">{{ fmtR(kpis.projecao_anual) }}</div>
          <div class="kpi-sub">Base: média de R$ {{ fmtR(kpis.media_mensal) }}/mês</div>
        </div>
        <div class="kpi-big">
          <div class="kpi-label">Mês de pico</div>
          <div class="kpi-value">{{ MESES[(kpis.mes_pico || 1) - 1] }}</div>
          <div class="kpi-sub">{{ fmtR(kpis.valor_pico) }}</div>
        </div>
        <div class="kpi-big">
          <div class="kpi-label">Diesel (% do gasto)</div>
          <div class="kpi-value">{{ kpis.pct_diesel?.toFixed(1) }}%</div>
          <div class="kpi-sub">{{ fmtR(kpis.gasto_diesel) }} de diesel</div>
        </div>
        <div class="kpi-big">
          <div class="kpi-label">Veículos ativos (mês)</div>
          <div class="kpi-value">{{ kpis.veiculos_ativos_mes }}</div>
          <div class="kpi-sub">abastecidos no mês atual</div>
        </div>
      </div>
      <div v-else class="kpis-exec">
        <div v-for="i in 5" :key="i" class="kpi-big skel" style="height:90px" />
      </div>

      <!-- Tendência 12 meses -->
      <section>
        <div class="section-heading">Tendência — últimos 12 meses</div>
        <GraficoTendencia :data="tendencia" :loading="lTendencia" />
      </section>

      <!-- Comparativo meses -->
      <section>
        <div class="section-heading">Mês atual vs mês anterior</div>
        <ComparativoMeses :data="comparativo" :loading="lComparativo" />
      </section>

      <!-- Mix combustíveis + Potencial economia -->
      <div class="two-col">
        <section>
          <div class="section-heading">Mix de combustíveis</div>
          <GraficoMixCombustiveis :data="mix" :loading="lMix" />
        </section>
        <section>
          <div class="section-heading">Potencial de economia</div>
          <SecaoPotencialEconomia :data="economia" :loading="lEconomia" />
        </section>
      </div>

      <!-- Benchmark ANP -->
      <section>
        <div class="section-heading">Benchmark vs mercado ANP</div>
        <BenchmarkANP :data="benchmark" :resumo="benchmarkResumo" :loading="lBenchmark" />
      </section>

      <!-- Top 5 veículos -->
      <section>
        <div class="section-heading">Top 5 veículos mais caros (histórico)</div>
        <div class="top5-grid" v-if="!lKpis && kpis.top5_veiculos?.length">
          <div v-for="(v, i) in kpis.top5_veiculos" :key="v.placa" class="top5-card">
            <div class="top5-rank">#{{ i + 1 }}</div>
            <div class="top5-placa mono">{{ v.placa }}</div>
            <div class="top5-model">{{ v.modelo || '—' }}</div>
            <div class="top5-valor">{{ fmtR(v.total_valor) }}</div>
            <div class="top5-sub">{{ fmtN(v.total_litros) }} L · {{ v.qtd_abastecimentos }} abast.</div>
            <div class="top5-bar-track">
              <div class="top5-bar-fill" :style="{ width: (v.total_valor / kpis.top5_veiculos[0].total_valor * 100) + '%' }" />
            </div>
          </div>
        </div>
        <div v-else-if="lKpis" class="top5-grid">
          <div v-for="i in 5" :key="i" class="top5-card skel" style="height:120px" />
        </div>
      </section>

    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchKpisEstrategicos, fetchTendencia12Meses, fetchPotencialEconomia, fetchMixCombustiveis, fetchComparativoMeses, fetchBenchmarkComparativo, fetchBenchmarkResumo } from '../api/diretoria.js'
import GraficoTendencia       from '../components/GraficoTendencia.vue'
import ComparativoMeses       from '../components/ComparativoMeses.vue'
import GraficoMixCombustiveis from '../components/GraficoMixCombustiveis.vue'
import SecaoPotencialEconomia from '../components/SecaoPotencialEconomia.vue'
import BenchmarkANP           from '../components/BenchmarkANP.vue'

const MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

const kpis           = ref({})
const tendencia      = ref([])
const comparativo    = ref({})
const mix            = ref([])
const economia       = ref({})
const benchmark      = ref([])
const benchmarkResumo = ref({})

const lKpis        = ref(true)
const lTendencia   = ref(true)
const lComparativo = ref(true)
const lMix         = ref(true)
const lEconomia    = ref(true)
const lBenchmark   = ref(true)

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

onMounted(() => {
  Promise.allSettled([
    fetchKpisEstrategicos().then(d => kpis.value = d).finally(() => lKpis.value = false),
    fetchTendencia12Meses().then(d => tendencia.value = d).finally(() => lTendencia.value = false),
    fetchComparativoMeses().then(d => comparativo.value = d).finally(() => lComparativo.value = false),
    fetchMixCombustiveis().then(d => mix.value = d).finally(() => lMix.value = false),
    fetchPotencialEconomia().then(d => economia.value = d).finally(() => lEconomia.value = false),
    fetchBenchmarkComparativo().then(d => benchmark.value = d).finally(() => lBenchmark.value = false),
    fetchBenchmarkResumo().then(d => benchmarkResumo.value = d).finally(() => { if (lBenchmark.value) lBenchmark.value = false }),
  ])
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
.section-name { font-size: 14px; font-weight: 500; color: var(--text-2); }
.last-update { font-size: 12px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; }

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

/* KPIs exec */
.kpis-exec { display: grid; grid-template-columns: repeat(5,1fr); gap: 12px; }
.kpi-big {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px 24px; display: flex; flex-direction: column; gap: 4px;
}
.kpi-label { font-size: 11px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.kpi-value { font-size: 24px; font-weight: 700; color: var(--text); letter-spacing: -0.02em; line-height: 1.1; margin: 4px 0; }
.kpi-value.accent { color: var(--accent); }
.kpi-sub { font-size: 12px; color: var(--text-3); }

/* Top 5 grid */
.top5-grid { display: grid; grid-template-columns: repeat(5,1fr); gap: 12px; }
.top5-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px; display: flex; flex-direction: column; gap: 4px;
}
.top5-rank { font-size: 11px; color: var(--text-3); font-weight: 600; }
.top5-placa { font-size: 16px; font-weight: 700; color: var(--text); letter-spacing: .04em; margin: 4px 0 2px; }
.top5-model { font-size: 11px; color: var(--text-3); margin-bottom: 8px; }
.top5-valor { font-size: 20px; font-weight: 700; color: var(--accent); }
.top5-sub { font-size: 11px; color: var(--text-3); margin-bottom: 8px; }
.top5-bar-track { height: 3px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; margin-top: auto; }
.top5-bar-fill { height: 100%; background: var(--accent); border-radius: 2px; opacity: .6; transition: width .8s ease; }

/* two-col */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.footer {
  display: flex; padding: 16px 40px;
  border-top: 1px solid var(--border-subtle);
  font-size: 12px; color: var(--text-3);
}

.mono { font-family: 'JetBrains Mono', monospace; }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }

@media (max-width: 1200px) {
  .kpis-exec { grid-template-columns: repeat(3,1fr); }
  .top5-grid  { grid-template-columns: repeat(3,1fr); }
}
@media (max-width: 900px) {
  .kpis-exec { grid-template-columns: repeat(2,1fr); }
  .top5-grid  { grid-template-columns: repeat(2,1fr); }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 680px) {
  .topbar, .page-header, .page-body, .footer { padding-left: 16px; padding-right: 16px; }
  .kpis-exec, .top5-grid { grid-template-columns: 1fr 1fr; }
}
</style>
