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
          :description="kpis.dias_restantes_uteis
            ? `${kpis.dias_restantes_uteis} dias úteis restantes · ritmo ${fmtR(kpis.media_dia_util)}/dia`
            : (kpis.veiculos_ativos_mes || 0) + ' veículos ativos'"
        />
        <KpiCardPro
          title="Preço Médio/L"
          :value="kpis.preco_medio_litro || 0"
          :trendValue="comparativo.variacao?.preco_pct"
          trendInvert
          format="currency"
          :decimals="2"
          description="Média ponderada do período"
        />
        <KpiCardPro
          title="Custo/KM"
          :value="kpis.custo_por_km || 0"
          :trendValue="comparativo.variacao?.custo_km_pct"
          trendInvert
          format="currency"
          :decimals="2"
          description="Eficiência do período"
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
              <span class="unit">LITROS ABASTECIDOS</span>
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
            <div class="metric-value">
              <template v-if="comparativo.mes_atual?.custo_km">
                R$ {{ comparativo.mes_atual.custo_km.toFixed(2) }} <span class="sub-unit">/KM</span>
              </template>
              <template v-else><span style="font-size:1rem;color:var(--text-3)">Dados insuficientes</span></template>
            </div>
            <div class="metric-comparisons">
              <div class="comp-row">
                <span class="comp-label">vs Mês Anterior</span>
                <span class="comp-val" :class="comparativo.variacao?.custo_km_abs ? getTrendClass(comparativo.variacao.custo_km_abs, 0.01) : ''">
                  <template v-if="comparativo.variacao?.custo_km_abs">
                    {{ comparativo.variacao.custo_km_abs > 0 ? '▲' : '▼' }} R$ {{ Math.abs(comparativo.variacao.custo_km_abs).toFixed(2) }}
                  </template>
                  <template v-else>—</template>
                </span>
              </div>
              <div class="comp-row">
                <span class="comp-label">vs Média 3 Meses</span>
                <span class="comp-val" :class="comparativo.variacao_vs_media?.custo_km_abs ? getTrendClass(comparativo.variacao_vs_media.custo_km_abs, 0.01) : ''">
                  <template v-if="comparativo.variacao_vs_media?.custo_km_abs">
                    {{ comparativo.variacao_vs_media.custo_km_abs > 0 ? '▲' : '▼' }} R$ {{ Math.abs(comparativo.variacao_vs_media.custo_km_abs).toFixed(2) }}
                  </template>
                  <template v-else>—</template>
                </span>
              </div>
            </div>
          </div>

        </div>
      </section>

      <!-- ANÁLISE A PARTIR DE MÊS DE REFERÊNCIA -->
      <section class="v-block ref-block">
        <div class="ref-header">
          <div>
            <div class="section-title" style="margin-bottom:8px">ANÁLISE A PARTIR DE UM MÊS DE REFERÊNCIA</div>
            <div class="ref-sub">
              Escolha um mês-âncora (ex: Fev/2026 — boom da guerra) e veja a evolução ponderada até o mês selecionado no filtro principal.
            </div>
          </div>
          <div class="ref-controls">
            <div class="ref-picker">
              <label>MÊS DE REFERÊNCIA</label>
              <div class="ref-picker-row">
                <select v-model.number="refMes">
                  <option v-for="(m, i) in store.opcoes.meses" :key="i" :value="i + 1">{{ m }}</option>
                </select>
                <select v-model.number="refAno">
                  <option v-for="y in store.opcoes.anos" :key="y" :value="y">{{ y }}</option>
                </select>
              </div>
            </div>
            <div class="ref-picker">
              <label>ATÉ O MÊS DO FILTRO</label>
              <div class="ref-ate">{{ (store.selecao.mes).toString().padStart(2,'0') }}/{{ store.selecao.ano }}</div>
            </div>
          </div>
        </div>

        <div v-if="lAnalise" class="ref-loading">Carregando análise...</div>

        <template v-else-if="analiseRef.referencia">
          <!-- KPIs ponderados -->
          <div class="ref-kpis">
            <div class="ref-kpi-card base">
              <div class="ref-kpi-label">BASE · {{ analiseRef.referencia.rotulo }}</div>
              <div class="ref-kpi-val">{{ fmtRPreco(analiseRef.referencia.preco_ponderado ?? analiseRef.referencia.preco_medio) }}<span class="unit">/L</span></div>
              <div class="ref-kpi-foot">
                Gasto: {{ fmtR(analiseRef.referencia.total_valor) }} · {{ fmtN(analiseRef.referencia.total_litros) }} L
              </div>
            </div>

            <div class="ref-kpi-card">
              <div class="ref-kpi-label">PREÇO POND. (MIX REF.) · MÊS ATUAL</div>
              <div class="ref-kpi-val">
                {{ analiseRef.ponderado ? fmtRPreco(analiseRef.ponderado.preco_medio_ponderado) : '—' }}<span class="unit">/L</span>
              </div>
              <div class="ref-kpi-foot" :class="getTrendClass(analiseRef.ponderado?.preco_vs_ref_pct)">
                <template v-if="analiseRef.ponderado?.preco_vs_ref_pct != null">
                  {{ analiseRef.ponderado.preco_vs_ref_pct > 0 ? '▲' : '▼' }}
                  {{ Math.abs(analiseRef.ponderado.preco_vs_ref_pct) }}% vs referência
                </template>
                <template v-else>Sem base suficiente</template>
              </div>
            </div>

            <div class="ref-kpi-card">
              <div class="ref-kpi-label">CUSTO/KM PONDERADO · PERÍODO</div>
              <div class="ref-kpi-val">
                {{ analiseRef.ponderado && analiseRef.ponderado.custo_km_ponderado
                    ? fmtRPreco(analiseRef.ponderado.custo_km_ponderado)
                    : '—' }}<span class="unit">/KM</span>
              </div>
              <div class="ref-kpi-foot" :class="getTrendClass(analiseRef.ponderado?.custo_km_vs_ref_pct)">
                <template v-if="analiseRef.ponderado?.custo_km_vs_ref_pct != null">
                  {{ analiseRef.ponderado.custo_km_vs_ref_pct > 0 ? '▲' : '▼' }}
                  {{ Math.abs(analiseRef.ponderado.custo_km_vs_ref_pct) }}% vs referência
                </template>
                <template v-else>Dados insuficientes</template>
              </div>
            </div>

            <div class="ref-kpi-card">
              <div class="ref-kpi-label">GASTO ACUMULADO · {{ analiseRef.ponderado?.n_meses || 0 }} MESES</div>
              <div class="ref-kpi-val">
                {{ analiseRef.ponderado ? fmtR(analiseRef.ponderado.gasto_total_janela) : '—' }}
              </div>
              <div class="ref-kpi-foot">
                Média mensal: {{ analiseRef.ponderado ? fmtR(analiseRef.ponderado.gasto_medio_mensal) : '—' }}
              </div>
            </div>
          </div>

          <!-- Banner explicativo para transparência da matemática -->
          <div class="ref-info-banner">
            <span class="ref-info-icon">i</span>
            <div>
              <strong>Como ler:</strong>
              <em>Preço Pond.</em> usa média ponderada pelo mix de combustível do mês de referência (índice de Laspeyres) — isola variação de preço da variação de mix.
              <em>Preço Real</em> = Gasto ÷ Litros do próprio mês (muda com o mix).
              <em>Custo/KM</em> = Gasto ÷ KM (hodômetro completo da frota).
              <template v-if="analiseRef.ponderado?.pesos_combustivel_ref">
                Mix referência:
                <span v-for="(pct, comb) in analiseRef.ponderado.pesos_combustivel_ref" :key="comb">
                  {{ comb }} {{ pct }}%
                </span>.
              </template>
            </div>
          </div>

          <!-- Série mensal -->
          <div class="ref-table-wrap">
            <table class="ref-table">
              <thead>
                <tr>
                  <th>Mês</th>
                  <th>Gasto</th>
                  <th>Δ%</th>
                  <th>Litros</th>
                  <th>Δ%</th>
                  <th>KM</th>
                  <th>Δ%</th>
                  <th>Preço Pond.</th>
                  <th>Δ Preço Pond.</th>
                  <th>Preço Real/L</th>
                  <th>Custo/KM</th>
                  <th>Δ%</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in analiseRef.serie" :key="m.rotulo" :class="{ 'is-ref': m.eh_referencia }">
                  <td>
                    <strong>{{ m.rotulo }}</strong>
                    <span v-if="m.eh_referencia" class="ref-tag">REF</span>
                  </td>
                  <td class="num">{{ fmtR(m.total_valor) }}</td>
                  <td class="num" :class="getTrendClass(m.valor_pct)">
                    <template v-if="m.eh_referencia">—</template>
                    <template v-else-if="m.valor_pct != null">{{ m.valor_pct > 0 ? '▲' : '▼' }} {{ Math.abs(m.valor_pct) }}%</template>
                    <template v-else>—</template>
                  </td>
                  <td class="num">{{ fmtN(m.total_litros) }}</td>
                  <td class="num" :class="getTrendClass(m.litros_pct)">
                    <template v-if="m.eh_referencia">—</template>
                    <template v-else-if="m.litros_pct != null">{{ m.litros_pct > 0 ? '▲' : '▼' }} {{ Math.abs(m.litros_pct) }}%</template>
                    <template v-else>—</template>
                  </td>
                  <td class="num">{{ m.total_km ? fmtN(m.total_km) : '—' }}</td>
                  <td class="num" :class="getTrendClass(m.km_pct)">
                    <template v-if="m.eh_referencia">—</template>
                    <template v-else-if="m.km_pct != null">{{ m.km_pct > 0 ? '▲' : '▼' }} {{ Math.abs(m.km_pct) }}%</template>
                    <template v-else>—</template>
                  </td>
                  <td class="num">{{ fmtRPreco(m.preco_ponderado) }}</td>
                  <td class="num" :class="getTrendClass(m.preco_pct)">
                    <template v-if="m.eh_referencia">—</template>
                    <template v-else-if="m.preco_pct != null">
                      {{ m.preco_pct > 0 ? '▲' : '▼' }} {{ Math.abs(m.preco_pct) }}%
                      <span class="abs-delta">({{ m.preco_abs > 0 ? '+' : '' }}{{ fmtRPreco(m.preco_abs) }})</span>
                    </template>
                    <template v-else>—</template>
                  </td>
                  <td class="num" style="color:#999;font-size:0.85em">{{ fmtRPreco(m.preco_medio) }}</td>
                  <td class="num">{{ m.custo_km ? fmtRPreco(m.custo_km) : '—' }}</td>
                  <td class="num" :class="getTrendClass(m.custo_km_pct)">
                    <template v-if="m.eh_referencia">—</template>
                    <template v-else-if="m.custo_km_pct != null">{{ m.custo_km_pct > 0 ? '▲' : '▼' }} {{ Math.abs(m.custo_km_pct) }}%</template>
                    <template v-else>—</template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <div v-else class="ref-empty">
          Sem dados para o mês de referência selecionado.
        </div>
      </section>

      <!-- MIDDLE SECTION: Análise Profunda -->
      <div class="middle-layout">
        
        <!-- Coluna Esquerda -->
        <div class="col-charts">
          <section class="v-block">
             <div class="section-title">TENDÊNCIA DE CUSTO (12 MESES)</div>
             <GraficoTendencia :data="tendencia" :loading="lTendencia" />
          </section>

          <section class="v-block">
             <div class="section-title">BENCHMARK DE MERCADO (ANP)</div>
             <BenchmarkANP :data="benchmark" :resumo="kpis.saving_resumo_anp" :loading="lBenchmark" />
          </section>

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

        <!-- Coluna Direita: Mix -->
        <aside class="col-aside">
          <div class="v-block">
             <div class="label-tiny mono">MIX DE COMBUSTÍVEL (MÊS)</div>
             <GraficoMixCombustiveis :data="mix.mes" :loading="lMix" />
          </div>

          <div class="v-block">
             <div class="label-tiny mono">MIX DE COMBUSTÍVEL (ANO)</div>
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
  fetchGastosFiliais,
  fetchAnaliseReferencia
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
const analiseRef     = ref({ referencia: null, serie: [], ponderado: null })

