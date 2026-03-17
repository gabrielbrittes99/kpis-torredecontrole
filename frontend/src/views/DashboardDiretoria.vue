<template>
  <div class="page executive-theme animate-in">

    <!-- Topbar: Padronizada -->
    <GlobalTopbar
      title="Diretoria"
      subtitle="Visão estratégica de saúde e performance"
      :show-period="true"
      :show-filters="true"
    />

    <div class="page-body">
      
      <!-- HERO SECTION: Os Números que Importam -->
      <div class="kpi-pro-grid">
        <KpiCardPro
          title="Saving Real (Mês)"
          :value="kpis.saving_acumulado_mes || 0"
          format="currency"
          theme="primary"
          description="Performance Negociação (vs ANP)"
        />
        <KpiCardPro
          title="Saúde da Operação"
          :value="kpis.score_saude || 100"
          format="number"
          unit="%"
          :trendValue="0"
          theme="dark"
        />
        <KpiCardPro
          title="Projeção (Mês)"
          :value="kpis.projecao_mes_atual || 0"
          format="currency"
          :description="'Baseado no Real até dia ' + (kpis.dia_referencia_proj || '—')"
        />
        <KpiCardPro
          title="Custo/KM Global"
          :value="kpis.custo_por_km || 0"
          format="currency"
          :decimals="3"
          :description="'Gasto Year-to-Date'"
        />
      </div>

      <!-- Performance Financeira (Comparativos Estratégicos) -->
      <section class="v-block section-performance">
        <div class="section-title">PERFORMANCE FINANCEIRA (MESMO PERÍODO EQUIVALENTE)</div>
        <div class="performance-grid">
          
          <!-- Card: Gasto Financeiro -->
          <div class="metric-comp-card">
            <div class="metric-header">
              <span class="label">GASTO FINANCEIRO (REAL)</span>
              <span class="unit">MÊS ATÉ HOJE</span>
            </div>
            <div class="metric-value">{{ fmtR(comparativo.mes_atual?.total_valor) }}</div>
            <div class="metric-comparisons">
              <div class="comp-row">
                <span class="comp-label">vs Mês Anterior</span>
                <span class="comp-val" :class="getTrendClass(comparativo.variacao?.valor_pct)">
                  {{ comparativo.variacao?.valor_pct > 0 ? '▲' : '▼' }} {{ Math.abs(comparativo.variacao?.valor_pct) }}%
                </span>
              </div>
              <div class="comp-row">
                <span class="comp-label">vs Média 3 Meses</span>
                <span class="comp-val" :class="getTrendClass(comparativo.variacao_vs_media?.valor_pct)">
                  {{ comparativo.variacao_vs_media?.valor_pct > 0 ? '▲' : '▼' }} {{ Math.abs(comparativo.variacao_vs_media?.valor_pct) }}%
                </span>
              </div>
            </div>
          </div>

          <!-- Card: Volume de Consumo -->
          <div class="metric-comp-card">
            <div class="metric-header">
              <span class="label">VOLUME DE CONSUMO</span>
              <span class="unit">LITROS BOMBEADOS</span>
            </div>
            <div class="metric-value">{{ fmtN(comparativo.mes_atual?.total_litros) }} <span class="sub-unit">L</span></div>
            <div class="metric-comparisons">
              <div class="comp-row">
                <span class="comp-label">vs Mês Anterior</span>
                <span class="comp-val" :class="getTrendClass(comparativo.variacao?.litros_pct)">
                  {{ comparativo.variacao?.litros_pct > 0 ? '▲' : '▼' }} {{ Math.abs(comparativo.variacao?.litros_pct) }}%
                </span>
              </div>
              <div class="comp-row">
                <span class="comp-label">vs Média 3 Meses</span>
                <span class="comp-val" :class="getTrendClass(comparativo.variacao_vs_media?.litros_pct)">
                  {{ comparativo.variacao_vs_media?.litros_pct > 0 ? '▲' : '▼' }} {{ Math.abs(comparativo.variacao_vs_media?.litros_pct) }}%
                </span>
              </div>
            </div>
          </div>

          <!-- Card: Custo por KM -->
          <div class="metric-comp-card">
            <div class="metric-header">
              <span class="label">CUSTO POR QUILÔMETRO</span>
              <span class="unit">EFICIÊNCIA REAL</span>
            </div>
            <div class="metric-value">R$ {{ comparativo.mes_atual?.custo_km?.toFixed(3) }} <span class="sub-unit">/KM</span></div>
            <div class="metric-comparisons">
              <div class="comp-row">
                <span class="comp-label">vs Mês Anterior</span>
                <span class="comp-val" :class="getTrendClass(comparativo.variacao?.custo_km_abs, 0.01)">
                  {{ comparativo.variacao?.custo_km_abs > 0 ? '▲' : '▼' }} R$ {{ Math.abs(comparativo.variacao?.custo_km_abs).toFixed(3) }}
                </span>
              </div>
              <div class="comp-row">
                <span class="comp-label">vs Média 3 Meses</span>
                <span class="comp-val" :class="getTrendClass(comparativo.variacao_vs_media?.custo_km_abs, 0.01)">
                  {{ comparativo.variacao_vs_media?.custo_km_abs > 0 ? '▲' : '▼' }} R$ {{ Math.abs(comparativo.variacao_vs_media?.custo_km_abs).toFixed(3) }}
                </span>
              </div>
            </div>
          </div>

        </div>
      </section>

      <!-- MIDDLE SECTION: Análise Profunda -->
      <div class="middle-layout">
        
        <!-- Coluna Esquerda: Gráficos -->
        <div class="col-charts">
          <section class="v-block">
             <div class="section-title">TENDÊNCIA DE CUSTO (12 MESES)</div>
             <GraficoTendencia :data="tendencia" :loading="lTendencia" />
          </section>

          <section class="v-block">
             <div class="section-title">BENCHMARK DE MERCADO (ANP)</div>
             <BenchmarkANP :data="benchmark" :resumo="kpis.saving_resumo_anp" :loading="lBenchmark" />
          </section>

          <!-- MATRIZ DE GASTOS POR FILIAL -->
          <section class="v-block">
             <div class="section-title">MATRIZ DE GASTOS POR FILIAL (REAL MÊS vs MÉDIA 3M)</div>
             <div class="spreadsheet-wrap">
               <table class="spreadsheet">
                 <thead>
                   <tr>
                     <th class="sticky-col">Filial</th>
                     <th colspan="2">Diesel</th>
                     <th colspan="2">Etanol</th>
                     <th colspan="2">Arla</th>
                     <th colspan="2">Gasolina</th>
                     <th class="total-head">Total Real</th>
                   </tr>
                   <tr class="sub-head">
                     <th class="sticky-col"></th>
                     <th>Real</th><th>vs 3M</th>
                     <th>Real</th><th>vs 3M</th>
                     <th>Real</th><th>vs 3M</th>
                     <th>Real</th><th>vs 3M</th>
                     <th>(Mês)</th>
                   </tr>
                 </thead>
                 <tbody>
                   <tr v-for="f in filiais" :key="f.filial">
                     <td class="sticky-col filial-name">{{ f.filial }}</td>
                     <td class="val">{{ fmtR(f.dados.DIESEL.valor) }}</td>
                     <td class="trend" :class="getTrendClass(f.dados.DIESEL.desvio_pct)">{{ f.dados.DIESEL.desvio_pct }}%</td>
                     
                     <td class="val">{{ fmtR(f.dados.ETANOL.valor) }}</td>
                     <td class="trend" :class="getTrendClass(f.dados.ETANOL.desvio_pct)">{{ f.dados.ETANOL.desvio_pct }}%</td>
                     
                     <td class="val">{{ fmtR(f.dados.ARLA.valor) }}</td>
                     <td class="trend" :class="getTrendClass(f.dados.ARLA.desvio_pct)">{{ f.dados.ARLA.desvio_pct }}%</td>
                     
                     <td class="val">{{ fmtR(f.dados.GASOLINA.valor) }}</td>
                     <td class="trend" :class="getTrendClass(f.dados.GASOLINA.desvio_pct)">{{ f.dados.GASOLINA.desvio_pct }}%</td>
                     
                     <td class="total-val">{{ fmtR(f.total_mes) }}</td>
                   </tr>
                 </tbody>
               </table>
             </div>
          </section>
        </div>

        <!-- Coluna Direita: Detalhes Executivos -->
        <aside class="col-aside">
          
          <!-- Potencial de Saving (Oportunidade) -->
          <div class="v-block opportunity-block">
            <div class="label-tiny mono">OPORTUNIDADE DE SAVING</div>
            <div class="opp-value">{{ fmtR(economia.economia_potencial) }}</div>
            <p class="opp-desc">Economia possível se todos abastecessem no posto mais barato da região.</p>
            <div class="opp-bar">
               <div class="opp-fill" :style="{ width: economia.economia_pct + '%' }"></div>
            </div>
            <div class="opp-footer mono">{{ economia.economia_pct }}% do gasto total</div>
          </div>

          <!-- IA de Mercado (Migrado de Vigilância) -->
          <div class="v-block side-block ia-block">
            <div class="ia-header">
              <div class="label-tiny mono" style="margin-bottom:0">INTELIGÊNCIA DE MERCADO <span class="ia-live-badge">IA AO VIVO</span></div>
              <button class="btn-update mono" @click="fetchIntel" :disabled="iaLoading">
                <span class="icon" :class="{ rotate: iaLoading }">⟳</span>
                {{ iaLoading ? 'Consultando...' : 'Atualizar' }}
              </button>
            </div>
            <div v-if="iaLoading" class="ia-loading mono">
              Consultando inteligência...
            </div>
            <div v-else-if="intel" class="ia-content">
              <div class="ia-resumo mono">
                 <span class="trend-icon">{{ intel.tendencia === 'alta' ? '▲' : '→' }}</span>
                 {{ intel.resumo }}
              </div>
              <div v-for="(n, i) in intel.noticias" :key="i" class="ia-card" :class="n.impacto">
                <div class="ia-n-header">
                  <span class="fonte mono">{{ n.fonte }}</span>
                  <span class="impacto mono">{{ n.impacto }}</span>
                </div>
                <div class="ia-n-title">{{ n.titulo }}</div>
                <div class="ia-n-market mono" v-if="n.brent_usd">
                  Brent: {{ n.brent_usd }} · Câmbio: {{ n.cambio }}
                </div>
              </div>
            </div>
          </div>

          <!-- Mix de Operação Mês -->
          <div class="v-block">
             <div class="label-tiny mono">MIX DE COMBUSTÍVEL (ESTE MÊS)</div>
             <GraficoMixCombustiveis :data="mix.mes" :loading="lMix" />
          </div>

          <!-- Mix de Operação Ano -->
          <div class="v-block">
             <div class="label-tiny mono">MIX DE COMBUSTÍVEL (ACUMULADO ANO)</div>
             <GraficoMixCombustiveis :data="mix.ano" :loading="lMix" />
          </div>

        </aside>
      </div>

    </div>

    <footer class="footer">
      <span>Relatório Estratégico · Gerado em {{ new Date().toLocaleDateString() }}</span>
      <span class="mono">CONFIDENCIAL // GRITSCH LOGÍSTICA</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useFiltrosStore } from '../stores/filtros'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import { useMercadoIA } from '../composables/useMercadoIA'
