<template>
  <div class="torre-container industrial-theme">
    <!-- ZONE 1: Barra de Situação (Traffic Lights) -->
    <div class="zona-1 situation-bar">
      <div class="status-card" :class="getBudgetStatus">
        <div class="card-indicator"></div>
        <div class="card-content">
          <div class="card-label">Orçamento do Mês</div>
          <div class="card-value">{{ estado.projecao?.percentual_orcamento ? estado.projecao.percentual_orcamento + '%' : '...' }}</div>
          <div class="card-verdict">{{ getBudgetVerdict }}</div>
        </div>
      </div>
      
      <div class="status-card" :class="getFleetStatus">
        <div class="card-indicator"></div>
        <div class="card-content">
          <div class="card-label">Veículos com Problema</div>
          <div class="card-value">{{ getProblemVehiclesCount }}</div>
          <div class="card-verdict">{{ getFleetVerdict }}</div>
        </div>
      </div>

      <div class="status-card" :class="getPriceStatus">
        <div class="card-indicator"></div>
        <div class="card-content">
          <div class="card-label">Preço Médio vs ANP</div>
          <div class="card-value">{{ (estado.benchmark?.variacao_media_pct || 0) > 0 ? '+' : '' }}{{ estado.benchmark?.variacao_media_pct || 0 }}%</div>
          <div class="card-verdict">{{ getPriceVerdict }}</div>
        </div>
      </div>

      <div class="status-card ok">
        <div class="card-indicator"></div>
        <div class="card-content">
          <div class="card-label">Saving Acumulado</div>
          <div class="card-value">{{ fmtR(estado.benchmark?.saving_total_mes || estado.projecao?.saving_real) }}</div>
          <div class="card-verdict">Economia Real</div>
        </div>
      </div>
    </div>

    <div class="main-grid">
      <!-- LEFT COLUMN -->
      <div class="col-left">
        <!-- ZONE 2: Ações Agora -->
        <div class="zona-2 actions-now">
          <div class="section-header">
            <h2 class="font-syne">Ações Priorizadas ({{ alertas.length }})</h2>
            <div class="header-line"></div>
          </div>
          <div class="actions-list">
            <div v-for="acao in alertas" :key="acao.id" class="action-item" :class="acao.nivel">
              <div class="action-num mono">{{ acao.prioridade }}</div>
              <div class="action-main">
                <div class="action-row">
                  <h3 class="action-title">{{ acao.titulo }}</h3>
                  <span class="action-impact mono">{{ acao.impacto }}</span>
                </div>
                <p class="action-desc">{{ acao.descricao }}</p>
              </div>
              <button class="btn-detail font-syne" @click="modalAtivo = acao">Ver Detalhe</button>
            </div>
            <div v-if="alertas.length === 0" class="empty-actions">
              <div class="icon">✓</div>
              <p>Nenhuma ação crítica pendente. Operação em conformidade.</p>
            </div>
          </div>
        </div>

        <!-- ZONE 3: Painéis de Decisão -->
        <div class="zona-3 decision-panels">
          <!-- Onde Abastecer -->
          <div class="panel-card supply-panel">
            <h3 class="font-syne">Onde Abastecer Agora</h3>
            <div class="panel-subtitle">Benchmark ANP por Município</div>
            <div class="ranking-list">
              <div v-for="(p, i) in getTopPostos" :key="p.razao_social_posto" class="rank-item" :class="{ first: i === 0 }">
                <div class="rank-label mono">#{{ i+1 }}</div>
                <div class="rank-info">
                  <div class="rank-name">{{ p.razao_social_posto }}</div>
                  <div class="rank-city">{{ p.cidade_posto }} <span class="anp">{{ p.variacao_pct }}% vs ANP</span></div>
                </div>
                <div class="rank-price mono">{{ fmtPrice(p.preco_medio) }}</div>
              </div>
              <div v-if="getPostoEvitar" class="rank-item avoid">
                <div class="rank-label mono">!</div>
                <div class="rank-info">
                  <div class="rank-name">{{ getPostoEvitar.razao_social_posto }}</div>
                  <div class="rank-city">EVITAR · {{ getPostoEvitar.cidade_posto }}</div>
                </div>
                <div class="rank-price mono">{{ fmtPrice(getPostoEvitar.preco_medio) }}</div>
              </div>
            </div>
          </div>

          <!-- Status Frota -->
          <div class="panel-card fleet-panel">
            <h3 class="font-syne">Status de Eficiência</h3>
            <div class="fleet-list">
              <div v-for="v in getFleetStatusList" :key="v.placa" class="fleet-item" :class="v.status">
                <div class="fleet-meta">
                  <span class="placa mono">{{ v.placa }}</span>
                  <span class="status-dot"></span>
                </div>
                <div class="efficiency-track">
                  <div class="efficiency-bar" :style="{ width: Math.min((v.km_litro / 4) * 100, 100) + '%' }"></div>
                </div>
                <div class="fleet-data mono">{{ v.km_litro || v.consumo_atual || 0 }} km/L</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ZONE 4: Coluna Direita (Executiva) -->
      <div class="col-right">
        <!-- Projeção -->
        <div class="zona-4-block projection-panel">
          <h3 class="font-syne">Projeção de Fechamento</h3>
          <div class="proj-sum mono">
            <div class="proj-label">Projetado (R$)</div>
            <div class="proj-val">{{ fmtR(estado.projecao?.projecao_fechamento) }}</div>
          </div>
          <div class="proj-track">
            <div class="proj-fill" :style="{ width: Math.min(estado.projecao?.percentual_orcamento, 110) + '%' }" :class="getBudgetStatus"></div>
          </div>
          <div class="proj-grid mono">
            <div class="pg-item"><span class="l">META/DIA</span><span class="v" :class="getBudgetStatus">{{ fmtR(estado.projecao?.meta_diaria_necessaria) }}</span></div>
            <div class="pg-item"><span class="l">DIAS REST.</span><span class="v">{{ estado.projecao?.dias_restantes }}</span></div>
            <div class="pg-item"><span class="l">DESVIO</span><span class="v" :class="getBudgetStatus">{{ fmtR(estado.projecao?.desvio_reais) }}</span></div>
          </div>
          <div class="proj-verdict" :class="getBudgetStatus">
            {{ getProjectionVerdictMsg }}
          </div>
        </div>

        <!-- Inteligência de Mercado -->
        <div class="zona-4-block market-panel">
          <div class="block-header">
            <h3 class="font-syne">Inteligência de Mercado</h3>
            <button class="btn-refresh-intel" @click="atualizarIntel" :disabled="intelLoading">
              <span class="icon" :class="{ spinning: intelLoading }">↻</span>
            </button>
          </div>
          
          <div v-if="!intel" class="intel-placeholder">
            <p>Clique em atualizar para processar dados de mercado via IA.</p>
          </div>
          <div v-else class="intel-content">
            <div class="intel-tickers">
              <div class="ticker">
                <span class="tl">BRENT</span>
                <span class="tv mono">${{ intel.brent.valor }} <span class="pct">+{{ intel.brent.variacao }}%</span></span>
              </div>
              <div class="ticker">
                <span class="tl">USD/BRL</span>
                <span class="tv mono">R${{ intel.cambio.valor }}</span>
              </div>
            </div>
            
            <div class="news-list">
              <div v-for="n in intel.noticias" :key="n.id" class="news-item">
                <div class="news-meta">
                  <span class="news-impact" :class="n.impacto.toLowerCase()">{{ n.impacto }} Impacto</span>
                  <span class="news-source">{{ n.fonte }}</span>
                </div>
                <div class="news-title">{{ n.titulo }}</div>
                <div class="news-action">Ação via IA: <span class="at">{{ n.acao }}</span></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Saúde da Operação -->
        <div class="zona-4-block health-score-block">
          <h3 class="font-syne">Score de Saúde</h3>
          <div class="score-display">
            <div class="score-val mono" :style="{ color: getHealthColor }">{{ healthScore }}%</div>
            <div class="score-grid">
              <div class="dim">
                <div class="dl">PREÇOS</div>
                <div class="db"><div class="df" :style="{ width: '85%' }"></div></div>
              </div>
              <div class="dim">
                <div class="dl">FROTA</div>
                <div class="db"><div class="df" :style="{ width: '70%', background: 'var(--yellow)' }"></div></div>
              </div>
              <div class="dim">
                <div class="dl">ORÇAMENTO</div>
                <div class="db"><div class="df" :style="{ width: '60%', background: 'var(--red)' }"></div></div>
              </div>
              <div class="dim">
                <div class="dl">ROTA</div>
                <div class="db"><div class="df" :style="{ width: '95%' }"></div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL DE AÇÃO -->
    <AcaoDetalhe v-model="modalAtivo" @resolve="atualizarTudo" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useGritschData } from '../composables/useGritschData'