const lTendencia   = ref(true)
const lComparativo = ref(true)
const lMix         = ref(true)
const lBenchmark   = ref(true)
const lFiliais     = ref(true)
const lAnalise     = ref(true)

// Mês de referência da análise (default: Fev do ano corrente — boom da guerra)
const refMes = ref(2)
const refAno = ref(new Date().getFullYear())

const fmtR = v => v != null ? 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'
const fmtRPrecise = v => v != null ? 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'
const fmtRPreco = v => v != null ? 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

const getTrendClass = (val, threshold = 2) => {
  if (val == null || Math.abs(val) < threshold) return 'neutral'
  return val > 0 ? 'red' : 'green'
}

function buildApiParams(extras = {}) {
  const s = store.selecao
  return {
    mes: s.mes,
    ano: s.ano,
    combustivel: s.combustivel || undefined,
    filial: s.filial || undefined,
    estado: s.estado || undefined,
    regiao: s.regiao || undefined,
    grupo: s.grupo || undefined,
    ...extras
  }
}

async function refreshData() {
  const p = buildApiParams()
  // Tendência sempre mostra últimos 12 meses — não envia mes/ano, apenas atributos
  const { mes, ano, ...pAtributos } = p

  lTendencia.value = true
  lComparativo.value = true
  lMix.value = true
  lBenchmark.value = true
  lFiliais.value = true

  await Promise.allSettled([
    fetchKpisEstrategicos(p).then(d => kpis.value = d).catch(e => console.warn('[Diretoria] KPIs:', e)),
    fetchTendencia12Meses(pAtributos).then(d => tendencia.value = d).catch(e => console.warn('[Diretoria] Tendência:', e)).finally(() => lTendencia.value = false),
    fetchComparativoMeses(p).then(d => comparativo.value = d).catch(e => console.warn('[Diretoria] Comparativo:', e)).finally(() => lComparativo.value = false),
    fetchMixCombustiveis(p).then(d => mix.value = d).catch(e => console.warn('[Diretoria] Mix:', e)).finally(() => lMix.value = false),
    fetchBenchmarkComparativo(p).then(d => benchmark.value = d).catch(e => console.warn('[Diretoria] Benchmark:', e)).finally(() => lBenchmark.value = false),
    fetchGastosFiliais(p).then(d => filiais.value = d).catch(e => console.warn('[Diretoria] Filiais:', e)).finally(() => lFiliais.value = false),
    refreshAnalise(),
  ])
}