import KpiCardPro from '../components/KpiCardPro.vue'
import { 
  fetchKpisEstrategicos, 
  fetchTendencia12Meses, 
  fetchPotencialEconomia, 
  fetchMixCombustiveis, 
  fetchComparativoMeses, 
  fetchBenchmarkComparativo,
  fetchGastosFiliais
} from '../api/diretoria.js'
import GraficoTendencia       from '../components/GraficoTendencia.vue'
import GraficoMixCombustiveis from '../components/GraficoMixCombustiveis.vue'
import BenchmarkANP           from '../components/BenchmarkANP.vue'

const { intel, loading: iaLoading, fetchIntel } = useMercadoIA()

const MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
const anosDisponiveis = [new Date().getFullYear(), new Date().getFullYear() - 1]

const store = useFiltrosStore()

const kpis           = ref({ score_saude: 100 })
const tendencia      = ref([])
const comparativo    = ref({})
const mix            = ref({ mes: [], ano: [] })
const economia       = ref({})
const benchmark      = ref([])
const filiais        = ref([])

const lTendencia   = ref(true)
const lComparativo = ref(true)
const lMix         = ref(true)
const lBenchmark   = ref(true)
const lFiliais     = ref(true)

const fmtR = v => v != null ? 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'
const fmtRPrecise = v => v != null ? 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 3, maximumFractionDigits: 3 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