import { useAlertas } from '../composables/useAlertas'
import { useIntelMercado } from '../composables/useIntelMercado'
import AcaoDetalhe from '../components/AcaoDetalhe.vue'

const { estado, carregando, atualizarTudo } = useGritschData()
const { alertas } = useAlertas(estado)
const { intel, carregando: intelLoading, atualizarIntel } = useIntelMercado()

const modalAtivo = ref(null)

onMounted(() => {
  console.log('[TorreDecisao] Component Mounted. Initializing Fetch...')
  atualizarTudo()
  // Refresh a cada 1 minuto em teste
  setInterval(atualizarTudo, 60000)
})

const fmtR = v => v ? 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : 'R$ 0'
const fmtPrice = v => v ? 'R$ ' + Number(v).toFixed(3) : 'R$ 0,000'

const getProblemVehiclesCount = computed(() => {
  // Assume que dados de frota no estado podem vir do fetch em formato de lista
  const list = estado.value.frota || []
  return list.filter(v => (v.variacao_consumo_pct || 0) > 25).length || 0
})

const getBudgetStatus = computed(() => {
  const p = estado.value.projecao?.percentual_orcamento || 0
  if (p > 105) return 'critico'
  if (p > 95) return 'atencao'
  return 'ok'
})

const getBudgetVerdict = computed(() => {
  const s = getBudgetStatus.value
  if (s === 'critico') return 'Agir Agora'
  if (s === 'atencao') return 'Verificar'
  return 'OK'
})