async function refreshAnalise() {
  lAnalise.value = true
  const s = store.selecao
  const params = {
    mes_ref: refMes.value,
    ano_ref: refAno.value,
    mes_ate: s.mes,
    ano_ate: s.ano,
    combustivel: s.combustivel || undefined,
    filial: s.filial || undefined,
    estado: s.estado || undefined,
    regiao: s.regiao || undefined,
    grupo: s.grupo || undefined,
  }
  try {
    const d = await fetchAnaliseReferencia(params)
    analiseRef.value = d || { referencia: null, serie: [], ponderado: null }
  } catch (e) {
    console.warn('[Diretoria] AnaliseRef:', e)
    analiseRef.value = { referencia: null, serie: [], ponderado: null }
  } finally {
    lAnalise.value = false
  }
}

watch(() => store.selecao, () => refreshData(), { deep: true })
watch([refMes, refAno], () => refreshAnalise())

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
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 40px;
}

.col-charts {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.col-aside {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

@media (max-width: 1200px) {
  .middle-layout {
    grid-template-columns: 1fr;
  }
  .col-aside {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .col-aside {
    grid-template-columns: 1fr;
  }
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

/* Two Column Grid for Mix positioning */
.two-col-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

@media (max-width: 1200px) {
  .two-col-grid {
    grid-template-columns: 1fr;
  }
}

/* Full Width Container for Tendência */
.v-block-full {
  width: 100%;
}


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

/* ── Análise por Mês de Referência ───────────────────────────────────── */
.ref-block { margin-bottom: 40px; }
.ref-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 32px; flex-wrap: wrap; margin-bottom: 24px;
}
.ref-sub { font-size: 12px; color: var(--text-dim); max-width: 560px; line-height: 1.5; }
.ref-controls { display: flex; gap: 16px; align-items: flex-end; }
.ref-picker { display: flex; flex-direction: column; gap: 6px; }
.ref-picker label {
  font-size: 10px; font-weight: 800; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.ref-picker-row { display: flex; gap: 6px; }
.ref-picker select {
  background: white; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 8px 12px; font-size: 12px; font-weight: 600; color: #1e293b;
  outline: none; cursor: pointer; min-width: 110px;
}
.ref-picker select:focus { border-color: #C41230; box-shadow: 0 0 0 3px rgba(196,18,48,0.1); }
.ref-ate {
  background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 8px 14px; font-size: 13px; font-weight: 700; color: #475569;
  font-family: 'JetBrains Mono', monospace;
}

.ref-kpis {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  margin-bottom: 20px;
}
.ref-kpi-card {
  background: white; border: 1px solid var(--border); border-radius: 14px;
  padding: 16px 18px; display: flex; flex-direction: column; gap: 6px;
}
.ref-kpi-card.base { border-color: #C41230; background: #fef2f4; }
.ref-kpi-label {
  font-size: 10px; font-weight: 800; color: var(--text-dim);
  letter-spacing: 0.08em; text-transform: uppercase;
}
.ref-kpi-val {
  font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.02em;
}
.ref-kpi-val .unit { font-size: 12px; color: var(--text-dim); font-weight: 600; margin-left: 4px; }
.ref-kpi-foot { font-size: 11px; color: var(--text-dim); font-weight: 600; }
.ref-kpi-foot.red { color: #ef4444; }
.ref-kpi-foot.green { color: #10b981; }

.ref-table-wrap {
  border: 1px solid var(--border); border-radius: 10px; overflow: hidden;
}
.ref-table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; }
.ref-table th {
  background: #f8fafc; color: var(--text-dim); font-size: 10px;
  text-transform: uppercase; font-weight: 700; padding: 10px 14px;
  text-align: left; letter-spacing: 0.05em;
}
.ref-table th:not(:first-child) { text-align: right; }
.ref-table td {
  padding: 10px 14px; font-size: 12px; color: #1e293b;
  border-top: 1px solid #f1f5f9;
}
.ref-table td.num { text-align: right; font-family: 'JetBrains Mono', monospace; }
.ref-table td.num.red { color: #ef4444; font-weight: 700; }
.ref-table td.num.green { color: #10b981; font-weight: 700; }
.ref-table td.num .abs-delta {
  font-size: 10px; color: var(--text-dim); font-weight: 500; margin-left: 4px;
}
.ref-table tr.is-ref { background: #fef2f4; }
.ref-table tr.is-ref td { font-weight: 700; color: #C41230; }
.ref-table tr.is-ref td .abs-delta { color: #C41230; }
.ref-tag {
  background: #C41230; color: white; font-size: 9px; font-weight: 800;
  padding: 2px 6px; border-radius: 4px; margin-left: 8px; letter-spacing: 0.05em;
}

.ref-loading, .ref-empty {
  padding: 24px; text-align: center; color: var(--text-dim); font-size: 13px;
}

.ref-info-banner {
  display: flex; gap: 12px; align-items: flex-start;
  background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px;
  padding: 12px 16px; margin-bottom: 16px; font-size: 12px; color: #0c4a6e;
  line-height: 1.6;
}
.ref-info-banner em { font-style: normal; font-weight: 700; color: #0369a1; }
.ref-info-banner strong { color: #075985; }
.ref-info-icon {
  background: #0284c7; color: white; width: 20px; height: 20px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800; font-family: 'Times New Roman', serif;
  flex-shrink: 0; font-style: italic;
}

@media (max-width: 1100px) {
  .ref-kpis { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .ref-kpis { grid-template-columns: 1fr; }
  .ref-header { flex-direction: column; }
  .ref-controls { width: 100%; }
}
</style>