const getScoreColor = s => {
  if (s > 80) return '#10b981' // Green
  if (s > 50) return '#f59e0b' // Yellow
  return '#ef4444' // Red
}

const getTrendClass = (val, threshold = 2) => {
  if (val == null || Math.abs(val) < threshold) return 'neutral'
  return val > 0 ? 'red' : 'green'
}

async function refreshData() {
  const p = { mes: store.selecao.mes, ano: store.selecao.ano }
  lTendencia.value = true
  lComparativo.value = true
  lMix.value = true
  lBenchmark.value = true
  lFiliais.value = true
  
  Promise.allSettled([
    fetchKpisEstrategicos(p).then(d => kpis.value = d),
    fetchTendencia12Meses(p).then(d => { tendencia.value = d; lTendencia.value = false }),
    fetchComparativoMeses(p).then(d => { comparativo.value = d; lComparativo.value = false }),
    fetchMixCombustiveis(p).then(d => { mix.value = d; lMix.value = false }),
    fetchPotencialEconomia(p).then(d => economia.value = d),
    fetchBenchmarkComparativo(p).then(d => { benchmark.value = d; lBenchmark.value = false }),
    fetchGastosFiliais(p).then(d => { filiais.value = d; lFiliais.value = false }),
  ])
}

watch(() => store.selecao, () => refreshData(), { deep: true })