const getFleetStatus = computed(() => {
  const count = getProblemVehiclesCount.value
  if (count > 2) return 'critico'
  if (count > 0) return 'atencao'
  return 'ok'
})

const getFleetVerdict = computed(() => {
  const s = getFleetStatus.value
  if (s === 'critico') return 'Ação Imediata'
  if (s === 'atencao') return 'Verificar'
  return 'Operação Normal'
})

const getPriceStatus = computed(() => {
  const p = estado.value.benchmark?.variacao_media_pct || 0
  if (p > 5) return 'critico'
  if (p > 2) return 'atencao'
  return 'ok'
})

const getPriceVerdict = computed(() => {
  const s = getPriceStatus.value
  if (s === 'critico') return 'Inadmissível'
  if (s === 'atencao') return 'Sinal Amarelo'
  return 'Economizando'
})

const getProjectionVerdictMsg = computed(() => {
  const proj = estado.value.projecao
  if (!proj) return 'Carregando análise...'
  if (proj.desvio_reais > 0) {
    return `Ação necessária: reduzir R$ ${Number(proj.meta_diaria_necessaria).toLocaleString()} /dia nos próximos ${proj.dias_restantes} dias`
  }
  return 'Projeção dentro do teto orçamentário'
})

const getTopPostos = computed(() => {
  const list = estado.value.precos || []
  return list.slice(0, 3)
})

const getPostoEvitar = computed(() => {
  const list = estado.value.precos
  if (!list || list.length < 5) return null
  return [...list].sort((a,b) => b.variacao_pct - a.variacao_pct)[0]
})

const getFleetStatusList = computed(() => {
  const list = estado.value.frota || []
  return list.map(v => ({
    ...v,
    status: (v.variacao_consumo_pct || 0) > 25 ? 'critico' : (v.variacao_consumo_pct || 0) > 10 ? 'atencao' : 'ok'
  })).sort((a,b) => {
    const map = { critico: 0, atencao: 1, ok: 2 }
    return map[a.status] - map[b.status]
  }).slice(0, 5)
})

const healthScore = computed(() => {
  let score = 100
  if (getBudgetStatus.value === 'critico') score -= 25
  if (getPriceStatus.value === 'critico') score -= 15
  if (getFleetStatus.value === 'critico') score -= 15
  return Math.max(score, 0)
})

const getHealthColor = computed(() => {
  const s = healthScore.value
  if (s > 80) return 'var(--green)'
  if (s > 50) return 'var(--yellow)'
  return 'var(--red)'
})
</script>

<style scoped>
.torre-container {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ZONE 1 */
.zona-1 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 40px;
}
.status-card {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 20px;
  display: flex;
  gap: 20px;
  position: relative;
  overflow: hidden;
}
.card-indicator { width: 4px; height: 100%; position: absolute; left: 0; top: 0; background: var(--text-3); }
.status-card.critico .card-indicator { background: var(--red); }
.status-card.atencao .card-indicator { background: var(--yellow); }
.status-card.ok .card-indicator { background: var(--green); }

