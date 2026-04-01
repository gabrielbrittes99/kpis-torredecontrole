<template>
  <div class="page executive-theme animate-in">

    <!-- Topbar: Padronizada -->
    <GlobalTopbar
      title="Diretoria"
      subtitle="Visão estratégica de custos e performance"
      :show-period="true"
      :show-filters="true"
    />

    <div class="page-body">
      
      <!-- HERO SECTION: Os Números que Importam -->
      <div class="kpi-pro-grid">
        <KpiCardPro
          title="Gasto Real (Mês)"
          :value="kpis.gasto_mes_atual_real || 0"
          :trendValue="comparativo.variacao?.valor_pct"
          trendInvert
          format="currency"
          theme="primary"
          :description="'Realizado até dia ' + (kpis.dia_referencia_proj || '—')"
        />
        <KpiCardPro
          title="Projeção (Mês)"
          :value="kpis.projecao_mes_atual || 0"
          format="currency"
          :description="(kpis.veiculos_ativos_mes || 0) + ' veículos ativos'"
        />
        <KpiCardPro
          title="Preço Médio/L"
          :value="kpis.preco_medio_litro || 0"
          :trendValue="comparativo.variacao?.preco_pct"
          trendInvert
          format="currency"
          :decimals="3"
          description="Média ponderada geral"
        />
        <KpiCardPro
          title="Custo/KM Global"
          :value="kpis.custo_por_km || 0"
          :trendValue="comparativo.variacao?.custo_km_pct"
          trendInvert
          format="currency"
          :decimals="3"
          description="Gasto Year-to-Date"
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
import KpiCardPro from '../components/KpiCardPro.vue'
import {
  fetchKpisEstrategicos,
  fetchTendencia12Meses,
  fetchMixCombustiveis,
  fetchComparativoMeses,
  fetchBenchmarkComparativo,
  fetchGastosFiliais
} from '../api/diretoria.js'
import GraficoTendencia       from '../components/GraficoTendencia.vue'
import GraficoMixCombustiveis from '../components/GraficoMixCombustiveis.vue'
import BenchmarkANP           from '../components/BenchmarkANP.vue'

const store = useFiltrosStore()

const kpis           = ref({})
const tendencia      = ref([])
const comparativo    = ref({})
const mix            = ref({ mes: [], ano: [] })
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

  await Promise.allSettled([
    fetchKpisEstrategicos(p).then(d => kpis.value = d).catch(e => console.warn('[Diretoria] KPIs:', e)),
    fetchTendencia12Meses(p).then(d => tendencia.value = d).catch(e => console.warn('[Diretoria] Tendência:', e)).finally(() => lTendencia.value = false),
    fetchComparativoMeses(p).then(d => comparativo.value = d).catch(e => console.warn('[Diretoria] Comparativo:', e)).finally(() => lComparativo.value = false),
    fetchMixCombustiveis(p).then(d => mix.value = d).catch(e => console.warn('[Diretoria] Mix:', e)).finally(() => lMix.value = false),
    fetchBenchmarkComparativo(p).then(d => benchmark.value = d).catch(e => console.warn('[Diretoria] Benchmark:', e)).finally(() => lBenchmark.value = false),
    fetchGastosFiliais(p).then(d => filiais.value = d).catch(e => console.warn('[Diretoria] Filiais:', e)).finally(() => lFiliais.value = false),
  ])
}

watch(() => store.selecao, () => refreshData(), { deep: true })

onMounted(() => {
  refreshData()
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
  --accent: #C41230;
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


/* Middle Layout */
.middle-layout {
  display: grid; grid-template-columns: 1fr 340px; gap: 40px;
}

.v-block {
  background:
    linear-gradient(white, white) padding-box,
    linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box;
  border: 1px solid transparent;
  border-radius: 20px;
  padding: 32px; margin-bottom: 24px;
}
.section-title {
  font-size: 11px; font-weight: 700; color: var(--text-dim); letter-spacing: 0.08em;
  margin-bottom: 24px; text-transform: uppercase; border-left: 3px solid #C41230;
  padding-left: 12px;
}

.label-tiny { font-size: 9px; font-weight: 800; color: var(--text-dim); margin-bottom: 12px; }


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

.metric-comparisons { border-top: 1px solid rgba(0,0,0,0.04); padding-top: 16px; display: flex; flex-direction: column; gap: 8px; }
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