onMounted(() => {
  refreshData()
  fetchIntel()
})
</script>

<style scoped>
.page { 
  min-height: 100vh; 
  background: #f8fafc; 
  color: #0f172a;
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
}

/* Theme - Padronizado com as outras telas */
.executive-theme {
  --accent: #f97316;
  --surface: #ffffff;
  --border: #e2e8f0;
  --text-dim: #64748b;
}

/* Topbar styles removed as they are now in GlobalTopbar */

/* Body */
.page-body { padding: 24px 32px; flex: 1; }

.kpi-pro-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}

.saving-card { border-left: 6px solid #10b981; }
.saving-card .card-value { color: #10b981; }
.cost-km-card { border-left: 6px solid #f97316; }
.cost-km-card .card-value { color: #f97316; }
.efficiency-card { border-left: 6px solid #f97316; }
.projection-mes-card { border-left: 6px solid #f43f5e; }
.projection-card { border-left: 6px solid #8b5cf6; }

.projection-card { border-left: 6px solid #8b5cf6; }

/* Middle Layout */
.middle-layout {
  display: grid; grid-template-columns: 1fr 340px; gap: 40px;
}

.v-block {
  background: white; border: 1px solid var(--border); border-radius: 20px;
  padding: 32px; margin-bottom: 24px;
}
.section-title {
  font-size: 11px; font-weight: 700; color: var(--text-dim); letter-spacing: 0.08em;
  margin-bottom: 24px; text-transform: uppercase; border-left: 3px solid #f97316;
  padding-left: 12px;
}

.label-tiny { font-size: 9px; font-weight: 800; color: var(--text-dim); margin-bottom: 12px; }

/* IA Block Styles */
.ia-block { padding: 24px; background: linear-gradient(180deg, white 0%, #f8fafc 100%); }
.ia-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.ia-live-badge { background: #f97316; color: white; padding: 2px 6px; border-radius: 4px; font-size: 8px; margin-left: 8px; }
.btn-update { background: transparent; border: 1px solid var(--border); border-radius: 6px; padding: 4px 8px; font-size: 9px; cursor: pointer; color: var(--text-dim); display: flex; align-items: center; gap: 4px; }
.btn-update:hover { background: #f1f5f9; }
.btn-update .icon.rotate { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.ia-loading { padding: 40px 0; text-align: center; font-size: 11px; color: var(--text-dim); }
.ia-content { display: flex; flex-direction: column; gap: 16px; }
.ia-resumo { font-size: 11px; color: #1e293b; background: white; padding: 12px; border-radius: 8px; border: 1px dashed var(--border); line-height: 1.5; }
.trend-icon { font-weight: 800; margin-right: 4px; color: #f97316; }
.ia-card { background: white; border: 1px solid var(--border); border-radius: 8px; padding: 16px; border-left: 3px solid var(--border); }
.ia-card.ALTA { border-left-color: #ef4444; }
.ia-card.BAIXA { border-left-color: #10b981; }
.ia-n-header { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 9px; }
.fonte { font-weight: 700; color: var(--text-dim); }
.impacto { font-weight: 800; padding: 2px 6px; border-radius: 4px; background: #f1f5f9; }
.ia-card.ALTA .impacto { color: #ef4444; background: #fef2f2; }
.ia-card.BAIXA .impacto { color: #10b981; background: #ecfdf5; }
.ia-n-title { font-size: 12px; font-weight: 600; color: #1e293b; margin-bottom: 12px; line-height: 1.4; }
.ia-n-market { font-size: 10px; color: var(--text-dim); display: flex; gap: 12px; }

/* Performance Section */
.section-performance {
  background: transparent; padding: 0; border: none; margin-bottom: 40px;
}
.performance-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
}
.metric-comp-card {
  background: white; border: 1px solid var(--border); border-radius: 20px;
  padding: 24px; display: flex; flex-direction: column;
}
.metric-header { display: flex; flex-direction: column; margin-bottom: 16px; }
.metric-header .label { font-size: 10px; font-weight: 700; color: var(--text-dim); letter-spacing: 0.1em; }
.metric-header .unit { font-size: 9px; color: var(--text-dim); opacity: 0.7; }

.metric-value { font-size: 32px; font-weight: 800; color: #1e293b; letter-spacing: -0.02em; margin-bottom: 20px; }
.metric-value .sub-unit { font-size: 14px; color: var(--text-dim); }

.metric-comparisons { border-top: 1px solid #f1f5f9; padding-top: 16px; display: flex; flex-direction: column; gap: 8px; }
.comp-row { display: flex; justify-content: space-between; align-items: center; }
.comp-label { font-size: 11px; color: var(--text-dim); }
.comp-val { font-size: 13px; font-weight: 700; }
.comp-val.red { color: #ef4444; }
.comp-val.green { color: #10b981; }

.green { color: #10b981; }
.red { color: #ef4444; }
.neutral { color: var(--text-dim); }

/* Spreadsheet Table Style */
.spreadsheet-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
}
.spreadsheet {
  width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif;
}
.spreadsheet th {
  background: #f8fafc; color: var(--text-dim); font-size: 10px;
  text-transform: uppercase; font-weight: 700; padding: 12px 14px;
  border: 1px solid var(--border); text-align: center;
}
.spreadsheet .sub-head th { padding: 8px; font-size: 9px; }
.spreadsheet td {
  padding: 10px 14px; border: 1px solid var(--border);
  font-size: 11px; white-space: nowrap;
}
.spreadsheet .sticky-col {
  position: sticky; left: 0; background: white; z-index: 2;
  border-right: 2px solid var(--border);
}
.spreadsheet .filial-name { font-weight: 700; color: var(--text); font-size: 11px; }
.spreadsheet .val { text-align: right; color: var(--text-dim); font-family: 'JetBrains Mono', monospace; }
.spreadsheet .trend { text-align: center; font-weight: 800; font-size: 10px; }
.spreadsheet .total-val { background: #f1f5f9; font-weight: 800; text-align: right; }
.spreadsheet .total-head { background: #e2e8f0; color: #475569; }

.opportunity-block {
  background: #f1f5f9; border: none;
}
.opportunity-block .opp-value { font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 8px; }
.opportunity-block .opp-desc { font-size: 12px; color: var(--text-dim); line-height: 1.5; margin-bottom: 20px; }
.opp-bar { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.opp-fill { height: 100%; background: #10b981; }
.opp-footer { font-size: 10px; margin-top: 10px; color: var(--text-dim); font-weight: 700; }

/* Utils */
.mono { font-family: 'JetBrains Mono', monospace; }
.trend.good { color: #10b981; }

.footer {
  padding: 32px; border-top: 1px solid var(--border);
  display: flex; justify-content: space-between; font-size: 11px; color: var(--text-dim);
}

.animate-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 1024px) {
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
  .middle-layout { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .kpi-pro-grid { grid-template-columns: 1fr; }
}
</style>