.card-label { font-size: 11px; color: var(--text-3); text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
.card-value { font-family: 'IBM Plex Mono', monospace; font-size: 26px; font-weight: 700; color: var(--text); }
.card-verdict { font-size: 11px; font-weight: 600; text-transform: uppercase; margin-top: 4px; }
.critico .card-verdict { color: var(--red); }
.atencao .card-verdict { color: var(--yellow); }
.ok .card-verdict { color: var(--green); }

/* GRID */
.main-grid { display: grid; grid-template-columns: 1fr 340px; gap: 40px; }

/* ZONE 2 */
.zona-2 { margin-bottom: 40px; }
.header-line { height: 1px; background: var(--border); margin-top: 8px; position: relative; }
.header-line::after { content: ""; position: absolute; left: 0; top: -1px; width: 40px; height: 3px; background: var(--orange); }

.actions-list { display: grid; gap: 16px; margin-top: 24px; }
.action-item {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  border-left: 6px solid transparent;
}
.action-item.critico { border-left-color: var(--red); }
.action-item.atencao { border-left-color: var(--yellow); }

.action-num {
  font-size: 18px; font-weight: 800; color: var(--text-3); border: 2px solid var(--border);
  width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
}
.action-main { flex: 1; min-width: 0; }
.action-row { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.action-title { font-size: 14px; font-weight: 700; text-transform: uppercase; }
.action-impact { font-size: 11px; color: var(--green); background: var(--green-bg); padding: 2px 6px; border-radius: 2px; white-space: nowrap; }
.critico .action-impact { color: var(--red); background: var(--red-bg); }
.action-desc { color: var(--text-2); font-size: 12px; margin: 4px 0 0; }

.btn-detail {
  background: transparent; border: 1px solid var(--border); color: var(--text-2);
  padding: 8px 16px; border-radius: 2px; cursor: pointer; font-size: 10px;
}

/* ZONE 3 */
.zona-3 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.panel-card { background: var(--surface); border: 1px solid var(--border); padding: 24px; }
.panel-card h3 { font-size: 13px; margin-bottom: 4px; }
.panel-subtitle { font-size: 10px; color: var(--text-3); margin-bottom: 20px; }

.ranking-list { display: grid; gap: 12px; }
.rank-item { display: flex; align-items: center; gap: 12px; padding: 10px; background: var(--void); border: 1px solid var(--border-subtle); }
.rank-item.first { border-color: var(--green); }
.rank-item.avoid { border-color: var(--red); }
.rank-label { font-size: 12px; color: var(--text-3); width: 20px; }
.rank-info { flex: 1; min-width: 0; }
.rank-name { font-size: 12px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-city { font-size: 10px; color: var(--text-3); }
.rank-price { font-size: 13px; font-weight: 600; }

.fleet-list { display: grid; gap: 10px; }
.fleet-item { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--border-subtle); }
.placa { font-size: 11px; color: var(--text-2); width: 60px; }
.efficiency-track { flex: 1; height: 3px; background: var(--void); }
.efficiency-bar { height: 100%; background: var(--green); }
.fleet-item.critico .efficiency-bar { background: var(--red); }
.status-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--green); }
.critico .status-dot { background: var(--red); }
.fleet-data { font-size: 11px; color: var(--text-3); width: 60px; text-align: right; }

/* ZONE 4 */
.zona-4-block { background: var(--surface); border: 1px solid var(--border); padding: 20px; margin-bottom: 24px; }
.zona-4-block h3 { font-size: 12px; color: var(--orange); margin-bottom: 16px; }

.proj-val { font-size: 24px; font-weight: 700; margin-bottom: 16px; }
.proj-track { height: 6px; background: var(--void); margin-bottom: 20px; }
.proj-fill { height: 100%; background: var(--green); }
.proj-fill.critico { background: var(--red); }
.proj-grid { display: grid; gap: 10px; font-size: 10px; margin-bottom: 20px; }
.pg-item { display: flex; justify-content: space-between; }
.pg-item .l { color: var(--text-3); }
.proj-verdict { padding: 12px; font-size: 11px; font-weight: 600; border-left: 3px solid; }
.proj-verdict.critico { background: var(--red-bg); border-color: var(--red); color: var(--red); }
.proj-verdict.ok { background: var(--green-bg); border-color: var(--green); color: var(--green); }

.market-panel .block-header { display: flex; justify-content: space-between; }
.btn-refresh-intel { background: var(--void); border: 1px solid var(--border); color: var(--text-3); cursor: pointer; }
.intel-tickers { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
.news-list { margin-top: 20px; display: grid; gap: 16px; }
.news-item { border-left: 1px solid var(--border); padding-left: 12px; }
.news-title { font-size: 11px; font-weight: 700; line-height: 1.3; }
.news-action { font-size: 10px; color: var(--text-3); margin-top: 4px; }

.score-display { display: flex; flex-direction: column; gap: 16px; }
.score-val { font-size: 40px; font-weight: 800; text-align: center; }
.score-grid { display: grid; gap: 8px; }
.dim { display: flex; align-items: center; gap: 10px; }
.dl { font-size: 9px; color: var(--text-3); width: 60px; }
.db { flex: 1; height: 3px; background: var(--void); }
.df { height: 100%; background: var(--green); }

.spinning { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { from {transform:rotate(0)} to {transform:rotate(360deg)} }
</style>
